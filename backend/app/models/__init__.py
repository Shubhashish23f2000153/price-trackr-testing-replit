# backend/app/models/__init__.py
from .product import Product
from .source import Source, ProductSource
from .price_log import PriceLog
from .watchlist import Watchlist
from .scam_score import ScamScore
from .sale import Sale
from .user import User
from .seller import Seller
from .price_aggregate import PriceHistoryDaily, PriceHistoryMonthly # <-- ADD THIS LINE

__all__ = [
    "Product",
    "Source",
    "ProductSource",
    "PriceLog",
    "Watchlist",
    "ScamScore",
    "Sale",
    "User",
    "Seller",
    "PriceHistoryDaily", # <-- ADD THIS LINE
    "PriceHistoryMonthly" # <-- ADD THIS LINE
]