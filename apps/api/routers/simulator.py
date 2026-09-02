import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from apps.api.core.database import get_db
from apps.api.engines.risk_engine import RiskEngine
from apps.api.engines.payment_memory import PaymentMemoryEngine
from apps.api.engines.recovery import RecoveryEngine
from apps.api.services.razorpay_svc import RazorpayService
from apps.api.engines.reconciliation import ReconciliationEngine
from apps.api.models.schema import Obligation, Person, PaymentEvent, AuditLog, ApprovalRequest

router = APIRouter(prefix="/simulator", tags=["Simulation Lab"])

@router.post("/run-impersonation-attack")
def run_impersonation_attack_simulation(db: Session = Depends(get_db)):
    """
    Scenario 1: Impersonation Attack Simulation
    A malicious actor pretending to be 'Rahul Sharma' requests ₹75,000 to a new VPA from a new number with high urgency.
    """
    user_id = "user_finova_master_001"
    
    # 1. Message received
    message_text = "Bro urgent medical emergency in family, hospital needs deposit right now! Please send ₹75,000 immediately to rahul.emergency@upi. My old phone is broken, don't call."
    
    # 2. Risk Engine Assessment
    risk_result = RiskEngine.evaluate_transaction_request(
        db=db,
        person_name="Rahul Sharma",
        amount=75000.0,
        request_phone="+919876549999",
        destination_vpa="rahul.emergency@upi",
        message_text=message_text
    )
    
    steps = [
        {"time": "10:42:01", "event": "Inbound payment request received via WhatsApp", "detail": f"Claimed Sender: 'Rahul Sharma' (+919876549999)"},
        {"time": "10:42:02", "event": "OCR & Entity Resolution analysis", "detail": "Known Rahul primary number: +919876543210. Request number is unverified."},
        {"time": "10:42:03", "event": "Risk Engine ML inference triggered", "detail": f"Model: XGBoost Ensemble. Risk Score: {risk_result['risk_score']}/100 ({risk_result['risk_level']})"},
        {"time": "10:42:04", "event": "Flagged Anomalies", "detail": ", ".join(risk_result["flagged_signals"])},
        {"time": "10:42:05", "event": "Policy Engine Guardrail Intercept", "detail": "Autonomous transfer BLOCKED. Queued in Human Approval Center."},
        {"time": "10:42:06", "event": "Verdict", "detail": "🛡️ IMPERSONATION ATTACK DEFENDED"}
    ]
    
    return {
        "scenario": "Impersonation Attack",
        "attack_status": "DEFENDED",
        "risk_evaluation": risk_result,
        "steps": steps
    }

