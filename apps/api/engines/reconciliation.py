import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from apps.api.models.schema import PaymentEvent, Obligation, ReconciliationRecord, Person, AuditLog
from apps.api.services.graph_svc import GraphService

class ReconciliationEngine:
    @staticmethod
    def reconcile_payment(
        db: Session,
        payment_event_id: str,
        user_id: str,
        force_manual_ob_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Engine 3: Core Reconciliation Workflow
        Determines: Which obligation does this payment belong to?
        """
        payment = db.query(PaymentEvent).filter(PaymentEvent.id == payment_event_id).first()
        if not payment:
            return {"success": False, "reason": "Payment not found"}
            
        if force_manual_ob_id:
            ob = db.query(Obligation).filter(Obligation.id == force_manual_ob_id).first()
            if not ob:
                return {"success": False, "reason": "Target obligation not found"}
            
            matched_amt = min(ob.remaining_amount, payment.amount)
            rec = ReconciliationRecord(
                obligation_id=ob.id,
                payment_event_id=payment.id,
                matched_amount=matched_amt,
                match_confidence=1.0,
                match_strategy="manual_user_override",
                notes=f"User manually reconciled against '{ob.title}'"
            )
            db.add(rec)
            ob.settled_amount += matched_amt
            ob.remaining_amount -= matched_amt
            if ob.remaining_amount <= 0:
                ob.status = "settled"
                ob.recovery_stage = "recovered"
            else:
                ob.status = "partial"
                
            db.commit()
            if ob.person_id:
                GraphService.recalculate_person_ledger(db, ob.person_id)
            return {"success": True, "reconciled": True, "obligation_title": ob.title, "matched_amount": matched_amt}

        # Auto-match search
        if not payment.person_id:
            return {
                "success": False,
                "reconciled": False,
                "reason": "Unassigned entity: Payment not linked to a known person. Added to Honest Exceptions."
            }
            
        person = db.query(Person).filter(Person.id == payment.person_id).first()
        open_obs = db.query(Obligation).filter(
            Obligation.person_id == payment.person_id,
            Obligation.status.in_(["pending", "partial", "overdue"])
        ).order_by(Obligation.due_date.asc(), Obligation.created_at.asc()).all()
        
        if not open_obs:
            return {
                "success": True,
                "reconciled": False,
                "reason": f"No open obligations found for {person.canonical_name}. Retained as unallocated credit."
            }
            
        # Strategy 1: Exact Amount Match
        exact_match = next((o for o in open_obs if abs(o.remaining_amount - payment.amount) < 0.01), None)
        if exact_match:
            rec = ReconciliationRecord(
                obligation_id=exact_match.id,
                payment_event_id=payment.id,
                matched_amount=payment.amount,
                match_confidence=0.99,
                match_strategy="exact_amount_match",
                notes=f"Exact match on remaining balance (₹{payment.amount:,.2f})"
            )
            db.add(rec)
            exact_match.settled_amount += payment.amount
            exact_match.remaining_amount = 0.0
            exact_match.status = "settled"
            exact_match.recovery_stage = "recovered"
            
            db.commit()
            GraphService.recalculate_person_ledger(db, person.id)
            return {
                "success": True,
                "reconciled": True,
                "strategy": "exact_amount_match",
                "obligation_title": exact_match.title,
                "matched_amount": payment.amount,
                "confidence": 0.99
            }
            
        # Strategy 2: Oldest Due Date Allocation (FIFO partial match)
        target_ob = open_obs[0]
        matched_amt = min(target_ob.remaining_amount, payment.amount)
        rec = ReconciliationRecord(
            obligation_id=target_ob.id,
            payment_event_id=payment.id,
            matched_amount=matched_amt,
            match_confidence=0.92,
            match_strategy="fifo_partial_allocation",
            notes=f"Partial allocation against oldest obligation '{target_ob.title}'"
        )
        db.add(rec)
        target_ob.settled_amount += matched_amt
        target_ob.remaining_amount -= matched_amt
        if target_ob.remaining_amount <= 0:
            target_ob.status = "settled"
            target_ob.recovery_stage = "recovered"
        else:
            target_ob.status = "partial"
            
        db.commit()
        GraphService.recalculate_person_ledger(db, person.id)
        return {
            "success": True,
            "reconciled": True,
            "strategy": "fifo_partial_allocation",
            "obligation_title": target_ob.title,
            "matched_amount": matched_amt,
            "remaining_obligation": target_ob.remaining_amount,
            "confidence": 0.92
        }

    @staticmethod
    def get_honest_exceptions(db: Session, user_id: str) -> List[Dict[str, Any]]:
        """
        Honest Exceptions: Transparently surface payments and edge-cases that AI could NOT safely auto-resolve.
        """
        exceptions = []
        
        # 1. Payments with no person attached
        unassigned_payments = db.query(PaymentEvent).filter(
            PaymentEvent.user_id == user_id,
            PaymentEvent.person_id == None
        ).all()
        for p in unassigned_payments:
            exceptions.append({
                "id": f"exc_{p.id}",
                "payment_id": p.id,
                "amount": p.amount,
                "utr": p.utr_rrn or "Missing UTR",
                "source": p.source,
                "reason_category": "UNKNOWN_COUNTERPARTY",
                "title": f"Unidentified payer of ₹{p.amount:,.2f}",
                "description": "Payment was received without matching phone, VPA, or known contact profile.",
                "suggested_action": "Assign Person manually or create new contact",
                "date": p.payment_date.strftime("%d %b %Y") if p.payment_date else "N/A"
            })
            
        # 2. Payments without reconciliation where person has multiple open obligations
        all_payments = db.query(PaymentEvent).filter(
            PaymentEvent.user_id == user_id,
            PaymentEvent.person_id != None
        ).all()
        
        for p in all_payments:
            rec_count = db.query(ReconciliationRecord).filter(ReconciliationRecord.payment_event_id == p.id).count()
            if rec_count == 0:
                person = db.query(Person).filter(Person.id == p.person_id).first()
                open_obs = db.query(Obligation).filter(
                    Obligation.person_id == p.person_id,
                    Obligation.status.in_(["pending", "partial", "overdue"])
                ).all()
                if len(open_obs) > 1:
                    exceptions.append({
                        "id": f"exc_multi_{p.id}",
                        "payment_id": p.id,
                        "amount": p.amount,
                        "utr": p.utr_rrn or "N/A",
                        "source": p.source,
                        "reason_category": "MULTIPLE_OBLIGATION_AMBIGUITY",
                        "title": f"Ambiguous obligation match for {person.canonical_name}",
                        "description": f"Received ₹{p.amount:,.2f}, but {person.canonical_name} has {len(open_obs)} active invoices/advances of varying amounts.",
                        "suggested_action": "Select which invoice to credit this payment against",
                        "date": p.payment_date.strftime("%d %b %Y") if p.payment_date else "N/A"
                    })
                    
        return exceptions
