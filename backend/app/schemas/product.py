from pydantic import BaseModel, HttpUrl
from typing import Optional, List
from datetime import datetime


class ProductBase(BaseModel):
    title: str
    sku: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None


class ProductCreate(ProductBase):
    url: str  # Initial URL to scrape


class ProductUpdate(BaseModel):
    title: Optional[str] = None
    brand: Optional[str] = None
    category: Optional[str] = None
    image_url: Optional[str] = None
    description: Optional[str] = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class PriceInfo(BaseModel):
    source_name: str
    current_price: float
    currency: str
    availability: str
    in_stock: bool
    url: str
    lowest_price: Optional[float] = None
    highest_price: Optional[float] = None


class ProductDetail(ProductResponse):
    prices: List[PriceInfo] = []
    lowest_ever_price: Optional[float] = None
    is_in_watchlist: bool = False
