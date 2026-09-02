from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional

from apps.api.core.database import get_db
from apps.api.engines.reconciliation import ReconciliationEngine

router = APIRouter(prefix="/reconciliation", tags=["Reconciliation"])

@router.get("/honest-exceptions")
def get_honest_exceptions(db: Session = Depends(get_db)):
    """
    Razorpay Revenue Recovery Special: Honest Exceptions list of ambiguous cases
    """
    user_id = "user_finova_master_001"
    return ReconciliationEngine.get_honest_exceptions(db, user_id)

@router.post("/match")
def manual_or_auto_reconcile(
    payment_event_id: str = Body(..., embed=True),
    obligation_id: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    user_id = "user_finova_master_001"
    res = ReconciliationEngine.reconcile_payment(
        db=db,
        payment_event_id=payment_event_id,
        user_id=user_id,
        force_manual_ob_id=obligation_id
    )
    return res
