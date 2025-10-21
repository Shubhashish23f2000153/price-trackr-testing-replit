from pydantic import BaseModel
from typing import Optional

class ProductDataFromExtension(BaseModel):
    url: str
    title: str
    currentPrice: float
    imageUrl: Optional[str] = None
    brand: Optional[str] = None
    description: Optional[str] = None