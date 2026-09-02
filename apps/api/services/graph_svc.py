import datetime
from sqlalchemy.orm import Session
from apps.api.models.schema import Person, Obligation, PaymentEvent, ReconciliationRecord

class GraphService:
    @staticmethod
    def recalculate_person_ledger(db: Session, person_id: str):
        """
        Recalculates a counterparty's running ledger, trust score, and reliability metrics.
        """
        person = db.query(Person).filter(Person.id == person_id).first()
        if not person:
            return None
            
        # Sum obligations
        receivables = db.query(Obligation).filter(
            Obligation.person_id == person_id,
            Obligation.obligation_type.in_(["receivable", "invoice", "advance", "loan", "emi"])
        ).all()
        
        payables = db.query(Obligation).filter(
            Obligation.person_id == person_id,
            Obligation.obligation_type == "payable"
        ).all()
        
        total_given = sum(o.total_amount for o in receivables)
        
        # Sum payments received from this person
        inbound_payments = db.query(PaymentEvent).filter(
            PaymentEvent.person_id == person_id,
            PaymentEvent.direction == "inbound",
            PaymentEvent.status == "captured"
        ).all()
        total_received = sum(p.amount for p in inbound_payments)
        
        # Outstanding net
        net_outstanding = max(0.0, total_given - total_received)
        
        person.total_given = total_given
        person.total_received = total_received
        person.outstanding_balance = net_outstanding
        
        # Reliability & delay calculations
        overdue_count = sum(1 for o in receivables if o.status == "overdue")
        settled_count = sum(1 for o in receivables if o.status == "settled")
        total_obs = len(receivables)
        
        if total_obs > 0:
            reliability = max(10.0, min(100.0, 100.0 - (overdue_count * 20.0) + (settled_count * 5.0)))
            person.payment_reliability = round(reliability, 1)
            # Trust score calculation
            person.trust_score = round(max(5.0, min(99.0, (reliability * 0.7) + (30.0 if net_outstanding < 50000 else 10.0))), 1)
        
        person.updated_at = datetime.datetime.utcnow()
        db.commit()
        db.refresh(person)
        return person
