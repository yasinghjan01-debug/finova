import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc

from apps.api.models.schema import Obligation, Person, ApprovalRequest, RecoveryAction
from apps.api.services.razorpay_svc import RazorpayService
from apps.api.services.policy_eng import PolicyEngine
from apps.api.services.audit_svc import AuditChainService

class RecoveryEngine:
    @staticmethod
    def evaluate_receivables_at_risk(db: Session, user_id: str) -> List[Dict[str, Any]]:
        """
        Engine 5: Evaluates receivables at risk and checks stopping rules
        """
        now = datetime.datetime.utcnow()
        open_obs = db.query(Obligation).filter(
            Obligation.user_id == user_id,
            Obligation.obligation_type.in_(["receivable", "invoice", "advance", "loan", "emi"]),
            Obligation.status.in_(["pending", "partial", "overdue"])
        ).order_by(desc(Obligation.remaining_amount)).all()
        
        results = []
        for ob in open_obs:
            # Check stopping rules
            if ob.recovery_stage == "stopped" or ob.status == "settled" or ob.remaining_amount <= 0:
                continue

            person = ob.person
            days_overdue = 0
            if ob.due_date and ob.due_date < now:
                days_overdue = (now - ob.due_date).days
                if ob.status != "overdue":
                    ob.status = "overdue"
                    db.commit()

            # Count previous attempts
            past_actions_count = db.query(RecoveryAction).filter(RecoveryAction.obligation_id == ob.id).count()
            
            # Stopping rule: If max attempts reached, stop automated nudges and escalate
            if past_actions_count >= 3:
                intervention = "MANUAL_LEGAL_ESCALATION"
                urgency = "CRITICAL"
                suggested_msg = f"Dear {person.canonical_name}, multiple recovery notices for Invoice #{ob.invoice_number or ob.title} (INR {ob.remaining_amount:,.2f}) have remained unanswered. Please contact finance administration immediately."
            elif days_overdue >= 14:
                intervention = "ESCALATED_RECOVERY_NOTICE"
                urgency = "HIGH"
                suggested_msg = f"Dear {person.canonical_name}, Invoice #{ob.invoice_number or ob.title} for INR {ob.remaining_amount:,.2f} is overdue by {days_overdue} days. Please settle immediately via the attached link to avoid service suspension."
            elif days_overdue >= 1:
                intervention = "FORMAL_PAYMENT_LINK"
                urgency = "MEDIUM"
                suggested_msg = f"Hi {person.canonical_name}, friendly reminder that payment for '{ob.title}' (INR {ob.remaining_amount:,.2f}) was due on {ob.due_date.strftime('%d %b')}. Click here to pay securely via UPI/Card."
            else:
                intervention = "GENTLE_DUE_NUDGE"
                urgency = "LOW"
                suggested_msg = f"Hi {person.canonical_name}, just a quick heads up regarding '{ob.title}' of INR {ob.remaining_amount:,.2f} due soon."
                
            results.append({
                "obligation_id": ob.id,
                "person_id": person.id if person else None,
                "person_name": person.canonical_name if person else "Unknown",
                "person_phone": person.primary_phone if person else None,
                "trust_score": person.trust_score if person else 50.0,
                "title": ob.title,
                "total_amount": ob.total_amount,
                "settled_amount": ob.settled_amount,
                "remaining_amount": ob.remaining_amount,
                "due_date": ob.due_date.strftime("%d %b %Y") if ob.due_date else "No due date",
                "days_overdue": days_overdue,
                "status": ob.status,
                "suggested_intervention": intervention,
                "urgency": urgency,
                "draft_message": suggested_msg,
                "recovery_stage": ob.recovery_stage,
                "past_actions_count": past_actions_count
            })
        return results

    @staticmethod
    def prepare_and_dispatch_recovery(
        db: Session,
        obligation_id: str,
        user_id: str,
        custom_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes bounded recovery workflow with Policy check & persisted RecoveryAction
        """
        ob = db.query(Obligation).filter(Obligation.id == obligation_id).first()
        if not ob:
            return {"success": False, "reason": "Obligation not found"}

        # Stopping rule check
        if ob.recovery_stage == "stopped":
            return {"success": False, "reason": f"Recovery stopped on this obligation. Reason: {ob.stop_reason or 'User stopped'}"}
            
        if ob.status == "settled" or ob.remaining_amount <= 0:
            return {"success": False, "reason": "Obligation already settled. Automated recovery stopping rule active."}

        person = ob.person
        person_name = person.canonical_name if person else "Counterparty"
        
        # 1. Generate Razorpay Payment Link
        payment_link = RazorpayService.create_payment_link(
            amount=ob.remaining_amount,
            description=f"Payment for {ob.title}",
            customer_name=person_name,
            customer_phone=person.primary_phone if person else None,
            obligation_id=ob.id
        )
        
        ob.razorpay_payment_link_id = payment_link["id"]
        
        message_body = (
            custom_message or 
            f"Hi {person_name}, please use this secure Razorpay link to pay INR {ob.remaining_amount:,.2f} for '{ob.title}': {payment_link['short_url']}"
        )
        
        # 2. Check Policy Engine
        can_auto, approval_level, policy_reason = PolicyEngine.evaluate_action(
            action_type="send_recovery_reminder",
            amount=ob.remaining_amount,
            risk_score=15.0 if person and person.trust_score >= 70 else 45.0,
            entity_trust_score=person.trust_score if person else 50.0
        )
        
        if can_auto:
            ob.recovery_stage = "scheduled_nudge"
            
            action_rec = RecoveryAction(
                user_id=user_id,
                obligation_id=ob.id,
                action_type="payment_link",
                stage="day_7_link",
                channel="whatsapp",
                message=message_body,
                razorpay_payment_link_id=payment_link["id"],
                status="executed",
                approved_by="policy"
            )
            db.add(action_rec)
            
            AuditChainService.record_event(
                db=db,
                user_id=user_id,
                event_type="RECOVERY_REMINDER_SENT_AUTONOMOUS",
                actor="RECOVERY_ENGINE",
                details={
                    "obligation_id": ob.id,
                    "person": person_name,
                    "amount": ob.remaining_amount,
                    "payment_link": payment_link["short_url"]
                }
            )
            db.commit()
            return {
                "success": True,
                "auto_dispatched": True,
                "message": "Payment reminder dispatched autonomously via policy approval.",
                "payment_link": payment_link["short_url"],
                "draft_message": message_body
            }
        else:
            # Queue in Approval Center
            approval = ApprovalRequest(
                user_id=user_id,
                action_type="send_recovery_reminder",
                title=f"Send payment reminder to {person_name} (₹{ob.remaining_amount:,.2f})",
                description=f"AI prepared recovery message with payment link {payment_link['short_url']}. Policy requires human sign-off due to amount threshold or trust score.",
                severity="MEDIUM" if ob.remaining_amount < 100000 else "HIGH",
                target_entity_name=person_name,
                amount=ob.remaining_amount,
                payload={
                    "obligation_id": ob.id,
                    "payment_link_id": payment_link["id"],
                    "short_url": payment_link["short_url"],
                    "draft_message": message_body
                }
            )
            db.add(approval)
            db.commit()
            return {
                "success": True,
                "auto_dispatched": False,
                "message": "Recovery action queued in AI Approval Center for user sign-off.",
                "approval_id": approval.id,
                "payment_link": payment_link["short_url"],
                "draft_message": message_body
            }

    @staticmethod
    def stop_recovery(db: Session, obligation_id: str, reason: str, user_id: str) -> Dict[str, Any]:
        """
        Stopping rule: Explicitly halt all recovery actions on an obligation
        """
        ob = db.query(Obligation).filter(Obligation.id == obligation_id).first()
        if not ob:
            return {"success": False, "reason": "Obligation not found"}
            
        ob.recovery_stage = "stopped"
        ob.stop_reason = reason
        
        action_rec = RecoveryAction(
            user_id=user_id,
            obligation_id=ob.id,
            action_type="stop_action",
            stage="stopped",
            channel="system",
            message=f"Recovery stopped. Reason: {reason}",
            status="stopped",
            approved_by="user"
        )
        db.add(action_rec)
        
        AuditChainService.record_event(
            db=db,
            user_id=user_id,
            event_type="RECOVERY_WORKFLOW_STOPPED",
            actor="USER",
            details={"obligation_id": obligation_id, "reason": reason}
        )
        db.commit()
        return {
            "success": True,
            "obligation_id": obligation_id,
            "status": "stopped",
            "stop_reason": reason,
            "message": f"All recovery workflows halted for '{ob.title}'."
        }
