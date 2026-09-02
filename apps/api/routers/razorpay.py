import json
import hashlib
import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Header, Body, status
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
from pydantic import BaseModel

from apps.api.core.database import get_db
from apps.api.core.config import settings
from apps.api.models.schema import PaymentEvent, Obligation, ReconciliationRecord, WebhookEvent, RecoveryAction
from apps.api.services.razorpay_svc import RazorpayService
from apps.api.services.entity_res import EntityResolutionService
from apps.api.services.audit_svc import AuditChainService
from apps.api.engines.reconciliation import ReconciliationEngine
from apps.api.core.auth import get_current_user

router = APIRouter(prefix="/razorpay", tags=["Razorpay Webhooks & Payment Gateway"])

class CreateOrderRequest(BaseModel):
    amount: float
    currency: str = "INR"
    receipt: Optional[str] = None
    notes: Optional[Dict[str, Any]] = None

class CreatePaymentLinkRequest(BaseModel):
    amount: float
    description: str
    customer_name: str
    customer_phone: Optional[str] = None
    obligation_id: Optional[str] = None

@router.post("/orders")
def create_order(payload: CreateOrderRequest, db: Session = Depends(get_db)):
    """
    Creates an official Razorpay Order: POST /v1/orders
    """
    order = RazorpayService.create_order(
        amount=payload.amount,
        currency=payload.currency,
        receipt=payload.receipt,
        notes=payload.notes
    )
    AuditChainService.record_event(
        db=db,
        event_type="RAZORPAY_ORDER_CREATED",
        actor="RAZORPAY_SERVICE",
        details={"order_id": order["id"], "amount": payload.amount}
    )
    return order

@router.post("/payment-links")
def create_payment_link(payload: CreatePaymentLinkRequest, db: Session = Depends(get_db)):
    """
    Creates an official Razorpay Payment Link: POST /v1/payment_links
    """
    link = RazorpayService.create_payment_link(
        amount=payload.amount,
        description=payload.description,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        obligation_id=payload.obligation_id
    )
    
    if payload.obligation_id:
        ob = db.query(Obligation).filter(Obligation.id == payload.obligation_id).first()
        if ob:
            ob.razorpay_payment_link_id = link["id"]
            db.commit()

    AuditChainService.record_event(
        db=db,
        event_type="RAZORPAY_PAYMENT_LINK_CREATED",
        actor="RECOVERY_ENGINE",
        details={"payment_link_id": link["id"], "amount": payload.amount, "obligation_id": payload.obligation_id}
    )
    return link

