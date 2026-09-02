import os
import re
import joblib
import numpy as np
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from apps.api.models.schema import Person, Identity, RiskEvent, AuditLog, ApprovalRequest
from apps.api.services.policy_eng import PolicyEngine
from apps.api.services.entity_res import EntityResolutionService

ARTIFACTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "ml", "artifacts")
MODEL_PATH = os.path.join(ARTIFACTS_DIR, "risk_model.joblib")

class RiskEngine:
    _model_cache = None

    @classmethod
    def get_model(cls):
        if cls._model_cache is None and os.path.exists(MODEL_PATH):
            cls._model_cache = joblib.load(MODEL_PATH)
        return cls._model_cache

    @staticmethod
    def extract_urgency_score(message_text: Optional[str]) -> float:
        if not message_text:
            return 0.15
        text = message_text.lower()
        urgency_terms = [
            "urgent", "immediately", "right now", "emergency", "fast", "asap",
            "hospital", "account blocked", "send now", "do not call", "phone broken",
            "please hurry", "life or death", "last warning"
        ]
        hits = sum(1 for term in urgency_terms if term in text)
        score = min(1.0, 0.15 + (hits * 0.25))
        return round(score, 3)

    @classmethod
    def evaluate_transaction_request(
        cls,
        db: Session,
        person_name: str,
        amount: float,
        request_phone: Optional[str] = None,
        destination_vpa: Optional[str] = None,
        message_text: Optional[str] = None,
        claimed_person_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Engine 4: Full ML + Heuristic Risk & Impersonation Assessment
        """
        flagged_signals = []
        person = None
        if claimed_person_id:
            person = db.query(Person).filter(Person.id == claimed_person_id).first()
        if not person:
            person, _, _ = EntityResolutionService.resolve_entity(db=db, name=person_name)

        hist_avg = 10000.0
        rel_age_days = 0
        past_txns = 0
        is_new_recipient = 1
        is_new_vpa = 1
        is_new_phone = 1
        
        if person:
            is_new_recipient = 0
            rel_age_days = max(1, int((person.updated_at - person.created_at).days) + 30)
            past_txns = max(1, len(person.payment_events))
            if person.total_given > 0:
                hist_avg = person.total_given / max(1, past_txns)
                
            # Check known phone identities
            if request_phone:
                verified_phone = any(
                    i.identity_value == request_phone for i in person.identities if i.identity_type == "phone"
                ) or (person.primary_phone == request_phone)
                is_new_phone = 0 if verified_phone else 1
                if is_new_phone:
                    flagged_signals.append("NEW_PHONE_NUMBER_ORIGIN")
            else:
                is_new_phone = 0
                
            # Check known VPA identities
            if destination_vpa:
                verified_vpa = any(
                    i.identity_value.lower() == destination_vpa.lower() for i in person.identities if i.identity_type == "upi_vpa"
                ) or (person.primary_vpa and person.primary_vpa.lower() == destination_vpa.lower())
                is_new_vpa = 0 if verified_vpa else 1
                if is_new_vpa:
                    flagged_signals.append("NEW_PAYMENT_DESTINATION_VPA")
            else:
                is_new_vpa = 0
        else:
            flagged_signals.append("UNKNOWN_BENEFICIARY")

        amount_multiplier = round(amount / max(1.0, hist_avg), 2)
        if amount_multiplier >= 3.0:
            flagged_signals.append(f"UNUSUAL_AMOUNT_{amount_multiplier}X_BASELINE")

        urgency_score = cls.extract_urgency_score(message_text)
        if urgency_score >= 0.65:
            flagged_signals.append("COERCIVE_URGENCY_LANGUAGE")

        # Feature vector
        feature_vector = np.array([[
            amount,
            hist_avg,
            amount_multiplier,
            is_new_recipient,
            is_new_vpa,
            is_new_phone,
            rel_age_days,
            past_txns,
            urgency_score,
            14,  # default hour
            1    # default velocity
        ]])

        model_artifact = cls.get_model()
        ml_prob = 0.15
        if model_artifact:
            model = model_artifact["model"]
            ml_prob = float(model.predict_proba(feature_vector)[0, 1])
        else:
            # Fallback heuristic calculation if model not yet loaded
            heuristic_risk = (is_new_phone * 35) + (is_new_vpa * 30) + (min(50, amount_multiplier * 8)) + (urgency_score * 25)
            ml_prob = min(0.99, heuristic_risk / 100.0)

        risk_score = round(ml_prob * 100.0, 1)
        if risk_score >= 80.0:
            risk_level = "CRITICAL"
        elif risk_score >= 60.0:
            risk_level = "HIGH"
        elif risk_score >= 35.0:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        # Construct explanation
        explanation_parts = []
        if is_new_phone and person:
            explanation_parts.append(f"Request arrived from an unverified phone number for contact '{person.canonical_name}'.")
        if is_new_vpa:
            explanation_parts.append(f"Destination VPA '{destination_vpa or 'Unknown'}' is not linked to known account history.")
        if amount_multiplier >= 3.0:
            explanation_parts.append(f"Requested amount (₹{amount:,.2f}) is {amount_multiplier}x higher than typical transaction volume.")
        if urgency_score >= 0.65:
            explanation_parts.append("Communication exhibits high emotional urgency and pressure tactics.")
        
        explanation = " ".join(explanation_parts) if explanation_parts else "Transaction fits within typical historical parameters and verified channels."

        # Policy Engine Evaluation
        can_auto, approval_level, policy_reason = PolicyEngine.evaluate_action(
            action_type="transfer_verification",
            amount=amount,
            risk_score=risk_score,
            entity_trust_score=person.trust_score if person else 50.0,
            flags=flagged_signals
        )

        requires_approval = not can_auto
        approval_id = None

        if requires_approval:
            rec_text = "BLOCK & VERIFY: Do not transfer funds. Contact recipient via their verified primary phone before proceeding."
            # Create Approval Request record
            approval = ApprovalRequest(
                action_type="block_suspicious_transfer",
                title=f"⚠️ {risk_level} Risk: ₹{amount:,.2f} request from {person.canonical_name if person else person_name}",
                description=explanation,
                severity=risk_level,
                target_entity_name=person.canonical_name if person else person_name,
                amount=amount,
                payload={
                    "risk_score": risk_score,
                    "flagged_signals": flagged_signals,
                    "destination_vpa": destination_vpa,
                    "request_phone": request_phone
                }
            )
            db.add(approval)
            db.commit()
            approval_id = approval.id
        else:
            rec_text = "PROCEED: Transaction parameters are consistent with verified payment history."

        # Record Risk Event
        risk_event = RiskEvent(
            person_id=person.id if person else None,
            risk_score=risk_score,
            risk_level=risk_level,
            ml_probability=round(ml_prob, 4),
            flagged_signals=flagged_signals,
            reason_explanation=explanation,
            status="pending_review" if requires_approval else "cleared"
        )
        db.add(risk_event)
        db.commit()

        return {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "ml_probability": round(ml_prob, 4),
            "flagged_signals": flagged_signals,
            "explanation": explanation,
            "recommendation": rec_text,
            "requires_approval": requires_approval,
            "approval_request_id": approval_id
        }
