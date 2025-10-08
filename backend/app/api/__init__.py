from fastapi import APIRouter
from . import products, watchlist, sales, scam

api_router = APIRouter()

api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(scam.router, prefix="/scam", tags=["scam"])
