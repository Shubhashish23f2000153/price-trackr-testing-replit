from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import ScamScore

router = APIRouter()


@router.get("/check")
async def check_scam(domain: str = Query(...), db: Session = Depends(get_db)):
    """Check scam score for a domain"""
    scam_score = db.query(ScamScore).filter(ScamScore.domain == domain).first()
    
    if not scam_score:
        # Default safe score if not in database
        return {
            "domain": domain,
            "score": 50.0,
            "trust_level": "unknown",
            "message": "No data available for this domain"
        }
    
    trust_level = "high" if scam_score.score >= 70 else "medium" if scam_score.score >= 40 else "low"
    
    return {
        "domain": domain,
        "score": scam_score.score,
        "trust_level": trust_level,
        "whois_days_old": scam_score.whois_days_old,
        "safe_browsing_flag": scam_score.safe_browsing_flag
    }
