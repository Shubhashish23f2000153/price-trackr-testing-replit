# worker/playwright_scraper/aggregation.py
from sqlalchemy import func, cast, Date, Integer
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime, timedelta, timezone

# --- FIX: Import models from the new models.py file ---
from .models import (
    PriceLog, 
    ProductSource, 
    PriceHistoryDaily, 
    PriceHistoryMonthly, 
    SessionLocal
)
# --- END FIX ---


def get_last_price_subquery(db: Session, date_trunc_unit: str, alias: str):
    """
    Helper to create a subquery that finds the latest price_cents for each (source_id, time_bucket).
    This is complex SQL, translated to SQLAlchemy.
    """
    # 1. Truncate the scrape time and get the row number, partitioned by source and bucket, ordered by time descending.
    subq = db.query(
        PriceLog.product_source_id,
        PriceLog.price_cents,
        func.date_trunc(date_trunc_unit, PriceLog.scraped_at).label("bucket"),
        func.row_number().over(
            partition_by=(
                PriceLog.product_source_id,
                func.date_trunc(date_trunc_unit, PriceLog.scraped_at)
            ),
            order_by=PriceLog.scraped_at.desc()
        ).label("rn")
    ).filter(
        PriceLog.scraped_at <= datetime.now(timezone.utc) # Ensure we don't grab future timestamps
    ).subquery('latest_prices_subq') # Added filter

    # 2. Select only the rows where row_number = 1 (the latest price in that bucket)
    last_price_q = db.query(
        subq.c.product_source_id,
        subq.c.bucket,
        subq.c.price_cents.label(alias)
    ).filter(subq.c.rn == 1).subquery('last_price_final_subq')
    
    return last_price_q

def run_daily_aggregation():
    """
    Aggregates raw price logs older than 30 days into daily summaries.
    """
    print("[Aggregator] Running DAILY aggregation...")
    db = SessionLocal()
    try:
        # Aggregate data from 30 days ago and older
        thirty_days_ago = datetime.now(timezone.utc).date() - timedelta(days=30)
        
        print(f"[Aggregator] Aggregating raw data older than or equal to: {thirty_days_ago}")

        # 1. Subquery for daily aggregates (MIN, MAX, AVG, COUNT)
        agg_subquery = db.query(
            PriceLog.product_source_id,
            cast(PriceLog.scraped_at, Date).label("day"),
            func.min(PriceLog.price_cents).label("min_cents"),
            func.max(PriceLog.price_cents).label("max_cents"),
            cast(func.avg(PriceLog.price_cents), Integer).label("avg_cents"),
            func.max(PriceLog.currency).label("currency"),
            func.count(PriceLog.id).label("samples")
        ).filter(
            cast(PriceLog.scraped_at, Date) <= thirty_days_ago
        ).group_by(
            PriceLog.product_source_id,
            cast(PriceLog.scraped_at, Date)
        ).subquery('daily_aggregates')

        # 2. Subquery to get the LAST price for each day (most recent price log in that day)
        last_price_subquery = get_last_price_subquery(db, 'day', 'last_cents')

        # 3. Join aggregates with the last price
        final_query = db.query(
            agg_subquery.c.product_source_id,
            agg_subquery.c.day,
            agg_subquery.c.min_cents,
            agg_subquery.c.max_cents,
            agg_subquery.c.avg_cents,
            last_price_subquery.c.last_cents,
            agg_subquery.c.currency,
            agg_subquery.c.samples
        ).join(
            last_price_subquery,
            (agg_subquery.c.product_source_id == last_price_subquery.c.product_source_id) &
            (agg_subquery.c.day == last_price_subquery.c.bucket)
        )

        # 4. Use INSERT... ON CONFLICT (Upsert) to insert this data into price_history_daily
        insert_stmt = insert(PriceHistoryDaily).from_select(
            ['product_source_id', 'day', 'min_cents', 'max_cents', 'avg_cents', 'last_cents', 'currency', 'samples'],
            final_query
        )
        
        # This is the "ON CONFLICT DO UPDATE" part
        upsert_stmt = insert_stmt.on_conflict_do_update(
            constraint='_daily_product_source_day_uc', # The unique constraint we created
            set_={
                'min_cents': insert_stmt.excluded.min_cents,
                'max_cents': insert_stmt.excluded.max_cents,
                'avg_cents': insert_stmt.excluded.avg_cents,
                'last_cents': insert_stmt.excluded.last_cents,
                'currency': insert_stmt.excluded.currency,
                'samples': insert_stmt.excluded.samples
            }
        )
        
        result = db.execute(upsert_stmt)
        db.commit()
        print(f"[Aggregator] Daily aggregation complete. {result.rowcount} rows affected.")

        # 5. Delete the raw logs that were just aggregated
        print(f"[Aggregator] Deleting aggregated raw logs older than or equal to {thirty_days_ago}...")
        total_deleted = 0
        while True:
            # Find rows to delete
            rows_to_delete = db.query(PriceLog.id).filter(
                cast(PriceLog.scraped_at, Date) <= thirty_days_ago
            ).limit(1000).all() # Batch size
            
            if not rows_to_delete:
                break # No more rows to delete

            ids_to_delete = [r[0] for r in rows_to_delete]
            
            # Execute delete by IDs
            delete_stmt = PriceLog.__table__.delete().where(PriceLog.id.in_(ids_to_delete))
            deleted_rows_count = db.execute(delete_stmt).rowcount
            db.commit()

            total_deleted += deleted_rows_count
            print(f"[Aggregator] Deleted {deleted_rows_count} raw rows... Total: {total_deleted}")

        print(f"[Aggregator] Raw log cleanup complete. Total deleted: {total_deleted}")

    except Exception as e:
        db.rollback()
        import traceback
        print(f"❌ CRITICAL ERROR in run_daily_aggregation: {e}\n{traceback.format_exc()}")
    finally:
        db.close()

