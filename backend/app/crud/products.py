from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from ..models import Product, ProductSource, Source, PriceLog
from ..schemas.product import ProductCreate, ProductUpdate


def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    return db.query(Product).offset(skip).limit(limit).all()


def create_product(db: Session, product: ProductCreate) -> Product:
    db_product = Product(
        title=product.title,
        sku=product.sku,
        brand=product.brand,
        category=product.category,
        image_url=product.image_url,
        description=product.description
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


def update_product(db: Session, product_id: int, product: ProductUpdate) -> Optional[Product]:
    db_product = get_product(db, product_id)
    if db_product:
        update_data = product.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_product, key, value)
        db.commit()
        db.refresh(db_product)
    return db_product


def delete_product(db: Session, product_id: int) -> bool:
    db_product = get_product(db, product_id)
    if db_product:
        db.delete(db_product)
        db.commit()
        return True
    return False


def get_product_with_prices(db: Session, product_id: int):
    """Get product with all current prices from different sources"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None
    
    prices = []
    for ps in product.product_sources:
        latest_price = db.query(PriceLog).filter(
            PriceLog.product_source_id == ps.id
        ).order_by(desc(PriceLog.scraped_at)).first()
        
        if latest_price:
            prices.append({
                "source_name": ps.source.site_name,
                "current_price": latest_price.price_cents / 100,
                "currency": latest_price.currency,
                "availability": latest_price.availability,
                "in_stock": latest_price.in_stock,
                "url": ps.url
            })
    
    return {"product": product, "prices": prices}