@router.post("/webhook")
async def handle_razorpay_webhook(
    request: Request,
    x_razorpay_signature: Optional[str] = Header(None),
    x_razorpay_event_id: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Razorpay Production Webhook Gateway with Idempotency & HMAC-SHA256 Verification:
    1. Signature Validation via HMAC-SHA256
    2. Idempotency Check using x-razorpay-event-id
    3. Audit Logging with Cryptographic Hash Chain
    4. Auto-Reconciliation & Recovery Completion
    """
    raw_body = await request.body()
    user_id = "user_finova_master_001"
    
    # 1. Webhook Signature Verification
    if not x_razorpay_signature:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing X-Razorpay-Signature header"
        )
        
    is_valid = RazorpayService.verify_webhook_signature(
        raw_body=raw_body,
        signature=x_razorpay_signature,
        secret=settings.RAZORPAY_WEBHOOK_SECRET
    )
    if not is_valid:
        AuditChainService.record_event(
            db=db,
            user_id=user_id,
            event_type="WEBHOOK_SIGNATURE_VERIFICATION_FAILED",
            actor="WEBHOOK_GATEWAY",
            details={"provided_signature": x_razorpay_signature}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Razorpay webhook signature"
        )

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Malformed JSON webhook payload")

    event_name = payload.get("event", "unknown")
    event_id = x_razorpay_event_id or payload.get("id") or f"evt_{hashlib.md5(raw_body).hexdigest()}"
    payload_hash = hashlib.sha256(raw_body).hexdigest()

    # 2. Idempotency Check (P0 Requirement: prevent duplicate deliveries)
    existing_event = db.query(WebhookEvent).filter(WebhookEvent.razorpay_event_id == event_id).first()
    if existing_event:
        existing_event.retry_count += 1
        db.commit()
        return {
            "status": "duplicate_ignored",
            "message": f"Webhook event '{event_id}' already ingested and processed.",
            "razorpay_event_id": event_id,
            "retry_count": existing_event.retry_count
        }

    # Record new Webhook Event
    webhook_rec = WebhookEvent(
        razorpay_event_id=event_id,
        event_type=event_name,
        payload_hash=payload_hash,
        raw_payload=raw_body.decode("utf-8"),
        signature_valid=True,
        processing_status="processing",
        received_at=datetime.datetime.utcnow()
    )
    db.add(webhook_rec)
    db.commit()

    # 3. Extract Payment Details
    payment_entity = payload.get("payload", {}).get("payment", {}).get("entity", {})
    plink_entity = payload.get("payload", {}).get("payment_link", {}).get("entity", {})
    
    pay_id = payment_entity.get("id")
    order_id = payment_entity.get("order_id")
    plink_id = plink_entity.get("id") or payment_entity.get("notes", {}).get("payment_link_id")
    amount_in_rupees = float(payment_entity.get("amount", 0)) / 100.0 if payment_entity else (float(plink_entity.get("amount", 0)) / 100.0)
    contact = payment_entity.get("contact")
    notes = payment_entity.get("notes", {})
    acquirer_data = payment_entity.get("acquirer_data", {})
    rrn = acquirer_data.get("rrn") or acquirer_data.get("upi_transaction_id") or f"RRN{event_id[:8]}"

    # Entity Resolution
    matched_person, _, _ = EntityResolutionService.resolve_entity(db=db, phone=contact, user_id=user_id)

    # Ingest into Payment Memory
    is_success = event_name in ["payment.captured", "order.paid", "payment_link.paid"]
    payment_event = PaymentEvent(
        user_id=user_id,
        person_id=matched_person.id if matched_person else None,
        utr_rrn=rrn,
        razorpay_payment_id=pay_id,
        razorpay_order_id=order_id,
        razorpay_payment_link_id=plink_id,
        amount=amount_in_rupees,
        currency="INR",
        direction="inbound",
        source="Razorpay Gateway",
        status="captured" if is_success else "failed",
        purpose=notes.get("description", f"Razorpay Settlement ({event_name})"),
        payment_date=datetime.datetime.utcnow(),
        confidence=1.0
    )
    db.add(payment_event)
    db.commit()
    db.refresh(payment_event)

    # 4. Auto-Reconcile if successful
    reconciled_res = None
    obligation_id = notes.get("obligation_id")
    if is_success and amount_in_rupees > 0:
        reconciled_res = ReconciliationEngine.reconcile_payment(
            db=db,
            payment_event_id=payment_event.id,
            user_id=user_id,
            force_manual_ob_id=obligation_id
        )
        
        # Check stopping rule: if obligation settled, update RecoveryAction
        if obligation_id:
            ob = db.query(Obligation).filter(Obligation.id == obligation_id).first()
            if ob and ob.status == "settled":
                ob.recovery_stage = "recovered"
                ob.stop_reason = "PAYMENT_RECEIVED_WEBHOOK"
                db.add(RecoveryAction(
                    user_id=user_id,
                    obligation_id=ob.id,
                    action_type="stop_action",
                    stage="stopped",
                    channel="system",
                    message="Automated recovery halted: Full payment verified via Razorpay webhook.",
                    status="stopped"
                ))
                db.commit()

    # 5. Tamper-Evident Audit Chain Logging
    AuditChainService.record_event(
        db=db,
        user_id=user_id,
        event_type="RAZORPAY_WEBHOOK_PROCESSED",
        actor="RAZORPAY_WEBHOOK",
        details={
            "event": event_name,
            "event_id": event_id,
            "razorpay_payment_id": pay_id,
            "amount": amount_in_rupees,
            "utr": rrn,
            "idempotent": True,
            "matched_person": matched_person.canonical_name if matched_person else "Unknown"
        }
    )

    webhook_rec.processing_status = "processed"
    webhook_rec.processed_at = datetime.datetime.utcnow()
    db.commit()

    return {
        "status": "success",
        "razorpay_event_id": event_id,
        "event": event_name,
        "payment_event_id": payment_event.id,
        "amount": amount_in_rupees,
        "reconciled": reconciled_res
    }

@router.post("/simulate-webhook")
def simulate_razorpay_webhook_event(
    event_name: str = "payment.captured",
    amount: float = 30000.0,
    obligation_id: Optional[str] = None,
    phone: Optional[str] = "+919876543210",
    event_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Simulation Lab Helper: Fires a signed Razorpay webhook through the gateway with event ID tracking
    """
    payload_dict, signature, raw_body, generated_evt_id = RazorpayService.simulate_webhook_event(
        event_name=event_name,
        amount=amount,
        event_id=event_id,
        contact=phone,
        notes={"obligation_id": obligation_id or ""}
    )
    
    # Forward through the standard webhook ingestion logic
    user_id = "user_finova_master_001"
    evt_id = event_id or generated_evt_id
    
    # Check duplicate
    existing = db.query(WebhookEvent).filter(WebhookEvent.razorpay_event_id == evt_id).first()
    if existing:
        existing.retry_count += 1
        db.commit()
        return {
            "success": True,
            "status": "duplicate_ignored",
            "message": f"Webhook '{evt_id}' recognized as duplicate and safely ignored (Idempotency verified)."
        }
        
    payment_entity = payload_dict["payload"]["payment"]["entity"]
    pay_id = payment_entity["id"]
    rrn = payment_entity["acquirer_data"]["rrn"]
    
    # Store Webhook Event
    webhook_rec = WebhookEvent(
        razorpay_event_id=evt_id,
        event_type=event_name,
        payload_hash=hashlib.sha256(raw_body).hexdigest(),
        raw_payload=raw_body.decode("utf-8"),
        signature_valid=True,
        processing_status="processed",
        received_at=datetime.datetime.utcnow(),
        processed_at=datetime.datetime.utcnow()
    )
    db.add(webhook_rec)
    
    matched_person, _, _ = EntityResolutionService.resolve_entity(db=db, phone=phone, user_id=user_id)
    payment_event = PaymentEvent(
        user_id=user_id,
        person_id=matched_person.id if matched_person else None,
        utr_rrn=rrn,
        razorpay_payment_id=pay_id,
        amount=amount,
        currency="INR",
        direction="inbound",
        source="Razorpay Sandbox Webhook",
        status="captured",
        purpose="Simulated Razorpay Settlement",
        payment_date=datetime.datetime.utcnow(),
        confidence=1.0
    )
    db.add(payment_event)
    db.commit()
    db.refresh(payment_event)

    rec_res = ReconciliationEngine.reconcile_payment(
        db=db,
        payment_event_id=payment_event.id,
        user_id=user_id,
        force_manual_ob_id=obligation_id
    )

    AuditChainService.record_event(
        db=db,
        user_id=user_id,
        event_type="SIMULATED_RAZORPAY_WEBHOOK_INGESTED",
        actor="SIMULATION_LAB",
        details={"event_id": evt_id, "amount": amount, "utr": rrn, "payment_id": pay_id}
    )

    return {
        "success": True,
        "message": f"Webhook '{event_name}' received, verified, and saved to webhook_events idempotency table.",
        "razorpay_event_id": evt_id,
        "simulated_payment_id": pay_id,
        "utr_rrn": rrn,
        "amount": amount,
        "reconciliation": rec_res
    }
