from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from urllib.parse import urlparse
from ..database import get_db
# Corrected Imports
from ..schemas.product import ProductCreate, ProductResponse, ProductDetail, ProductWithHistorySchema
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
    # ... (this endpoint remains the same)
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

    # --- UPDATED: Create Seller during product add ---
    marketplace_name = domain.split('.')[0].title()
    seller = crud_products.get_or_create_seller(
        db,
        marketplace=marketplace_name,
        seller_name=product_data.brand or "Unknown", # Use brand as fallback
        seller_rating=None,
        review_count=None
    )
    # --- END UPDATE ---

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
        currency="INR",
        in_stock=True
    )
    db.add(price_log)
    db.commit()
    db.refresh(new_product)

    product_dict = {column.name: getattr(new_product, column.name) for column in new_product.__table__.columns}
    return {**product_dict, "newly_created": True}


@router.post("/track", response_model=ProductResponse)
async def track_product(product: ProductCreate, db: Session = Depends(get_db)):
    # ... (this endpoint remains mostly the same)
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

    # --- UPDATED: Create a default Seller on track ---
    marketplace_name = domain.split('.')[0].title()
    seller = crud_products.get_or_create_seller(
        db,
        marketplace=marketplace_name,
        seller_name=product.brand or "Unknown", # Use brand as fallback
        seller_rating=None,
        review_count=None
    )
    # --- END UPDATE ---

    product_source = ProductSource(
        product_id=db_product.id,
        source_id=source.id,
        seller_id=seller.id if seller else None, # Link seller
        url=product.url
    )
    db.add(product_source)
    db.commit()

    try:
        enqueue_scrape(product.url, db_product.id, product_source.id) # Pass product_source.id
        print(f"Enqueued scrape job for: {product.url}")
    except Exception as e:
        print(f"Failed to enqueue scrape job for {product.url}: {e}")

    return db_product


@router.get("/export", response_model=List[ProductWithHistorySchema])
async def export_all_data(db: Session = Depends(get_db)):
    # ... (this endpoint remains the same)
    try:
        all_products = crud_products.get_products(db, skip=0, limit=10000)
        export_data = []
        
        for product in all_products:
            product_dict = {column.name: getattr(product, column.name) for column in product.__table__.columns}
            
            # --- UPDATED: Use new history function ---
            history_data = crud_prices.get_flexible_price_history(db, product.id, range_option="all")
            
            # Format data to match the old schema for export
            history_list = [
                {
                    "date": item["date"],
                    "price": item["price"],
                    "source": item["source"]
                }
                for item in history_data
            ]
            # --- END UPDATE ---
            
            product_with_history = {**product_dict, "price_history": history_list}
            export_data.append(product_with_history)
            
        return export_data
        
    except Exception as e:
        print(f"Error exporting data: {e}")
        raise HTTPException(status_code=500, detail="Failed to export data.")


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    # This endpoint is now correct because crud_products.get_product_with_prices
    # was already updated to read from the 'sellers' table.
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


# --- THIS IS THE UPDATED ENDPOINT ---
@router.get("/{product_id}/history", response_model=List[PriceHistory])
async def get_price_history(
    product_id: int, 
    range: RangeOption = Query("30d", description="Time range for history (e.g., 7d, 1y, all)"),
    db: Session = Depends(get_db)
):
    """
    Get price history for a product, aggregated based on the time range.
    """
    history_data = crud_prices.get_flexible_price_history(db, product_id, range_option=range)
    
    # Convert data to PriceHistory schema
    return [
        PriceHistory(
            date=item["date"],
            price=item["price"],
            source=item["source"]
        )
        for item in history_data
    ]
# --- END UPDATED ENDPOINT ---


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