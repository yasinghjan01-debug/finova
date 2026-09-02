import datetime
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_, desc

from apps.api.models.schema import PaymentEvent, Person, Obligation, ReconciliationRecord, AuditLog
from apps.api.services.ocr_parser import OCRParserService
from apps.api.services.entity_res import EntityResolutionService
from apps.api.services.graph_svc import GraphService
from apps.api.services.audit_svc import AuditChainService

class PaymentMemoryEngine:
    @staticmethod
    def ingest_unstructured_proof(
        db: Session,
        raw_text: str,
        user_id: str,
        proof_image_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Engine 1 Workflow: Raw Proof (Screenshot/SMS/Text) -> OCR Parser -> Entity Resolution -> Payment Memory Object
        """
        parsed = OCRParserService.parse_payment_proof(raw_text)
        
        # Entity Resolution
        matched_person, entity_conf, match_reason = EntityResolutionService.resolve_entity(
            db=db,
            name=parsed.get("sender_name"),
            vpa=parsed.get("sender_vpa"),
            user_id=user_id
        )
        
        # Create Canonical Payment Event
        amount = parsed.get("amount") or 0.0
        utr = parsed.get("utr")
        source = parsed.get("source_app", "screenshot_ocr")
        
        payment_event = PaymentEvent(
            user_id=user_id,
            person_id=matched_person.id if matched_person else None,
            utr_rrn=utr,
            amount=amount,
            currency="INR",
            direction="inbound",
            source=source,
            status="captured",
            raw_proof_text=raw_text,
            proof_image_url=proof_image_url,
            purpose="Payment via proof upload",
            confidence=round((parsed.get("confidence", 0.8) + entity_conf) / 2.0, 3) if matched_person else parsed.get("confidence", 0.7),
            payment_date=datetime.datetime.utcnow()
        )
        db.add(payment_event)
        db.flush()
        
        # Audit Log via Cryptographic Hash Chain
        AuditChainService.record_event(
            db=db,
            user_id=user_id,
            event_type="OCR_PROOF_INGESTED",
            actor="MEMORY_ENGINE",
            details={
                "payment_id": payment_event.id,
                "amount": amount,
                "utr": utr,
                "matched_person": matched_person.canonical_name if matched_person else "Unknown",
                "confidence": payment_event.confidence
            }
        )
        
        # Attempt auto-reconciliation if person was matched
        reconciled_ob = None
        if matched_person and amount > 0:
            open_ob = db.query(Obligation).filter(
                Obligation.person_id == matched_person.id,
                Obligation.status.in_(["pending", "partial", "overdue"])
            ).order_by(Obligation.created_at.asc()).first()
            
            if open_ob:
                match_amt = min(open_ob.remaining_amount, amount)
                rec_record = ReconciliationRecord(
                    obligation_id=open_ob.id,
                    payment_event_id=payment_event.id,
                    matched_amount=match_amt,
                    match_confidence=payment_event.confidence,
                    match_strategy="ocr_entity_auto_match",
                    notes=f"Auto-reconciled against '{open_ob.title}'"
                )
                db.add(rec_record)
                
                open_ob.settled_amount += match_amt
                open_ob.remaining_amount -= match_amt
                if open_ob.remaining_amount <= 0:
                    open_ob.status = "settled"
                    open_ob.recovery_stage = "recovered"
                else:
                    open_ob.status = "partial"
                reconciled_ob = open_ob
                
                # Recalculate Graph Ledger
                GraphService.recalculate_person_ledger(db, matched_person.id)
                
        db.commit()
        db.refresh(payment_event)
        
        return {
            "payment_event_id": payment_event.id,
            "amount": payment_event.amount,
            "utr": payment_event.utr_rrn,
            "sender_name": parsed.get("sender_name"),
            "sender_vpa": parsed.get("sender_vpa"),
            "matched_person_id": matched_person.id if matched_person else None,
            "matched_person_name": matched_person.canonical_name if matched_person else None,
            "entity_confidence": entity_conf,
            "overall_confidence": payment_event.confidence,
            "auto_reconciled": reconciled_ob is not None,
            "reconciled_obligation_id": reconciled_ob.id if reconciled_ob else None,
            "matched_obligation_title": reconciled_ob.title if reconciled_ob else None,
            "proof_summary": f"Identified ₹{amount:,.2f} from {matched_person.canonical_name if matched_person else 'Unknown'} with UTR {utr or 'N/A'}"
        }

    @staticmethod
    def find_my_money(db: Session, query: str, user_id: str, limit: int = 20) -> Dict[str, Any]:
        """
        Hero Feature: 'Find My Money'
        """
        q_clean = query.strip()
        matches = []
        total_amount = 0.0
        
        # Extract potential amount from search query
        amt_match = re.search(r"(?:₹|Rs\.?|INR)?\s*([\d,]+(?:\.\d{2})?)", q_clean)
        target_amount = None
        if amt_match:
            try:
                target_amount = float(amt_match.group(1).replace(",", ""))
            except ValueError:
                pass
                
        keywords = [k.lower() for k in re.findall(r"\b[A-Za-z0-9]+\b", q_clean) if len(k) > 2]
        
        payments = db.query(PaymentEvent).filter(PaymentEvent.user_id == user_id).order_by(desc(PaymentEvent.payment_date)).all()
        
        for p in payments:
            score = 0.0
            reasons = []
            
            # Amount exact match gets a substantial boost
            if target_amount and abs(p.amount - target_amount) < 0.01:
                score += 1.5
                reasons.append(f"Exact amount ₹{p.amount:,.2f}")
            elif target_amount and abs(p.amount - target_amount) / max(1, target_amount) < 0.1:
                score += 0.3
                reasons.append(f"Close amount ₹{p.amount:,.2f}")
                
            # UTR match
            if p.utr_rrn and any(k in p.utr_rrn.lower() for k in keywords):
                score += 0.8
                reasons.append(f"UTR match '{p.utr_rrn}'")
                
            # Person match
            if p.person:
                p_name_lower = p.person.canonical_name.lower()
                if any(k in p_name_lower for k in keywords):
                    score += 0.6
                    reasons.append(f"Person match '{p.person.canonical_name}'")
                    
            # Purpose / Context match
            if p.purpose and any(k in p.purpose.lower() for k in keywords):
                score += 0.3
                reasons.append(f"Purpose match '{p.purpose}'")
                
            if score > 0.3 or not keywords:
                rec = db.query(ReconciliationRecord).filter(ReconciliationRecord.payment_event_id == p.id).first()
                ob_title = rec.obligation.title if rec and rec.obligation else None
                person_name = p.person.canonical_name if p.person else "Unknown Counterparty"
                evidence = " • ".join(reasons) if reasons else f"Payment record from {person_name}"
                
                matches.append({
                    "payment_id": p.id,
                    "amount": p.amount,
                    "utr_rrn": p.utr_rrn,
                    "person_name": person_name,
                    "payment_date": p.payment_date.strftime("%d %b %Y") if p.payment_date else "N/A",
                    "purpose": p.purpose or "General Transfer",
                    "source": p.source,
                    "proof_available": bool(p.raw_proof_text or p.proof_image_url),
                    "status": "Reconciled" if rec else p.status.capitalize(),
                    "confidence": round(min(0.99, max(p.confidence, min(1.0, score / 2.0))), 3),
                    "matched_obligation": ob_title,
                    "evidence_snippet": evidence,
                    "_sort_score": score
                })
                total_amount += p.amount
                
        # Sort primarily by match score
        matches.sort(key=lambda x: x["_sort_score"], reverse=True)
        top_matches = matches[:limit]
        for m in top_matches:
            m.pop("_sort_score", None)
            
        return {
            "query": query,
            "total_matches": len(top_matches),
            "total_amount_matched": total_amount,
            "matches": top_matches
        }
