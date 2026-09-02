import json
import hashlib
import datetime
from typing import Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from apps.api.models.schema import AuditLog

GENESIS_HASH = "0" * 64

class AuditChainService:
    @staticmethod
    def calculate_event_hash(
        sequence_number: int,
        previous_hash: str,
        event_type: str,
        actor: str,
        timestamp_epoch: int,
        details: Dict[str, Any]
    ) -> str:
        """
        Cryptographic SHA-256 Hash Chaining with Deterministic Integer Epoch Time:
        H(n) = SHA256(sequence_number || previous_hash || event_type || actor || timestamp_epoch || canonical_json(details))
        """
        canonical_details = json.dumps(details, sort_keys=True, default=str)
        payload = f"{sequence_number}|{previous_hash}|{event_type}|{actor}|{timestamp_epoch}|{canonical_details}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    @classmethod
    def record_event(
        cls,
        db: Session,
        event_type: str,
        actor: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> AuditLog:
        """
        Appends a new tamper-evident audit record to the cryptographic chain.
        """
        latest = db.query(AuditLog).order_by(AuditLog.sequence_number.desc()).first()
        
        if latest and latest.sequence_number is not None:
            seq = latest.sequence_number + 1
            prev_hash = latest.event_hash or GENESIS_HASH
        else:
            seq = 1
            prev_hash = GENESIS_HASH
            
        now = datetime.datetime.utcnow()
        timestamp_epoch = int(now.timestamp())
        
        event_hash = cls.calculate_event_hash(
            sequence_number=seq,
            previous_hash=prev_hash,
            event_type=event_type,
            actor=actor,
            timestamp_epoch=timestamp_epoch,
            details=details
        )
        
        log_entry = AuditLog(
            user_id=user_id,
            sequence_number=seq,
            previous_hash=prev_hash,
            event_hash=event_hash,
            event_type=event_type,
            actor=actor,
            details=details,
            ip_address=ip_address,
            created_at=now
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry

    @classmethod
    def verify_audit_chain(cls, db: Session) -> Tuple[bool, int, str]:
        """
        Validates mathematical integrity of entire audit log chain.
        """
        logs = db.query(AuditLog).order_by(AuditLog.sequence_number.asc()).all()
        if not logs:
            return (True, 0, "Audit chain is empty. Integrity verified.")
            
        expected_prev = GENESIS_HASH
        for idx, log in enumerate(logs):
            seq = log.sequence_number or (idx + 1)
            
            if log.previous_hash != expected_prev:
                return (
                    False,
                    idx,
                    f"TAMPER DETECTED at sequence {seq}: previous_hash mismatch. Expected {expected_prev}, found {log.previous_hash}"
                )
                
            epoch = int(log.created_at.timestamp()) if log.created_at else 0
            recomputed = cls.calculate_event_hash(
                sequence_number=seq,
                previous_hash=log.previous_hash,
                event_type=log.event_type,
                actor=log.actor,
                timestamp_epoch=epoch,
                details=log.details or {}
            )
            
            if log.event_hash != recomputed:
                return (
                    False,
                    idx,
                    f"TAMPER DETECTED at sequence {seq}: event_hash mismatch."
                )
                
            expected_prev = log.event_hash
            
        return (True, len(logs), f"Audit chain verified successfully: {len(logs)} tamper-evident records intact.")
