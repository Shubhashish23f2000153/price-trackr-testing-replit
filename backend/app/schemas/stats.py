from pydantic import BaseModel

class SpaceInfo(BaseModel):
    tracked_items: int
    price_points: int