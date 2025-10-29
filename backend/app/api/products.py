from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from urllib.parse import urlparse
from ..database import get_db
# Corrected Imports Start Here
# --- IMPORT THE NEW SCHEMA ---
from ..schemas.product import ProductCreate, ProductResponse, ProductDetail, ProductWithHistorySchema
from ..schemas.price import PriceHistory
from ..schemas.extension import ProductDataFromExtension
from ..crud import products as crud_products
from ..crud import prices as crud_prices
from ..models import Product, Source, ProductSource, PriceLog, ScamScore
from ..crud import watchlist as crud_watchlist
from ..schemas.watchlist import WatchlistCreate
# Corrected Imports End Here
from ..utils.scraper_queue import enqueue_scrape, enqueue_scam_check

router = APIRouter()


@router.post("/add-from-extension")
async def add_product_from_extension(product_data: ProductDataFromExtension, db: Session = Depends(get_db)):
    # ... (this endpoint remains the same)
    parsed_url = urlparse(product_data.url)
    domain = parsed_url.netloc.replace('www.', '')
    
    try:
        existing_scam_score = db.query(ScamScore).filter(ScamScore.domain == domain).first()
        if not existing_scam_score:
            enqueue_scam_check(domain)
            print(f"Enqueued scam check job for new domain: {domain}")
    except Exception as e:
        print(f"Failed to enqueue scam check job for {domain}: {e}")
    
    source = db.query(Source).filter(Source.domain == domain).first()
    if not source:
        source = Source(domain=domain, site_name=domain.split('.')[0].title())
        db.add(source)
        try:
            db.commit()
            db.refresh(source)
        except Exception as e:
            db.rollback()
            raise HTTPException(status_code=500, detail="Database error while creating source.")

    new_product = Product(
        title=product_data.title,
        brand=product_data.brand,
        description=product_data.description,
        image_url=product_data.imageUrl
    )
    db.add(new_product)
    try:
        db.commit()
        db.refresh(new_product)
    except Exception as e:
        db.rollback()
        print(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail="Database error while creating product.")

    product_source = ProductSource(
        product_id=new_product.id,
        source_id=source.id,
        url=product_data.url
    )
    db.add(product_source)
    try:
        db.commit()
        db.refresh(product_source)
    except Exception as e:
        db.rollback()
        db.delete(new_product)
        db.commit()
        print(f"Error creating product source, rolled back product: {e}")
        raise HTTPException(status_code=500, detail="Database error while linking product source.")

    price_log = PriceLog(
        product_source_id=product_source.id,
        price_cents=int(product_data.currentPrice * 100),
        currency="INR",
        in_stock=True
    )
    db.add(price_log)
    try:
        db.commit()
        db.refresh(new_product)
    except Exception as e:
         db.rollback()
         db.delete(product_source)
         db.delete(new_product)
         db.commit()
         print(f"Error creating price log, rolled back all: {e}")
         raise HTTPException(status_code=500, detail="Database error while saving initial price.")

    product_dict = {column.name: getattr(new_product, column.name) for column in new_product.__table__.columns}
    return {**product_dict, "newly_created": True}


@router.post("/track", response_model=ProductResponse)
async def track_product(product: ProductCreate, db: Session = Depends(get_db)):
    # ... (this endpoint remains the same)
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
            print(f"Enqueued scam check job for new domain: {domain}")
    except Exception as e:
        print(f"Failed to enqueue scam check job for {domain}: {e}")

    source = db.query(Source).filter(Source.domain == domain).first()
    if not source:
        site_name = domain.split('.')[0].title()
        source = Source(domain=domain, site_name=site_name, trust_score=50.0)
        db.add(source)
        db.commit()
        db.refresh(source)

    product_source = ProductSource(
        product_id=db_product.id,
        source_id=source.id,
        url=product.url
    )
    db.add(product_source)
    db.commit()

    try:
        enqueue_scrape(product.url, db_product.id, source.id)
        print(f"Enqueued scrape job for: {product.url}")
    except Exception as e:
        print(f"Failed to enqueue scrape job for {product.url}: {e}")

    return db_product


# --- NEW EXPORT ENDPOINT (Must be before '/{product_id}') ---
@router.get("/export", response_model=List[ProductWithHistorySchema])
async def export_all_data(db: Session = Depends(get_db)):
    """
    Export all products and their full price histories in a single JSON.
    """
    try:
        all_products = crud_products.get_products(db, skip=0, limit=10000)
        export_data = []
        
        for product in all_products:
            product_dict = {column.name: getattr(product, column.name) for column in product.__table__.columns}
            
            history_logs = crud_prices.get_price_history(db, product.id, days=9999)
            history_list = [
                {
                    "date": log.scraped_at,
                    "price": log.price_cents / 100,
                    "source": log.product_source.source.site_name if log.product_source and log.product_source.source else "Unknown"
                }
                for log in history_logs
            ]
            
            product_with_history = {**product_dict, "price_history": history_list}
            export_data.append(product_with_history)
            
        return export_data
        
    except Exception as e:
        print(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export data.")


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    # ... (this endpoint remains the same)
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
    # ... (this endpoint remains the same)
    products = crud_products.get_products(db, skip=skip, limit=limit)
    return products


@router.get("/{product_id}/history")
async def get_price_history(product_id: int, days: int = 30, db: Session = Depends(get_db)):
    # ... (this endpoint remains the same)
    history = crud_prices.get_price_history(db, product_id, days)
    return [
        {
            "date": log.scraped_at,
            "price": log.price_cents / 100,
            "source": log.product_source.source.site_name if log.product_source and log.product_source.source else "Unknown"
        }
        for log in history
    ]


@router.delete("/all", status_code=status.HTTP_200_OK)
async def delete_all_tracked_products(db: Session = Depends(get_db)):
    # ... (this endpoint remains the same)
    try:
        deleted_count = crud_products.delete_all_products(db)
        return {"message": f"Successfully deleted {deleted_count} products."}
    except Exception as e:
        print(f"Error deleting all products: {e}")
        raise HTTPException(status_code=500, detail="Could not delete all products.")


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    # ... (this endpoint remains the same)
    success = crud_products.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}