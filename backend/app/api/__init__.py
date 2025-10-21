from fastapi import APIRouter
from . import products, watchlist, sales, scam, stats # 1. Import stats
from . import cron  # 1. Import cron

api_router = APIRouter()

api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(scam.router, prefix="/scam", tags=["scam"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"]) # 2. Add this line
api_router.include_router(cron.router, prefix="/cron", tags=["cron"])  # 2. Add this line