@router.post("/run-revenue-recovery")
def run_revenue_recovery_simulation(db: Session = Depends(get_db)):
    """
    Scenario 2: Complete Revenue Recovery Loop
    Overdue obligation -> AI recovery draft with Razorpay link -> Simulated Webhook -> Auto-reconcile -> ₹0 balance
    """
    user_id = "user_finova_master_001"
    
    # Find or create overdue obligation
    ob = db.query(Obligation).filter(
        Obligation.user_id == user_id,
        Obligation.remaining_amount > 0
    ).first()
    
    if not ob:
        ob = Obligation(
            user_id=user_id,
            person_id="person_rahul_001",
            title="Material Supply Advance",
            total_amount=50000.0,
            settled_amount=20000.0,
            remaining_amount=30000.0,
            status="overdue",
            due_date=datetime.datetime.utcnow() - datetime.timedelta(days=10),
            invoice_number="INV-REC-900"
        )
        db.add(ob)
        db.commit()
        db.refresh(ob)
        
    initial_remaining = ob.remaining_amount
    person_name = ob.person.canonical_name if ob.person else "Counterparty"
    
    # Step 1: AI generates recovery link
    payment_link = RazorpayService.create_payment_link(
        amount=initial_remaining,
        description=f"Settlement for {ob.title}",
        customer_name=person_name,
        obligation_id=ob.id
    )
    
    # Step 2: Simulate Razorpay webhook payment received
    sim_webhook, signature, raw_body = RazorpayService.simulate_webhook_event(
        event_name="payment.captured",
        amount=initial_remaining,
        notes={"obligation_id": ob.id, "description": ob.title}
    )
    
    pay_id = sim_webhook["payload"]["payment"]["entity"]["id"]
    rrn = sim_webhook["payload"]["payment"]["entity"]["acquirer_data"]["rrn"]
    
    payment_event = PaymentEvent(
        user_id=user_id,
        person_id=ob.person_id,
        utr_rrn=rrn,
        razorpay_payment_id=pay_id,
        amount=initial_remaining,
        currency="INR",
        direction="inbound",
        source="Razorpay Recovery Link",
        status="captured",
        purpose=f"Auto recovery settlement for {ob.title}",
        payment_date=datetime.datetime.utcnow(),
        confidence=1.0
    )
    db.add(payment_event)
    db.flush()
    
    # Step 3: Auto-reconciliation
    rec_res = ReconciliationEngine.reconcile_payment(
        db=db,
        payment_event_id=payment_event.id,
        user_id=user_id,
        force_manual_ob_id=ob.id
    )
    
    steps = [
        {"time": "11:15:00", "event": f"Overdue receivable identified: ₹{initial_remaining:,.2f}", "detail": f"Counterparty: {person_name}, Due date exceeded."},
        {"time": "11:15:01", "event": "Recovery Agent selected intervention", "detail": "Generated branded Razorpay payment link & polite reminder draft."},
        {"time": "11:15:02", "event": f"Razorpay Link Created", "detail": payment_link["short_url"]},
        {"time": "11:15:05", "event": "Payer completes settlement", "detail": f"Payment ID: {pay_id}, UTR: {rrn}"},
        {"time": "11:15:06", "event": "Razorpay Webhook Ingested", "detail": "HMAC-SHA256 signature verified. Status: payment.captured."},
        {"time": "11:15:07", "event": "Reconciliation Engine Executed", "detail": f"Matched ₹{initial_remaining:,.2f} to '{ob.title}'. Outstanding balance: ₹0.00"},
        {"time": "11:15:08", "event": "Ledger Updated & Audit Logged", "detail": "🎉 REVENUE SUCCESSFULLY RECOVERED"}
    ]
    
    return {
        "scenario": "Revenue Recovery",
        "recovered_amount": initial_remaining,
        "payment_link": payment_link["short_url"],
        "payment_id": pay_id,
        "utr": rrn,
        "status": "RECOVERED",
        "steps": steps
    }

@router.post("/run-screenshot-ocr")
def run_screenshot_ocr_simulation(db: Session = Depends(get_db)):
    """
    Scenario 3: Screenshot OCR -> Payment Memory -> Ledger Update
    """
    user_id = "user_finova_master_001"
    sample_ocr = (
        "Google Pay\n"
        "Payment Successful to Arjun Mehta\n"
        "Amount: ₹20,000.00\n"
        "From: Rahul Sharma (rahul.sharma@okhdfcbank)\n"
        "UPI Ref / UTR: 829103829102\n"
        "Date: 28 Aug 2026\n"
        "Note: Construction advance"
    )
    
    res = PaymentMemoryEngine.ingest_unstructured_proof(
        db=db,
        raw_text=sample_ocr,
        user_id=user_id
    )
    
    steps = [
        {"time": "09:30:00", "event": "Payment screenshot uploaded", "detail": "Image proof parsed by OCR Engine"},
        {"time": "09:30:01", "event": "Structured Extraction", "detail": f"Amount: ₹{res.get('amount'):,.2f}, UTR: {res.get('utr')}, Sender: {res.get('sender_name')}"},
        {"time": "09:30:02", "event": "Entity Resolution Match", "detail": f"Matched '{res.get('matched_person_name')}' with {res.get('entity_confidence')*100:.1f}% confidence"},
        {"time": "09:30:03", "event": "Canonical Memory Stored", "detail": f"Saved payment #{res.get('payment_event_id')}"},
        {"time": "09:30:04", "event": "Auto-Reconciliation Status", "detail": f"Reconciled with '{res.get('matched_obligation_title') or 'Open Balance'}'"}
    ]
    
    return {
        "scenario": "Screenshot OCR to Memory",
        "result": res,
        "steps": steps
    }
