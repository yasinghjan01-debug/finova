from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from apps.api.core.database import get_db
from apps.api.models.schema import AuditLog
from apps.api.services.audit_svc import AuditChainService

router = APIRouter(prefix="/audit", tags=["Cryptographic Audit Chain"])

@router.get("")
def list_audit_logs(db: Session = Depends(get_db)):
    user_id = "user_finova_master_001"
    logs = db.query(AuditLog).order_by(AuditLog.sequence_number.desc(), AuditLog.created_at.desc()).limit(50).all()
    results = []
    for l in logs:
        results.append({
            "id": l.id,
            "sequence_number": l.sequence_number,
            "previous_hash": l.previous_hash,
            "event_hash": l.event_hash,
            "event_type": l.event_type,
            "actor": l.actor,
            "details": l.details,
            "timestamp": l.created_at.strftime("%d %b %Y, %I:%M:%S %p") if l.created_at else ""
        })
    return results

@router.get("/verify")
def verify_audit_chain(db: Session = Depends(get_db)):
    """
    Mathematical Tamper-Evidence Verification:
    Walks entire SHA-256 hash chain from sequence #1 to latest.
    """
    is_valid, count, message = AuditChainService.verify_audit_chain(db)
    return {
        "is_tamper_evident_valid": is_valid,
        "records_verified": count,
        "verification_message": message,
        "cryptographic_algorithm": "SHA-256 Hash Chaining"
    }
