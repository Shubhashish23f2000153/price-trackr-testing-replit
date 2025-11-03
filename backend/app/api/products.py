from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from urllib.parse import urlparse
from ..database import get_db
# Corrected Imports
from ..schemas.product import ProductCreate, ProductResponse, ProductDetail, ProductWithHistorySchema, ProductReplace
from ..schemas.price import PriceHistory
from ..schemas.extension import ProductDataFromExtension
from ..crud import products as crud_products
from ..crud import prices as crud_prices # Import crud_prices
from ..models import Product, Source, ProductSource, PriceLog, ScamScore, Seller
from ..crud import watchlist as crud_watchlist
from ..schemas.watchlist import WatchlistCreate
from ..utils.scraper_queue import enqueue_scrape, enqueue_scam_check
from typing import Literal # Import Literal

RangeOption = Literal["1h", "6h", "24h", "7d", "30d", "90d", "1y", "all"]

router = APIRouter()


@router.post("/add-from-extension")
async def add_product_from_extension(product_data: ProductDataFromExtension, db: Session = Depends(get_db)):
    parsed_url = urlparse(product_data.url)
    domain = parsed_url.netloc.replace('www.', '')

    try:
        existing_scam_score = db.query(ScamScore).filter(ScamScore.domain == domain).first()
        if not existing_scam_score:
            enqueue_scam_check(domain)
    except Exception as e:
        print(f"Failed to enqueue scam check job for {domain}: {e}")

    source = db.query(Source).filter(Source.domain == domain).first()
    if not source:
        source = Source(domain=domain, site_name=domain.split('.')[0].title())
        db.add(source)
        db.commit()
        db.refresh(source)

    marketplace_name = domain.split('.')[0].title()
    seller = crud_products.get_or_create_seller(
        db,
        marketplace=marketplace_name,
        seller_name=product_data.brand or "Unknown", # Use brand as fallback
        seller_rating=None,
        review_count=None
    )

    new_product = Product(
        title=product_data.title,
        brand=product_data.brand,
        description=product_data.description,
        image_url=product_data.imageUrl
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    product_source = ProductSource(
        product_id=new_product.id,
        source_id=source.id,
        seller_id=seller.id if seller else None, # Link seller
        url=product_data.url
    )
    db.add(product_source)
    db.commit()
    db.refresh(product_source)

    price_log = PriceLog(
        product_source_id=product_source.id,
        price_cents=int(product_data.currentPrice * 100),
        currency="INR", # Default, extension should specify later
        in_stock=True
    )
    db.add(price_log)
    db.commit()
    db.refresh(new_product)

    # --- "MEESHO SOUVENIR" FIX (FOR EXTENSION) ---
    if "meesho.com" not in domain:
        try:
            enqueue_scrape(product_source.url, new_product.id, product_source.id)
            print(f"Enqueued scrape job for: {product_source.url}")
        except Exception as e:
            print(f"Failed to enqueue scrape job for {product_source.url}: {e}")
    else:
         print(f"Skipping worker scrape for meesho.com product: {product_source.url}")
    # --- END OF FIX ---

    product_dict = {column.name: getattr(new_product, column.name) for column in new_product.__table__.columns}
    return {**product_dict, "newly_created": True}


@router.post("/track", response_model=ProductResponse)
async def track_product(product: ProductCreate, db: Session = Depends(get_db)):
    existing_product_source = db.query(ProductSource).filter(ProductSource.url == product.url).first()
    if existing_product_source:
        print(f"URL already tracked: {product.url}")
        return existing_product_source.product

    db_product = crud_products.create_product(db, product)
    parsed_url = urlparse(product.url)
    domain = parsed_url.netloc.replace('www.', '')

    try:
        existing_scam_score = db.query(ScamScore).filter(ScamScore.domain == domain).first()
        if not existing_scam_score:
            enqueue_scam_check(domain)
    except Exception as e:
        print(f"Failed to enqueue scam check job for {domain}: {e}")

    source = db.query(Source).filter(Source.domain == domain).first()
    if not source:
        site_name = domain.split('.')[0].title()
        source = Source(domain=domain, site_name=site_name, trust_score=50.0)
        db.add(source)
        db.commit()
        db.refresh(source)

    marketplace_name = domain.split('.')[0].title()
    seller = crud_products.get_or_create_seller(
        db,
        marketplace=marketplace_name,
        seller_name=product.brand or "Unknown", # Use brand as fallback
        seller_rating=None,
        review_count=None
    )

    product_source = ProductSource(
        product_id=db_product.id,
        source_id=source.id,
        seller_id=seller.id if seller else None, # Link seller
        url=product.url
    )
    db.add(product_source)
    db.commit()

    # --- "MEESHO SOUVENIR" FIX (FOR APP) ---
    if "meesho.com" not in domain:
        try:
            enqueue_scrape(product.url, db_product.id, product_source.id) # Pass product_source.id
            print(f"Enqueued scrape job for: {product.url}")
        except Exception as e:
            print(f"Failed to enqueue scrape job for {product.url}: {e}")
    else:
        print(f"Skipping worker scrape for meesho.com product: {product.url}")
    # --- END OF FIX ---

    return db_product


@router.get("/export", response_model=List[ProductWithHistorySchema])
async def export_all_data(db: Session = Depends(get_db)):
    # ... (same as before)
    try:
        all_products = crud_products.get_products(db, skip=0, limit=10000)
        export_data = []

        for product in all_products:
            product_dict = {column.name: getattr(product, column.name) for column in product.__table__.columns}
            history_data = crud_prices.get_flexible_price_history(db, product.id, range_option="all")
            history_list = [
                {
                    "date": item["date"],
                    "price": item["price"],
                    "source": item["source"]
                }
                for item in history_data
            ]
            product_with_history = {**product_dict, "price_history": history_list}
            export_data.append(product_with_history)

        return export_data

    except Exception as e:
        print(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export data.")


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    # ... (same as before)
    result = crud_products.get_product_with_prices(db, product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")

    product_obj = result["product"]
    prices = result["prices"]
    lowest_price = crud_prices.get_lowest_price(db, product_id)
    is_watchlisted_flag = crud_watchlist.is_in_watchlist(db, product_id=product_id)
    product_dict = {column.name: getattr(product_obj, column.name) for column in product_obj.__table__.columns}

    return {
        **product_dict,
        "prices": prices,
        "lowest_ever_price": lowest_price,
        "is_in_watchlist": is_watchlisted_flag
    }


@router.get("/", response_model=List[ProductResponse])
async def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # ... (same as before)
    products = crud_products.get_products(db, skip=skip, limit=limit)
    return products


@router.get("/{product_id}/history", response_model=List[PriceHistory])
async def get_price_history(
    product_id: int, 
    range: RangeOption = Query("30d", description="Time range for history (e.g., 7d, 1y, all)"),
    db: Session = Depends(get_db)
):
    # ... (same as before)
    history_data = crud_prices.get_flexible_price_history(db, product_id, range_option=range)
    return [
        PriceHistory(
            date=item["date"],
            price=item["price"],
            source=item["source"]
        )
        for item in history_data
    ]


@router.delete("/all", status_code=status.HTTP_200_OK)
async def delete_all_tracked_products(db: Session = Depends(get_db)):
    # ... (same as before)
    try:
        deleted_count = crud_products.delete_all_products(db)
        return {"message": f"Successfully deleted {deleted_count} products."}
    except Exception as e:
        print(f"Error deleting all products: {e}")
        raise HTTPException(status_code=500, detail="Could not delete all products.")


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    # ... (same as before)
    success = crud_products.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}


@router.post("/replace", response_model=ProductResponse)
async def replace_product(
    payload: ProductReplace, 
    db: Session = Depends(get_db)
):
    # ... (same as before)
    print(f"Replacing product {payload.old_product_id} with new URL: {payload.new_url}")

    delete_success = crud_products.delete_product(db, payload.old_product_id)
    if not delete_success:
        print(f"Warning: Could not find old product {payload.old_product_id} to delete. Proceeding to add new one.")

    new_product_data = ProductCreate(
        url=payload.new_url,
        title="Loading replacement product..."
    )

    try:
        new_product = await track_product(new_product_data, db)
        return new_product
    except HTTPException as e:
        raise e
    except Exception as e:
        print(f"Error during replacement tracking: {e}")
        raise HTTPException(status_code=500, detail="Failed to track the new replacement product.")

@router.post("/cleanup-orphans", status_code=status.HTTP_200_OK)
async def cleanup_orphaned_product_sources(db: Session = Depends(get_db)):
    # ... (same as before)
    print("Running orphan cleanup job...")

    valid_product_ids_query = db.query(Product.id).all()
    valid_product_ids = {pid[0] for pid in valid_product_ids_query}

    if not valid_product_ids:
        print("No valid products found. Deleting all product sources.")
        deleted_count_result = db.execute(ProductSource.__table__.delete())
        deleted_count = deleted_count_result.rowcount
    else:
        orphaned_sources_query = db.query(ProductSource).filter(
            ProductSource.product_id.notin_(valid_product_ids)
        )
        orphaned_sources = orphaned_sources_query.all()
        deleted_count = len(orphaned_sources)

        if deleted_count > 0:
            print(f"Found {deleted_count} orphaned product sources. Deleting them...")
            orphaned_sources_query.delete(synchronize_session=False)
        else:
            print("No orphaned product sources found. Database is clean.")

    db.commit()

    return {
        "message": "Orphan cleanup complete.",
        "deleted_orphaned_sources": deleted_count
    }