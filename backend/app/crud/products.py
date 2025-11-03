# backend/app/crud/products.py
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from ..models import Product, ProductSource, Source, PriceLog, Seller # Import ProductSource
from ..schemas.product import ProductCreate, ProductUpdate
from datetime import datetime, timezone # Import datetime


def get_product(db: Session, product_id: int) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def get_products(db: Session, skip: int = 0, limit: int = 100) -> List[Product]:
    return db.query(Product).offset(skip).limit(limit).all()

# --- HELPER FUNCTION ---
def get_or_create_seller(db: Session, marketplace: str, seller_name: str, seller_rating: str, review_count: str) -> Optional[Seller]:
    """Upserts a seller in the database."""
    if not seller_name:
        return None
    
    try:
        # Try to find an existing seller by name and marketplace
        existing_seller = db.query(Seller).filter(
            Seller.marketplace == marketplace,
            Seller.seller_name == seller_name
        ).first()

        if existing_seller:
            # Update existing seller's info if it's new
            existing_seller.seller_rating = seller_rating or existing_seller.seller_rating
            existing_seller.review_count = review_count or existing_seller.review_count
            existing_seller.last_seen = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing_seller)
            return existing_seller
        else:
            # Create a new seller
            new_seller = Seller(
                marketplace=marketplace,
                seller_name=seller_name,
                seller_rating=seller_rating,
                review_count=review_count
            )
            db.add(new_seller)
            db.commit()
            db.refresh(new_seller)
            return new_seller
    except Exception as e:
        db.rollback()
        print(f"[API] Error in get_or_create_seller: {e}")
        return None
# --- END HELPER ---

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


# --- THIS IS THE NEWLY FIXED FUNCTION ---
def delete_product(db: Session, product_id: int) -> bool:
    """
    Deletes a single product and all its associated product sources.
    """
    db_product = get_product(db, product_id)
    if db_product:
        # 1. Explicitly delete all associated ProductSource entries first.
        # This stops the cron job from picking them up.
        db.query(ProductSource).filter(
            ProductSource.product_id == product_id
        ).delete(synchronize_session=False)
        
        # 2. Now delete the main Product entry
        db.delete(db_product)
        
        # 3. Commit both deletions
        db.commit()
        return True
    return False
# --- END NEWLY FIXED FUNCTION ---


def get_product_with_prices(db: Session, product_id: int):
    """Get product with all current prices from different sources"""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        return None

    prices = []
    
    # Query all product sources linked to this product
    product_sources = db.query(ProductSource).filter(ProductSource.product_id == product_id).all()

    for ps in product_sources:
        # Get the most recent price log for this specific product source
        latest_price = db.query(PriceLog).filter(
            PriceLog.product_source_id == ps.id
        ).order_by(desc(PriceLog.scraped_at)).first()
        
        # Get the seller info
        seller_info = db.query(Seller).filter(Seller.id == ps.seller_id).first()

        if latest_price:
            prices.append({
                "source_name": ps.source.site_name,
                "current_price": latest_price.price_cents / 100,
                "currency": latest_price.currency,
                "availability": latest_price.availability,
                "in_stock": latest_price.in_stock,
                "url": ps.url,
                "seller_name": seller_info.seller_name if seller_info else None,
                "seller_rating": seller_info.seller_rating if seller_info else None,
                "seller_review_count": seller_info.review_count if seller_info else None,
                "avg_review_sentiment": latest_price.avg_review_sentiment
            })

    return {"product": product, "prices": prices}


# --- THIS IS THE FIX FROM THE PREVIOUS MESSAGE (KEEP IT) ---
def delete_all_products(db: Session) -> int:
    """
    Deletes all products and their sources from the database.
    This explicitly deletes from ProductSource to prevent orphaned scrape jobs.
    """
    # Explicitly delete all ProductSource entries first. This stops the worker.
    db.query(ProductSource).delete(synchronize_session=False)
    
    # Then delete all Product entries
    num_deleted = db.query(Product).delete(synchronize_session=False)
    
    db.commit()
    return num_deleted
# --- END PREVIOUS FIX ---