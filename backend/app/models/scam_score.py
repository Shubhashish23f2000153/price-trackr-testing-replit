from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.sql import func
from ..database import Base


class ScamScore(Base):
    __tablename__ = "scam_scores"

    id = Column(Integer, primary_key=True, index=True)
    domain = Column(String(200), unique=True, nullable=False, index=True)
    whois_days_old = Column(Integer, nullable=True)
    safe_browsing_flag = Column(Boolean, default=False)
    trust_signals = Column(Float, default=0.0)
    score = Column(Float, default=0.0)  # 0-100 (100 = safest)
    last_checked = Column(DateTime(timezone=True), server_default=func.now())
