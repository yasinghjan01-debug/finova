from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional

from apps.api.core.database import get_db
from apps.api.engines.recovery import RecoveryEngine
from apps.api.core.auth import get_current_user

router = APIRouter(prefix="/recovery", tags=["Revenue Recovery"])

@router.get("/at-risk")
def get_receivables_at_risk(db: Session = Depends(get_db)):
    user_id = "user_finova_master_001"
    return RecoveryEngine.evaluate_receivables_at_risk(db, user_id)

@router.post("/dispatch")
def dispatch_recovery(
    obligation_id: str = Body(..., embed=True),
    custom_message: Optional[str] = Body(None, embed=True),
    db: Session = Depends(get_db)
):
    user_id = "user_finova_master_001"
    res = RecoveryEngine.prepare_and_dispatch_recovery(
        db=db,
        obligation_id=obligation_id,
        user_id=user_id,
        custom_message=custom_message
    )
    return res

@router.post("/stop")
def stop_recovery(
    obligation_id: str = Body(..., embed=True),
    reason: str = Body("User requested hold", embed=True),
    db: Session = Depends(get_db)
):
    user_id = "user_finova_master_001"
    return RecoveryEngine.stop_recovery(
        db=db,
        obligation_id=obligation_id,
        reason=reason,
        user_id=user_id
    )
