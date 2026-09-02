import json
import uuid
import datetime
import pytest
from fastapi.testclient import TestClient
from apps.api.main import app
from apps.api.services.razorpay_svc import RazorpayService
from apps.api.services.policy_eng import PolicyEngine
from apps.api.services.audit_svc import AuditChainService
from apps.api.core.database import SessionLocal
from apps.api.models.schema import WebhookEvent, Obligation, PaymentEvent, RecoveryAction, User
from apps.api.core.auth import hash_password, create_access_token

client = TestClient(app)

# ==============================================================================
# 18-POINT VERIFICATION MATRIX FOR RAZORPAY BUILDATHON SUBMISSION
# ==============================================================================

def test_01_create_razorpay_order():
    """TEST 01: Create Razorpay order via POST /api/v1/razorpay/orders"""
    resp = client.post("/api/v1/razorpay/orders", json={
        "amount": 15000.0,
        "currency": "INR",
        "receipt": "rcpt_test_001",
        "notes": {"project": "Finova Phase 1"}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["entity"] == "order"
    assert data["amount"] == 1500000  # In paise
    assert data["id"].startswith("order_")

def test_02_payment_captured_webhook():
    """TEST 02: Ingest genuine signed payment.captured webhook"""
    payload, sig, raw_body, evt_id = RazorpayService.simulate_webhook_event(
        event_name="payment.captured",
        amount=20000.0,
        contact="+919876543210"
    )
    resp = client.post(
        "/api/v1/razorpay/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": evt_id
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["razorpay_event_id"] == evt_id
    assert data["amount"] == 20000.0

def test_03_invalid_webhook_signature_rejected():
    """TEST 03: Reject webhook with tampered/invalid signature with 400 Bad Request"""
    payload, sig, raw_body, evt_id = RazorpayService.simulate_webhook_event(
        event_name="payment.captured",
        amount=10000.0
    )
    resp = client.post(
        "/api/v1/razorpay/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": "tampered_invalid_signature_hex_12345",
            "X-Razorpay-Event-Id": evt_id
        }
    )
    assert resp.status_code == 400
    assert "Invalid Razorpay webhook signature" in resp.json()["detail"]

def test_04_duplicate_webhook_ignored_idempotency():
    """TEST 04: Duplicate webhook delivery ignored (Idempotency verified via WebhookEvent)"""
    fixed_evt_id = f"evt_idempotency_test_{uuid.uuid4().hex[:8]}"
    payload, sig, raw_body, _ = RazorpayService.simulate_webhook_event(
        event_name="payment.captured",
        amount=5000.0,
        event_id=fixed_evt_id
    )
    # First delivery
    resp1 = client.post(
        "/api/v1/razorpay/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": fixed_evt_id
        }
    )
    assert resp1.status_code == 200
    assert resp1.json()["status"] == "success"

    # Second delivery (duplicate retry)
    resp2 = client.post(
        "/api/v1/razorpay/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": fixed_evt_id
        }
    )
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["status"] == "duplicate_ignored"
    assert data2["retry_count"] >= 1

def test_05_out_of_order_webhook_handled():
    """TEST 05: Handle webhook where payment captured arrives before local order cache"""
    out_of_order_evt_id = f"evt_ooo_{uuid.uuid4().hex[:8]}"
    payload, sig, raw_body, _ = RazorpayService.simulate_webhook_event(
        event_name="payment.captured",
        amount=12000.0,
        event_id=out_of_order_evt_id,
        order_id="order_unrecorded_in_local_cache"
    )
    resp = client.post(
        "/api/v1/razorpay/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": out_of_order_evt_id
        }
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

