from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from ..database import get_db
from ..schemas.sale import SaleCreate, SaleResponse
from ..crud import sales as crud_sales
from ..models import Sale
from sqlalchemy import or_

router = APIRouter()


@router.get("/", response_model=List[SaleResponse])
async def get_sales(
    region: Optional[str] = None, 
    status: Optional[str] = Query(None, enum=["ongoing", "upcoming"]),
    db: Session = Depends(get_db)
):
    """Get active sales, with optional filtering by region and status (ongoing/upcoming)"""
    query = db.query(Sale).filter(Sale.is_active == True)
    
    if region:
        query = query.filter(Sale.region == region)

    if status:
        now = datetime.now(timezone.utc)
        if status == "ongoing":
            query = query.filter(
                or_(Sale.start_date == None, Sale.start_date <= now),
                or_(Sale.end_date == None, Sale.end_date >= now)
            )
        elif status == "upcoming":
            query = query.filter(Sale.start_date > now)
            
    return query.all()


@router.post("/", response_model=SaleResponse)
async def create_sale(sale: SaleCreate, db: Session = Depends(get_db)):
    """Create a new sale entry"""
    db_sale = crud_sales.create_sale(db, sale)
    return db_sale

@router.delete("/all", status_code=status.HTTP_200_OK)
async def delete_all_tracked_sales(db: Session = Depends(get_db)):
    """Deletes all sales from the database."""
    try:
        deleted_count = crud_sales.delete_all_sales(db)
        return {"message": f"Successfully deleted {deleted_count} sales."}
    except Exception as e:
        print(f"Error deleting all sales: {e}")
        raise HTTPException(status_code=500, detail="Could not delete all sales.")