from fastapi import APIRouter, Depends, HTTPException, status # Ensure status is imported
from sqlalchemy.orm import Session
from typing import List
from urllib.parse import urlparse
from ..database import get_db
# Corrected Imports Start Here
from ..schemas.product import ProductCreate, ProductResponse, ProductDetail
from ..schemas.price import PriceHistory
from ..schemas.extension import ProductDataFromExtension # Added missing import
from ..crud import products as crud_products
from ..crud import prices as crud_prices
from ..models import Product, Source, ProductSource, PriceLog # Added missing Product, PriceLog
from ..crud import watchlist as crud_watchlist # Import watchlist crud
from ..schemas.watchlist import WatchlistCreate # Import watchlist schema
# Corrected Imports End Here
from ..utils.scraper_queue import enqueue_scrape

router = APIRouter()


@router.post("/add-from-extension") # Removed response_model for flexibility
async def add_product_from_extension(product_data: ProductDataFromExtension, db: Session = Depends(get_db)):
    """Add a new product with data scraped from the extension.
       Returns the product data and a flag indicating if it was newly created.
       !! WARNING: This version allows duplicate entries for the same URL !!"""

    # --- DUPLICATE CHECK REMOVED ---
    # existing_product_source = db.query(ProductSource).filter(ProductSource.url == product_data.url).first()
    # if existing_product_source:
    #     # If it exists, return the existing product and set newly_created to False
    #     product_dict = {column.name: getattr(existing_product_source.product, column.name) for column in existing_product_source.product.__table__.columns}
    #     return {**product_dict, "newly_created": False}
    # --- END OF REMOVED BLOCK ---


    # --- Create the product entry (this will now happen every time) ---
    new_product = Product(
        title=product_data.title,
        brand=product_data.brand,
        description=product_data.description,
        image_url=product_data.imageUrl
    )
    db.add(new_product)
    # Commit here to get the new_product.id
    try:
        db.commit()
        db.refresh(new_product)
    except Exception as e:
        db.rollback()
        print(f"Error creating product: {e}")
        raise HTTPException(status_code=500, detail="Database error while creating product.")


    # Find or create the source
    parsed_url = urlparse(product_data.url)
    domain = parsed_url.netloc.replace('www.', '')
    source = db.query(Source).filter(Source.domain == domain).first()
    if not source:
        source = Source(domain=domain, site_name=domain.split('.')[0].title())
        db.add(source)
        try:
            db.commit()
            db.refresh(source)
        except Exception as e:
            db.rollback()
            # Attempt to delete the product we just created if source fails
            db.delete(new_product)
            db.commit()
            print(f"Error creating source, rolled back product: {e}")
            raise HTTPException(status_code=500, detail="Database error while creating source.")


    # Link the product to the source
    product_source = ProductSource(
        product_id=new_product.id,
        source_id=source.id,
        url=product_data.url
    )
    db.add(product_source)
    # Commit here to generate the product_source.id
    try:
        db.commit()
        db.refresh(product_source)
    except Exception as e:
        db.rollback()
         # Attempt cleanup
        if not db.query(ProductSource).filter(ProductSource.product_id == new_product.id).count():
             db.delete(new_product)
        db.commit()
        print(f"Error creating product source, potential rollback: {e}")
        raise HTTPException(status_code=500, detail="Database error while linking product source.")


    # Add the initial price log
    price_log = PriceLog(
        product_source_id=product_source.id,
        price_cents=int(product_data.currentPrice * 100),
        currency="INR", # Assuming INR for now
        in_stock=True
    )
    db.add(price_log)

    # Final commit for the price log
    try:
        db.commit()
        db.refresh(new_product) # Refresh to get final state
    except Exception as e:
         db.rollback()
         # Attempt cleanup
         if not db.query(PriceLog).filter(PriceLog.product_source_id == product_source.id).count():
            db.delete(product_source)
            if not db.query(ProductSource).filter(ProductSource.product_id == new_product.id).count():
                 db.delete(new_product)
         db.commit()
         print(f"Error creating price log, potential rollback: {e}")
         raise HTTPException(status_code=500, detail="Database error while saving initial price.")

    # Always return newly_created as True now
    product_dict = {column.name: getattr(new_product, column.name) for column in new_product.__table__.columns}
    return {**product_dict, "newly_created": True}


@router.post("/track", response_model=ProductResponse)
async def track_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Add a new product to track by URL (used by the web app's +Add page)."""
    # Check if product source URL already exists
    existing_product_source = db.query(ProductSource).filter(ProductSource.url == product.url).first()
    if existing_product_source:
        print(f"URL already tracked: {product.url}")
        return existing_product_source.product # Return existing if URL matches

    # If not existing, create the product
    db_product = crud_products.create_product(db, product)

    parsed_url = urlparse(product.url)
    domain = parsed_url.netloc.replace('www.', '')

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
    db.commit() # Commit source before enqueuing

    # Enqueue scraping job for the background worker
    try:
        enqueue_scrape(product.url, db_product.id, source.id)
        print(f"Enqueued scrape job for: {product.url}")
    except Exception as e:
        print(f"Failed to enqueue scrape job for {product.url}: {e}")

    return db_product


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product details with current prices and watchlist status."""
    result = crud_products.get_product_with_prices(db, product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")

    product_obj = result["product"]
    prices = result["prices"]
    lowest_price = crud_prices.get_lowest_price(db, product_id)

    # Check if the product is in the watchlist (assuming anonymous user for now)
    # TODO: Modify this when user accounts are implemented
    is_watchlisted_flag = crud_watchlist.is_in_watchlist(db, product_id=product_id)

    # Convert SQLAlchemy model instance to dict before adding extra keys
    product_dict = {column.name: getattr(product_obj, column.name) for column in product_obj.__table__.columns}


    return {
        **product_dict, # Use the converted dict
        "prices": prices,
        "lowest_ever_price": lowest_price,
        "is_in_watchlist": is_watchlisted_flag
    }


@router.get("/", response_model=List[ProductResponse])
async def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all tracked products."""
    products = crud_products.get_products(db, skip=skip, limit=limit)
    return products


@router.get("/{product_id}/history")
async def get_price_history(product_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get price history for a product."""
    history = crud_prices.get_price_history(db, product_id, days)
    # Ensure log.product_source and log.product_source.source are loaded
    return [
        {
            "date": log.scraped_at,
            "price": log.price_cents / 100,
            "source": log.product_source.source.site_name if log.product_source and log.product_source.source else "Unknown"
        }
        for log in history
    ]

# --- ROUTE ORDER FIX ---
# The /all route MUST be defined *before* the /{product_id} route
# to avoid "/all" being interpreted as a product_id.

@router.delete("/all", status_code=status.HTTP_200_OK)
async def delete_all_tracked_products(db: Session = Depends(get_db)):
    """Deletes all tracked products from the database."""
    try:
        # Ensure the CRUD function commits the change
        deleted_count = crud_products.delete_all_products(db)
        return {"message": f"Successfully deleted {deleted_count} products."}
    except Exception as e:
        print(f"Error deleting all products: {e}") # Log the specific error
        raise HTTPException(status_code=500, detail="Could not delete all products.")


@router.delete("/{product_id}", status_code=status.HTTP_200_OK)
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a tracked product."""
    success = crud_products.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}