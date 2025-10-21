from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from urllib.parse import urlparse
from ..database import get_db
from ..schemas.product import ProductCreate, ProductResponse, ProductDetail
from ..schemas.extension import ProductDataFromExtension
from ..crud import products as crud_products
from ..crud import prices as crud_prices
from ..models import Product, Source, ProductSource, PriceLog
from ..utils.scraper_queue import enqueue_scrape

router = APIRouter()


@router.post("/add-from-extension", response_model=ProductResponse)
async def add_product_from_extension(product_data: ProductDataFromExtension, db: Session = Depends(get_db)):
    """Add a new product with data scraped from the extension."""
    
    existing_product_source = db.query(ProductSource).filter(ProductSource.url == product_data.url).first()
    if existing_product_source:
        return existing_product_source.product

    new_product = Product(
        title=product_data.title,
        brand=product_data.brand,
        description=product_data.description,
        image_url=product_data.imageUrl
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)

    parsed_url = urlparse(product_data.url)
    domain = parsed_url.netloc.replace('www.', '')
    source = db.query(Source).filter(Source.domain == domain).first()
    if not source:
        source = Source(domain=domain, site_name=domain.split('.')[0].title())
        db.add(source)
        db.commit()
        db.refresh(source)

    product_source = ProductSource(
        product_id=new_product.id,
        source_id=source.id,
        url=product_data.url
    )
    db.add(product_source)
    # Commit here to generate the product_source.id
    db.commit()
    db.refresh(product_source)
    
    price_log = PriceLog(
        product_source_id=product_source.id, # Now this ID exists
        price_cents=int(product_data.currentPrice * 100),
        currency="INR", # Assuming INR for now
        in_stock=True
    )
    db.add(price_log)
    
    db.commit()
    db.refresh(new_product)
    
    return new_product


@router.post("/track", response_model=ProductResponse)
async def track_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Add a new product to track by URL (for non-extension tracking)."""
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
    db.commit()
    
    try:
        enqueue_scrape(product.url, db_product.id, source.id)
    except Exception as e:
        print(f"Failed to enqueue scrape job: {e}")
    
    return db_product


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product details with current prices."""
    result = crud_products.get_product_with_prices(db, product_id)
    if not result:
        raise HTTPException(status_code=404, detail="Product not found")
    
    product = result["product"]
    prices = result["prices"]
    lowest_price = crud_prices.get_lowest_price(db, product_id)
    
    return {
        **product.__dict__,
        "prices": prices,
        "lowest_ever_price": lowest_price,
        "is_in_watchlist": False
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
    return [
        {
            "date": log.scraped_at,
            "price": log.price_cents / 100,
            "source": log.product_source.source.site_name
        }
        for log in history
    ]


@router.delete("/{product_id}")
async def delete_product(product_id: int, db: Session = Depends(get_db)):
    """Delete a tracked product."""
    success = crud_products.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}