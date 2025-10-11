from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime


class WatchlistBase(BaseModel):
    product_id: int
    alert_rules: Optional[Dict[str, Any]] = None


class WatchlistCreate(WatchlistBase):
    user_id: Optional[str] = None


# NEW - Schema for updating an alert
class WatchlistUpdate(BaseModel):
    alert_rules: Optional[Dict[str, Any]] = None


class WatchlistResponse(WatchlistBase):
    id: int
    user_id: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True