from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from apps.api.core.database import get_db
from apps.api.engines.risk_engine import RiskEngine
from apps.api.models.schema import RiskEvent
from apps.api.schemas.schemas import RiskAnalysisRequest, RiskAnalysisResponse

router = APIRouter(prefix="/risk", tags=["Risk & Scam Shield"])

@router.post("/evaluate", response_model=RiskAnalysisResponse)
def evaluate_transaction_risk(payload: RiskAnalysisRequest, db: Session = Depends(get_db)):
    """
    Evaluates ML fraud risk and impersonation indicators for a transfer request
    """
    res = RiskEngine.evaluate_transaction_request(
        db=db,
        person_name=payload.person_name,
        amount=payload.amount,
        request_phone=payload.request_phone,
        destination_vpa=payload.destination_vpa,
        message_text=payload.message_text,
        claimed_person_id=payload.claimed_person_id
    )
    return res

@router.get("/events")
def list_risk_events(db: Session = Depends(get_db)):
    events = db.query(RiskEvent).order_by(RiskEvent.created_at.desc()).limit(20).all()
    results = []
    for r in events:
        results.append({
            "id": r.id,
            "person_name": r.person.canonical_name if r.person else "Unknown",
            "risk_score": r.risk_score,
            "risk_level": r.risk_level,
            "ml_probability": r.ml_probability,
            "flagged_signals": r.flagged_signals,
            "explanation": r.reason_explanation,
            "status": r.status,
            "date": r.created_at.strftime("%d %b %Y, %I:%M %p")
        })
    return results
