import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from apps.api.models.schema import Person, Obligation, PaymentEvent, Identity, RiskEvent
from apps.api.services.graph_svc import GraphService

class RelationshipGraphEngine:
    @staticmethod
    def get_person_relationship_card(db: Session, person_id: str) -> Optional[Dict[str, Any]]:
        """
        Engine 2: Comprehensive Relationship Card and Trust Profile
        """
        person = GraphService.recalculate_person_ledger(db, person_id)
        if not person:
            return None
            
        identities = db.query(Identity).filter(Identity.person_id == person_id).all()
        obligations = db.query(Obligation).filter(Obligation.person_id == person_id).order_by(desc(Obligation.created_at)).all()
        payments = db.query(PaymentEvent).filter(PaymentEvent.person_id == person_id).order_by(desc(PaymentEvent.payment_date)).all()
        risks = db.query(RiskEvent).filter(RiskEvent.person_id == person_id).order_by(desc(RiskEvent.created_at)).all()
        
        # Build unified chronological timeline
        timeline = []
        for ob in obligations:
            timeline.append({
                "type": "OBLIGATION",
                "title": f"Obligation created: {ob.title}",
                "amount": ob.total_amount,
                "remaining": ob.remaining_amount,
                "status": ob.status,
                "date": ob.created_at.strftime("%d %b %Y, %I:%M %p"),
                "timestamp": ob.created_at.timestamp()
            })
        for p in payments:
            timeline.append({
                "type": "PAYMENT",
                "title": f"Payment received via {p.source}",
                "amount": p.amount,
                "utr": p.utr_rrn,
                "status": p.status,
                "date": p.payment_date.strftime("%d %b %Y, %I:%M %p") if p.payment_date else "N/A",
                "timestamp": p.payment_date.timestamp() if p.payment_date else 0
            })
        for r in risks:
            timeline.append({
                "type": "RISK_ALERT",
                "title": f"Risk flagged: {r.risk_level} ({int(r.risk_score)}/100)",
                "amount": None,
                "status": r.status,
                "date": r.created_at.strftime("%d %b %Y, %I:%M %p"),
                "timestamp": r.created_at.timestamp()
            })
            
        timeline.sort(key=lambda x: x["timestamp"], reverse=True)
        
        return {
            "id": person.id,
            "canonical_name": person.canonical_name,
            "category": person.category,
            "primary_phone": person.primary_phone,
            "primary_vpa": person.primary_vpa,
            "trust_score": person.trust_score,
            "payment_reliability": person.payment_reliability,
            "avg_delay_days": person.avg_delay_days,
            "total_given": person.total_given,
            "total_received": person.total_received,
            "outstanding_balance": person.outstanding_balance,
            "identities": [
                {
                    "type": i.identity_type,
                    "value": i.identity_value,
                    "verified": i.verified,
                    "confidence": i.confidence_score,
                    "source": i.source
                } for i in identities
            ],
            "open_obligations": [
                {
                    "id": o.id,
                    "title": o.title,
                    "total_amount": o.total_amount,
                    "settled_amount": o.settled_amount,
                    "remaining_amount": o.remaining_amount,
                    "status": o.status,
                    "due_date": o.due_date.strftime("%d %b %Y") if o.due_date else "No due date"
                } for o in obligations if o.status in ["pending", "partial", "overdue"]
            ],
            "timeline": timeline
        }
        
    @staticmethod
    def get_all_relationships(db: Session, user_id: str) -> List[Dict[str, Any]]:
        people = db.query(Person).filter(Person.user_id == user_id).all()
        results = []
        for p in people:
            GraphService.recalculate_person_ledger(db, p.id)
            results.append({
                "id": p.id,
                "canonical_name": p.canonical_name,
                "category": p.category,
                "primary_phone": p.primary_phone,
                "primary_vpa": p.primary_vpa,
                "trust_score": p.trust_score,
                "payment_reliability": p.payment_reliability,
                "total_given": p.total_given,
                "total_received": p.total_received,
                "outstanding_balance": p.outstanding_balance,
                "status": "Healthy" if p.trust_score >= 70 else ("Needs Attention" if p.trust_score >= 40 else "High Risk")
            })
        return sorted(results, key=lambda x: x["outstanding_balance"], reverse=True)
