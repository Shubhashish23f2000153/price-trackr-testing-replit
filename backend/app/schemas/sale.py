from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SaleBase(BaseModel):
    title: str
    description: Optional[str] = None
    discount_percentage: Optional[float] = None
    source_domain: str
    region: str = "Global"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SaleCreate(SaleBase):
    is_active: bool = True


class SaleResponse(SaleBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