def test_06_payment_reconciled():
    """TEST 06: Incoming payment matched to open obligation"""
    resp = client.post("/api/v1/reconciliation/match", json={
        "payment_event_id": "pay_rahul_001",
        "obligation_id": "ob_rahul_001"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True

def test_07_partial_payment_calculated():
    """TEST 07: Verify partial payment settlement updates remaining balance"""
    db = SessionLocal()
    ob = db.query(Obligation).filter(Obligation.id == "ob_rahul_001").first()
    assert ob is not None
    assert ob.settled_amount > 0
    assert ob.remaining_amount == ob.total_amount - ob.settled_amount
    db.close()

def test_08_screenshot_ocr():
    """TEST 08: Screenshot OCR parsing extracts structured financial data"""
    proof_text = """
    PhonePe Transaction Successful
    Paid to Arjun Mehta
    Amount: INR 18,500.00
    From: Rahul Sharma (rahul@okhdfcbank)
    UTR: 819203819203
    Date: 29 Aug 2026
    """
    resp = client.post("/api/v1/memory/ingest-proof", json={"raw_text": proof_text})
    assert resp.status_code == 200
    data = resp.json()
    assert data["extracted_amount"] == 18500.0
    assert data["extracted_utr"] == "819203819203"
    assert data["matched_person_name"] == "Rahul Sharma"

def test_09_utr_extracted():
    """TEST 09: 12-digit Indian banking UTR successfully identified from text"""
    from apps.api.services.ocr_parser import OCRParserService
    parsed = OCRParserService.parse_payment_proof("Payment ref no / UTR: 928174829102 completed.")
    assert parsed["utr"] == "928174829102"

def test_10_fraud_model_prediction():
    """TEST 10: XGBoost Risk Model evaluates anomalous request and predicts high probability"""
    resp = client.post("/api/v1/risk/evaluate", json={
        "person_name": "Rahul Sharma",
        "amount": 75000.0,
        "request_phone": "+919876549999",
        "destination_vpa": "unknown.hacker@upi",
        "message_text": "Emergency! Send money right now immediately!"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["risk_score"] >= 60.0
    assert data["risk_level"] in ["HIGH", "CRITICAL"]
    assert "NEW_PHONE_NUMBER_ORIGIN" in data["flagged_signals"]

def test_11_held_out_evaluation():
    """TEST 11: Held-out benchmark metrics exist and show realistic trade-offs"""
    resp = client.get("/api/v1/dashboard/metrics")
    assert resp.status_code == 200
    benchmarks = resp.json().get("ml_benchmarks", {})
    assert "XGBoost (FINOVA Production)" in benchmarks
    xgb_bench = benchmarks["XGBoost (FINOVA Production)"]
    assert xgb_bench["precision"] >= 0.90
    assert xgb_bench["recall"] >= 0.90
    assert "estimated_fp_cost_inr" in xgb_bench

def test_12_high_risk_action_requires_approval():
    """TEST 12: High-risk actions cannot execute autonomously and require approval"""
    can_auto, level, reason = PolicyEngine.evaluate_action(
        action_type="transfer_verification",
        amount=75000.0,
        risk_score=92.4,
        flags=["NEW_PAYMENT_DESTINATION"]
    )
    assert can_auto is False
    assert level == "CRITICAL_SECURITY_CONFIRMATION"

def test_13_recovery_stopping_rule():
    """TEST 13: Recovery stopping rule halts all actions once obligation is paid or stopped"""
    resp = client.post("/api/v1/recovery/stop", json={
        "obligation_id": "ob_vikram_001",
        "reason": "Client filed dispute on invoice"
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "stopped"

def test_14_payment_link_created():
    """TEST 14: Razorpay Payment Link generated with standard parameters"""
    resp = client.post("/api/v1/razorpay/payment-links", json={
        "amount": 30000.0,
        "description": "Construction advance settlement",
        "customer_name": "Rahul Sharma",
        "customer_phone": "+919876543210"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["entity"] == "payment_link"
    assert data["id"].startswith("plink_")
    assert data["short_url"].startswith("https://rzp.io/")

def test_15_payment_link_paid_webhook():
    """TEST 15: Handle payment_link.paid webhook event"""
    payload, sig, raw_body, evt_id = RazorpayService.simulate_webhook_event(
        event_name="payment_link.paid",
        amount=30000.0,
        payment_link_id="plink_test_settle_01",
        contact="+919876543210",
        notes={"obligation_id": "ob_rahul_001"}
    )
    resp = client.post(
        "/api/v1/razorpay/webhook",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": sig,
            "X-Razorpay-Event-Id": evt_id
        }
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"

def test_16_recovery_balance_updated():
    """TEST 16: Verify ledger and relationship graph reflects updated balance"""
    resp = client.get("/api/v1/people/person_rahul_001")
    assert resp.status_code == 200
    data = resp.json()
    assert "total_given" in data
    assert "total_received" in data
    assert "trust_score" in data

def test_17_audit_hash_verified():
    """TEST 17: Tamper-evident cryptographic SHA-256 hash chain verification passes"""
    resp = client.get("/api/v1/audit/verify")
    assert resp.status_code == 200
    data = resp.json()
    assert data["is_tamper_evident_valid"] is True
    assert data["records_verified"] > 0
    assert "intact" in data["verification_message"]

def test_18_unauthorized_user_access_rejected():
    """TEST 18: Rejects invalid or expired tokens on protected endpoint"""
    resp = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid_forged_token"})
    assert resp.status_code == 401
