from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class PriceLogBase(BaseModel):
    price_cents: int
    currency: str = "INR"
    availability: str = "Unknown"
    in_stock: bool = True


class PriceLogCreate(PriceLogBase):
    product_source_id: int


class PriceLogResponse(PriceLogBase):
    id: int
    product_source_id: int
    scraped_at: datetime
    
    class Config:
        from_attributes = True


class PriceHistory(BaseModel):
    date: datetime
    price: float
    source: str
