from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from apps.api.engines.payment_memory import PaymentMemoryEngine
from apps.api.engines.relationship_graph import RelationshipGraphEngine
from apps.api.engines.recovery import RecoveryEngine
from apps.api.engines.risk_engine import RiskEngine
from apps.api.services.entity_res import EntityResolutionService

class FinovaAgentTools:
    @staticmethod
    def search_transactions(db: Session, query: str, user_id: str) -> Dict[str, Any]:
        """Searches past payments, UTRs, amounts, and proof metadata."""
        return PaymentMemoryEngine.find_my_money(db=db, query=query, user_id=user_id)

    @staticmethod
    def get_counterparty_profile(db: Session, name_or_phone: str) -> Dict[str, Any]:
        """Fetches full financial ledger, trust score, and active obligations for a person."""
        person, score, reason = EntityResolutionService.resolve_entity(db=db, name=name_or_phone, phone=name_or_phone)
        if not person:
            return {"found": False, "message": f"No record found for '{name_or_phone}'"}
        card = RelationshipGraphEngine.get_person_relationship_card(db=db, person_id=person.id)
        return {"found": True, "data": card}

    @staticmethod
    def check_payment_risk(
        db: Session,
        name: str,
        amount: float,
        phone: Optional[str] = None,
        vpa: Optional[str] = None,
        message: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assesses ML fraud and impersonation risk for a pending payment transfer."""
        return RiskEngine.evaluate_transaction_request(
            db=db,
            person_name=name,
            amount=amount,
            request_phone=phone,
            destination_vpa=vpa,
            message_text=message
        )

    @staticmethod
    def list_overdue_obligations(db: Session, user_id: str) -> List[Dict[str, Any]]:
        """Lists all outstanding and overdue receivables requiring recovery."""
        return RecoveryEngine.evaluate_receivables_at_risk(db=db, user_id=user_id)