def run_monthly_aggregation():
    """
    Aggregates daily price logs older than 1 year into monthly summaries.
    """
    print("[Aggregator] Running MONTHLY aggregation...")
    db = SessionLocal()
    try:
        # Aggregate data from 1 year ago and older
        one_year_ago = datetime.now(timezone.utc).date() - timedelta(days=365)
        # Truncate to the first of the month
        one_year_ago_month = one_year_ago.replace(day=1)
        
        print(f"[Aggregator] Aggregating daily data older than: {one_year_ago_month}")

        # 1. Subquery for monthly aggregates from daily table
        agg_subquery = db.query(
            PriceHistoryDaily.product_source_id,
            func.date_trunc('month', PriceHistoryDaily.day).label("month"),
            func.min(PriceHistoryDaily.min_cents).label("min_cents"),
            func.max(PriceHistoryDaily.max_cents).label("max_cents"),
            cast(func.avg(PriceHistoryDaily.avg_cents), Integer).label("avg_cents"),
            func.max(PriceHistoryDaily.currency).label("currency"),
            func.sum(PriceHistoryDaily.samples).label("samples")
        ).filter(
            PriceHistoryDaily.day < one_year_ago_month
        ).group_by(
            PriceHistoryDaily.product_source_id,
            func.date_trunc('month', PriceHistoryDaily.day)
        ).subquery('monthly_aggregates')

        # 2. Subquery to get the LAST price for each month (from the daily table)
        subq_last_day = db.query(
            PriceHistoryDaily.product_source_id,
            PriceHistoryDaily.last_cents,
            func.date_trunc('month', PriceHistoryDaily.day).label("bucket"),
            func.row_number().over(
                partition_by=(
                    PriceHistoryDaily.product_source_id,
                    func.date_trunc('month', PriceHistoryDaily.day)
                ),
                order_by=PriceHistoryDaily.day.desc()
            ).label("rn")
        ).filter(
             PriceHistoryDaily.day < one_year_ago_month
        ).subquery('latest_daily_subq')
        
        last_price_subquery = db.query(
            subq_last_day.c.product_source_id,
            subq_last_day.c.bucket,
            subq_last_day.c.last_cents.label('last_cents')
        ).filter(subq_last_day.c.rn == 1).subquery('last_price_final_subq')

        # 3. Join aggregates with the last price
        final_query = db.query(
            agg_subquery.c.product_source_id,
            agg_subquery.c.month,
            agg_subquery.c.min_cents,
            agg_subquery.c.max_cents,
            agg_subquery.c.avg_cents,
            last_price_subquery.c.last_cents,
            agg_subquery.c.currency,
            agg_subquery.c.samples
        ).join(
            last_price_subquery,
            (agg_subquery.c.product_source_id == last_price_subquery.c.product_source_id) &
            (agg_subquery.c.month == last_price_subquery.c.bucket)
        )
        
        # 4. Use INSERT... ON CONFLICT (Upsert)
        insert_stmt = insert(PriceHistoryMonthly).from_select(
            ['product_source_id', 'month', 'min_cents', 'max_cents', 'avg_cents', 'last_cents', 'currency', 'samples'],
            final_query
        )
        
        upsert_stmt = insert_stmt.on_conflict_do_update(
            constraint='_monthly_product_source_month_uc',
            set_={
                'min_cents': insert_stmt.excluded.min_cents,
                'max_cents': insert_stmt.excluded.max_cents,
                'avg_cents': insert_stmt.excluded.avg_cents,
                'last_cents': insert_stmt.excluded.last_cents,
                'currency': insert_stmt.excluded.currency,
                'samples': insert_stmt.excluded.samples
            }
        )
        
        result = db.execute(upsert_stmt)
        db.commit()
        print(f"[Aggregator] Monthly aggregation complete. {result.rowcount} rows affected.")

        # 5. Delete the daily logs that were just aggregated
        print(f"[Aggregator] Deleting aggregated daily logs older than {one_year_ago_month}...")
        total_deleted = 0
        while True:
            # Find rows to delete
            rows_to_delete = db.query(PriceHistoryDaily.id).filter(
                PriceHistoryDaily.day < one_year_ago_month
            ).limit(1000).all()
            
            if not rows_to_delete:
                break

            ids_to_delete = [r[0] for r in rows_to_delete]

            # Execute delete by IDs
            delete_stmt = PriceHistoryDaily.__table__.delete().where(PriceHistoryDaily.id.in_(ids_to_delete))
            deleted_rows_count = db.execute(delete_stmt).rowcount
            db.commit()

            total_deleted += deleted_rows_count
            print(f"[Aggregator] Deleted {deleted_rows_count} daily rows... Total: {total_deleted}")
            
        print(f"[Aggregator] Daily log cleanup complete. Total deleted: {total_deleted}")

    except Exception as e:
        db.rollback()
        import traceback
        print(f"❌ CRITICAL ERROR in run_monthly_aggregation: {e}\n{traceback.format_exc()}")
    finally:
        db.close()


def run_aggregation_jobs():
    """Main entry point for the aggregation worker task."""
    print("--- 🚀 Starting Price Aggregation Job ---")
    run_daily_aggregation()
    run_monthly_aggregation()
    print("--- ✅ Finished Price Aggregation Job ---")