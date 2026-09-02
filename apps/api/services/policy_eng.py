from typing import Dict, Any, Tuple
from apps.api.core.config import settings

class PolicyEngine:
    @staticmethod
    def evaluate_action(
        action_type: str,
        amount: float,
        risk_score: float,
        entity_trust_score: float = 80.0,
        flags: list = None
    ) -> Tuple[bool, str, str]:
        """
        Evaluates whether an action can execute autonomously or requires human authorization.
        Returns: (can_auto_execute: bool, required_approval_level: str, reason: str)
        Levels: 'NONE', 'STANDARD_APPROVAL', 'CRITICAL_SECURITY_CONFIRMATION'
        """
        flags = flags or []
        
        # Rule 1: High Risk or Tamper Signals ALWAYS require critical user authorization
        if risk_score >= settings.HIGH_RISK_THRESHOLD or "NEW_PAYMENT_DESTINATION" in flags or "IMPERSONATION_SUSPECTED" in flags:
            return (
                False,
                "CRITICAL_SECURITY_CONFIRMATION",
                f"Action blocked by policy: Risk score ({risk_score}/100) exceeds safety threshold. Security confirmation required."
            )
            
        # Rule 2: Recovery Reminders
        if action_type == "send_recovery_reminder":
            if amount <= settings.AUTO_REMINDER_MAX_AMOUNT and entity_trust_score >= 70.0 and risk_score < 30.0:
                return (
                    True,
                    "NONE",
                    f"Autonomous policy match: Low-value polite nudge (₹{amount:,.2f}) to trusted relationship."
                )
            else:
                return (
                    False,
                    "STANDARD_APPROVAL",
                    f"Human approval required: Reminder amount ₹{amount:,.2f} exceeds auto-threshold or trust score ({entity_trust_score}) needs review."
                )

        # Rule 3: Reconciliation
        if action_type == "auto_reconcile":
            if risk_score < 20.0:
                return (True, "NONE", "Policy approved: High confidence deterministic reconciliation.")
            else:
                return (False, "STANDARD_APPROVAL", "Policy hold: Low confidence or ambiguous reconciliation candidate.")

        # Default fallback
        return (False, "STANDARD_APPROVAL", "Standard safety guardrail: Human review requested.")
