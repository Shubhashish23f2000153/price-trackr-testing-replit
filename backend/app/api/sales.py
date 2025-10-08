from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..schemas.sale import SaleCreate, SaleResponse
from ..crud import sales as crud_sales

router = APIRouter()


@router.get("/", response_model=List[SaleResponse])
async def get_sales(region: str = None, db: Session = Depends(get_db)):
    """Get active sales for a region"""
    sales = crud_sales.get_active_sales(db, region)
    return sales


@router.post("/", response_model=SaleResponse)
async def create_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    """Create a new sale entry"""
    db_sale = crud_sales.create_sale(db, sale)
    return db_sale
