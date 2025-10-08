from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.product import ProductCreate, ProductResponse, ProductDetail
from ..schemas.price import PriceHistory
from ..crud import products as crud_products
from ..crud import prices as crud_prices

router = APIRouter()


@router.post("/track", response_model=ProductResponse)
async def track_product(product: ProductCreate, db: Session = Depends(get_db)):
    """Add a new product to track by URL"""
    db_product = crud_products.create_product(db, product)
    return db_product


@router.get("/{product_id}", response_model=ProductDetail)
async def get_product(product_id: int, db: Session = Depends(get_db)):
    """Get product details with current prices"""
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
        "is_in_watchlist": False  # TODO: Check actual watchlist
    }


@router.get("/", response_model=List[ProductResponse])
async def list_products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all tracked products"""
    products = crud_products.get_products(db, skip=skip, limit=limit)
    return products


@router.get("/{product_id}/history")
async def get_price_history(product_id: int, days: int = 30, db: Session = Depends(get_db)):
    """Get price history for a product"""
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
    """Delete a tracked product"""
    success = crud_products.delete_product(db, product_id)
    if not success:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted successfully"}
