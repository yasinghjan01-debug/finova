import re
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy import desc

from apps.api.models.schema import Person, Obligation, PaymentEvent
from apps.api.services.entity_res import EntityResolutionService
from apps.api.services.graph_svc import GraphService
from apps.api.engines.payment_memory import PaymentMemoryEngine
from apps.api.engines.recovery import RecoveryEngine

class EvidenceBackedAssistant:
    @staticmethod
    def answer_query(db: Session, query: str, user_id: str) -> Dict[str, Any]:
        """
        Evidence-Backed Financial AI Assistant:
        Extracts intent, queries relational and graph stores, constructs exact answer, and attaches verified evidence.
        """
        q_lower = query.lower()
        evidence_items = []
        action_suggested = None
        
        # 1. Intent: "At risk" / "Overdue" / "Recovery"
        if any(k in q_lower for k in ["at risk", "overdue", "delayed", "recover", "pending money", "who owes"]):
            at_risk = RecoveryEngine.evaluate_receivables_at_risk(db=db, user_id=user_id)
            total_at_risk = sum(item["remaining_amount"] for item in at_risk)
            
            for item in at_risk:
                evidence_items.append({
                    "title": f"Obligation: {item['title']} ({item['person_name']})",
                    "date": item["due_date"],
                    "amount": item["remaining_amount"],
                    "utr": None,
                    "type": "RECEIVABLE_AT_RISK"
                })
                
            answer = (
                f"You currently have **₹{total_at_risk:,.2f}** across {len(at_risk)} open receivables at risk or awaiting payment.\n\n"
                f"Top outstanding: " + ", ".join([f"{item['person_name']} (₹{item['remaining_amount']:,.2f})" for item in at_risk[:3]]) + "."
            )
            action_suggested = "Review Recovery Queue to dispatch Razorpay payment links"
            return {"answer": answer, "evidence": evidence_items, "action_suggested": action_suggested}

        # 2. Intent: Specific Person balance / payments (e.g. "How much money does Rahul owe me?")
        # Find person mentioned in query
        all_people = db.query(Person).filter(Person.user_id == user_id).all()
        target_person = None
        for p in all_people:
            first_name = p.canonical_name.split()[0].lower()
            if first_name in q_lower or p.canonical_name.lower() in q_lower:
                target_person = p
                break
                
        if target_person:
            GraphService.recalculate_person_ledger(db, target_person.id)
            obs = db.query(Obligation).filter(Obligation.person_id == target_person.id).all()
            payments = db.query(PaymentEvent).filter(PaymentEvent.person_id == target_person.id).order_by(desc(PaymentEvent.payment_date)).all()
            
            for ob in obs:
                evidence_items.append({
                    "title": f"Obligation: {ob.title}",
                    "date": ob.created_at.strftime("%d %b %Y"),
                    "amount": ob.total_amount,
                    "utr": None,
                    "type": f"OBLIGATION_{ob.status.upper()}"
                })
            for p in payments:
                evidence_items.append({
                    "title": f"Payment: {p.source} - {p.purpose or 'Transfer'}",
                    "date": p.payment_date.strftime("%d %b %Y") if p.payment_date else "N/A",
                    "amount": p.amount,
                    "utr": p.utr_rrn,
                    "type": "PAYMENT_RECEIVED"
                })
                
            if "how much" in q_lower or "owe" in q_lower or "balance" in q_lower:
                answer = (
                    f"**{target_person.canonical_name}** currently has an outstanding balance of **₹{target_person.outstanding_balance:,.2f}**.\n\n"
                    f"• Total Given: ₹{target_person.total_given:,.2f}\n"
                    f"• Total Received: ₹{target_person.total_received:,.2f}\n"
                    f"• Payment Reliability: {target_person.payment_reliability}% (Avg delay: {target_person.avg_delay_days} days)"
                )
            else:
                answer = (
                    f"Found **{len(payments)} payments** (total ₹{target_person.total_received:,.2f}) and **{len(obs)} obligations** for **{target_person.canonical_name}**.\n"
                    f"Current net outstanding is **₹{target_person.outstanding_balance:,.2f}**."
                )
            return {"answer": answer, "evidence": evidence_items, "action_suggested": "View Relationship Profile"}

        # 3. Fallback: Search Payment Memory via Find My Money
        search_res = PaymentMemoryEngine.find_my_money(db=db, query=query, user_id=user_id)
        if search_res["matches"]:
            for m in search_res["matches"]:
                evidence_items.append({
                    "title": f"{m['person_name']} - {m['purpose']}",
                    "date": m["payment_date"],
                    "amount": m["amount"],
                    "utr": m["utr_rrn"],
                    "type": "PAYMENT_MATCH"
                })
            top = search_res["matches"][0]
            answer = (
                f"Found **{search_res['total_matches']} matching transactions** totaling **₹{search_res['total_amount_matched']:,.2f}**.\n\n"
                f"Top Match: **₹{top['amount']:,.2f}** from **{top['person_name']}** on {top['payment_date']} (UTR: `{top['utr_rrn'] or 'N/A'}`). "
                f"Status: {top['status']} ({int(top['confidence']*100)}% confidence)."
            )
        else:
            answer = "I searched your Financial Memory but couldn't find matching transactions or obligations for that query. You can search by person name, amount (e.g. ₹20,000), or 12-digit UTR."

        return {"answer": answer, "evidence": evidence_items, "action_suggested": None}
