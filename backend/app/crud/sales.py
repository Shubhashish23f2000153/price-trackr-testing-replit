from sqlalchemy.orm import Session
from typing import List
from ..models import Sale
from ..schemas.sale import SaleCreate


def create_sale(db: Session, sale: SaleCreate) -> Sale:
    db_sale = Sale(**sale.model_dump())
    db.add(db_sale)
    db.commit()
    db.refresh(db_sale)
    return db_sale


def get_active_sales(db: Session, region: str = None) -> List[Sale]:
    query = db.query(Sale).filter(Sale.is_active == True)
    if region:
        query = query.filter(Sale.region == region)
    return query.all()


def get_all_sales(db: Session) -> List[Sale]:
    return db.query(Sale).all()

def delete_all_sales(db: Session) -> int:
    """Deletes all sales from the database and returns the count."""
    num_deleted = db.query(Sale).delete()
    db.commit()
    return num_deleted