import datetime
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from apps.api.core.database import get_db
from apps.api.models.schema import ApprovalRequest, AuditLog
from apps.api.schemas.schemas import ApprovalRead, ApprovalAction
from apps.api.services.audit_svc import AuditChainService

router = APIRouter(prefix="/approvals", tags=["AI Action Center & Approvals"])

@router.get("", response_model=List[ApprovalRead])
def list_pending_approvals(db: Session = Depends(get_db)):
    """
    AI Actions Waiting For You
    """
    approvals = db.query(ApprovalRequest).filter(ApprovalRequest.status == "pending").order_by(ApprovalRequest.created_at.desc()).all()
    return approvals

@router.post("/{approval_id}/decision")
def resolve_approval_action(
    approval_id: str,
    payload: ApprovalAction,
    db: Session = Depends(get_db)
):
    user_id = "user_finova_master_001"
    approval = db.query(ApprovalRequest).filter(ApprovalRequest.id == approval_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval request not found")
        
    decision = payload.decision.lower()
    if decision not in ["approve", "reject", "escalate"]:
        raise HTTPException(status_code=400, detail="Invalid decision. Must be 'approve', 'reject', or 'escalate'")
        
    approval.status = "approved" if decision == "approve" else ("rejected" if decision == "reject" else "escalated")
    approval.user_decision_note = payload.note or f"Action {decision}d by user."
    approval.resolved_at = datetime.datetime.utcnow()
    
    # Audit log via Cryptographic Hash Chain
    AuditChainService.record_event(
        db=db,
        user_id=user_id,
        event_type=f"USER_{decision.upper()}D_ACTION",
        actor="USER",
        details={
            "approval_id": approval.id,
            "action_type": approval.action_type,
            "title": approval.title,
            "amount": approval.amount,
            "note": approval.user_decision_note
        }
    )
    
    db.commit()
    return {
        "success": True,
        "approval_id": approval.id,
        "status": approval.status,
        "message": f"Action successfully {approval.status}."
    }
