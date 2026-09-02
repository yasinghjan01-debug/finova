import json
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.services.razorpay_svc import RazorpayService
from apps.api.services.policy_eng import PolicyEngine

client = TestClient(app)

def test_policy_engine_rules():
    # Rule 1: High risk -> must require approval
    can_auto, level, reason = PolicyEngine.evaluate_action(
        action_type="transfer_verification",
        amount=75000.0,
        risk_score=92.0,
        flags=["NEW_PAYMENT_DESTINATION"]
    )
    assert can_auto is False
    assert level == "CRITICAL_SECURITY_CONFIRMATION"

    # Rule 2: Low-value gentle reminder -> allowed
    can_auto_low, level_low, reason_low = PolicyEngine.evaluate_action(
        action_type="send_recovery_reminder",
        amount=15000.0,
        risk_score=10.0,
        entity_trust_score=85.0
    )
    assert can_auto_low is True
    assert level_low == "NONE"

def test_simulated_razorpay_webhook():
    response = client.post(
        "/api/v1/razorpay/simulate-webhook",
        params={"amount": 10000.0, "phone": "+919876543210"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "simulated_payment_id" in data
    assert data["amount"] == 10000.0

def test_simulation_lab_impersonation_scenario():
    response = client.post("/api/v1/simulator/run-impersonation-attack")
    assert response.status_code == 200
    data = response.json()
    assert data["attack_status"] == "DEFENDED"
    assert data["risk_evaluation"]["risk_score"] >= 60.0
    assert len(data["steps"]) >= 5
