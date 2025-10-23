from fastapi import APIRouter

# Import each individual router file directly
from . import products
from . import watchlist
from . import sales
from . import scam
from . import stats
from . import cron
from . import user

# Create the main API router instance
api_router = APIRouter()

# Include each router using the imported module and its 'router' instance
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(scam.router, prefix="/scam", tags=["scam"])
api_router.include_router(stats.router, prefix="/stats", tags=["stats"])
api_router.include_router(cron.router, prefix="/cron", tags=["cron"])
api_router.include_router(user.router, prefix="/users", tags=["users"]) # Include the user router