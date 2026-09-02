import datetime
import uuid
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
)
from sqlalchemy.orm import relationship
from apps.api.core.database import Base

def generate_uuid():
    return str(uuid.uuid4())

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=True)
    phone = Column(String(30), nullable=True)
    business_name = Column(String(255), nullable=True)
    role = Column(String(50), default="merchant")  # merchant, freelancer, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relationships
    people = relationship("Person", back_populates="user", cascade="all, delete-orphan")
    obligations = relationship("Obligation", back_populates="user", cascade="all, delete-orphan")
    payment_events = relationship("PaymentEvent", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="user", cascade="all, delete-orphan")
    recovery_actions = relationship("RecoveryAction", back_populates="user", cascade="all, delete-orphan")

class Person(Base):
    __tablename__ = "people"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    canonical_name = Column(String(255), index=True, nullable=False)
    primary_phone = Column(String(30), nullable=True, index=True)
    primary_vpa = Column(String(100), nullable=True, index=True)
    category = Column(String(50), default="counterparty")  # client, vendor, employee, friend, contractor
    trust_score = Column(Float, default=80.0)  # 0 to 100
    payment_reliability = Column(Float, default=85.0)  # 0 to 100 %
    avg_delay_days = Column(Float, default=2.5)
    total_given = Column(Float, default=0.0)
    total_received = Column(Float, default=0.0)
    outstanding_balance = Column(Float, default=0.0)  # Positive = they owe us, Negative = we owe them
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="people")
    identities = relationship("Identity", back_populates="person", cascade="all, delete-orphan")
    obligations = relationship("Obligation", back_populates="person", cascade="all, delete-orphan")
    payment_events = relationship("PaymentEvent", back_populates="person")
    risk_events = relationship("RiskEvent", back_populates="person")

class Identity(Base):
    __tablename__ = "identities"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    person_id = Column(String(36), ForeignKey("people.id"), index=True, nullable=False)
    identity_type = Column(String(50), nullable=False)  # alias_name, phone, upi_vpa, bank_account, email
    identity_value = Column(String(255), index=True, nullable=False)
    confidence_score = Column(Float, default=1.0)
    verified = Column(Boolean, default=True)
    source = Column(String(100), default="manual")  # ocr, razorpay, whatsapp, manual
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    person = relationship("Person", back_populates="identities")

class Obligation(Base):
    __tablename__ = "obligations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    person_id = Column(String(36), ForeignKey("people.id"), index=True, nullable=False)
    title = Column(String(255), nullable=False)
    obligation_type = Column(String(50), default="receivable")  # receivable, payable, invoice, advance, loan, emi
    total_amount = Column(Float, nullable=False)
    settled_amount = Column(Float, default=0.0)
    remaining_amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending")  # pending, partial, settled, overdue, written_off
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    invoice_number = Column(String(100), nullable=True, index=True)
    razorpay_order_id = Column(String(100), nullable=True, index=True)
    razorpay_payment_link_id = Column(String(100), nullable=True, index=True)
    notes = Column(Text, nullable=True)
    recovery_stage = Column(String(50), default="none")  # none, scheduled_nudge, due_reminder, overdue_escalated, recovered, stopped
    stop_reason = Column(String(100), nullable=True)
    
    user = relationship("User", back_populates="obligations")
    person = relationship("Person", back_populates="obligations")
    reconciliation_records = relationship("ReconciliationRecord", back_populates="obligation", cascade="all, delete-orphan")
    recovery_actions = relationship("RecoveryAction", back_populates="obligation", cascade="all, delete-orphan")

class PaymentEvent(Base):
    __tablename__ = "payment_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    person_id = Column(String(36), ForeignKey("people.id"), index=True, nullable=True)
    utr_rrn = Column(String(100), index=True, nullable=True)
    razorpay_payment_id = Column(String(100), index=True, nullable=True)
    razorpay_order_id = Column(String(100), index=True, nullable=True)
    razorpay_payment_link_id = Column(String(100), index=True, nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    direction = Column(String(20), default="inbound")  # inbound, outbound
    source = Column(String(50), default="razorpay")  # razorpay, screenshot_ocr, upi_sms, bank_feed, manual
    status = Column(String(50), default="captured")  # captured, authorized, failed, refunded, pending_verification
    raw_proof_text = Column(Text, nullable=True)
    proof_image_url = Column(String(500), nullable=True)
    purpose = Column(String(255), nullable=True)
    payment_date = Column(DateTime, default=datetime.datetime.utcnow)
    confidence = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="payment_events")
    person = relationship("Person", back_populates="payment_events")
    reconciliation_records = relationship("ReconciliationRecord", back_populates="payment_event", cascade="all, delete-orphan")
    risk_events = relationship("RiskEvent", back_populates="payment_event")

class WebhookEvent(Base):
    __tablename__ = "webhook_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    razorpay_event_id = Column(String(100), unique=True, index=True, nullable=False)
    event_type = Column(String(100), index=True, nullable=False)
    payload_hash = Column(String(64), nullable=False)
    raw_payload = Column(Text, nullable=False)
    signature_valid = Column(Boolean, default=True)
    received_at = Column(DateTime, default=datetime.datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    processing_status = Column(String(50), default="processed")  # processed, duplicate, failed, ignored
    retry_count = Column(Integer, default=0)

class ReconciliationRecord(Base):
    __tablename__ = "reconciliation_records"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    obligation_id = Column(String(36), ForeignKey("obligations.id"), index=True, nullable=False)
    payment_event_id = Column(String(36), ForeignKey("payment_events.id"), index=True, nullable=False)
    matched_amount = Column(Float, nullable=False)
    match_confidence = Column(Float, default=1.0)
    match_strategy = Column(String(50), default="exact_utr_amount")  # exact_utr_amount, fuzzy_entity_amount, partial_settlement, manual_override
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    obligation = relationship("Obligation", back_populates="reconciliation_records")
    payment_event = relationship("PaymentEvent", back_populates="reconciliation_records")

class RiskEvent(Base):
    __tablename__ = "risk_events"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    person_id = Column(String(36), ForeignKey("people.id"), index=True, nullable=True)
    payment_event_id = Column(String(36), ForeignKey("payment_events.id"), index=True, nullable=True)
    risk_score = Column(Float, nullable=False)  # 0 - 100
    risk_level = Column(String(20), default="LOW")  # LOW, MEDIUM, HIGH, CRITICAL
    model_name = Column(String(50), default="XGBoost_Ensemble_v1")
    ml_probability = Column(Float, default=0.0)
    flagged_signals = Column(JSON, default=list)  # ["NEW_PAYMENT_DESTINATION", "URGENCY_SPIKE", "UNUSUAL_AMOUNT_7.5X"]
    reason_explanation = Column(Text, nullable=False)
    status = Column(String(30), default="pending_review")  # pending_review, approved_by_user, blocked, dismissed
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    person = relationship("Person", back_populates="risk_events")
    payment_event = relationship("PaymentEvent", back_populates="risk_events")

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=True)
    action_type = Column(String(50), nullable=False)  # send_recovery_reminder, block_transfer, confirm_reconciliation, verify_impersonator
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(String(20), default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    target_entity_name = Column(String(255), nullable=True)
    amount = Column(Float, nullable=True)
    payload = Column(JSON, default=dict)
    status = Column(String(30), default="pending")  # pending, approved, rejected, escalated
    user_decision_note = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="approval_requests")

class RecoveryAction(Base):
    __tablename__ = "recovery_actions"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=False)
    obligation_id = Column(String(36), ForeignKey("obligations.id"), index=True, nullable=False)
    action_type = Column(String(50), nullable=False)  # gentle_reminder, payment_link, escalated_notice, stop_action
    stage = Column(String(50), nullable=False)  # day_1, day_3, day_7, day_14, stopped
    channel = Column(String(50), default="whatsapp")  # whatsapp, sms, email, manual
    message = Column(Text, nullable=False)
    razorpay_payment_link_id = Column(String(100), nullable=True)
    status = Column(String(50), default="executed")  # scheduled, executed, approved, stopped
    scheduled_at = Column(DateTime, default=datetime.datetime.utcnow)
    executed_at = Column(DateTime, default=datetime.datetime.utcnow)
    approved_by = Column(String(50), default="policy")  # policy, user
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="recovery_actions")
    obligation = relationship("Obligation", back_populates="recovery_actions")

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id"), index=True, nullable=True)
    sequence_number = Column(Integer, nullable=True, index=True)
    previous_hash = Column(String(64), nullable=True)
    event_hash = Column(String(64), nullable=True, index=True)
    event_type = Column(String(100), nullable=False)  # WEBHOOK_RECEIVED, OCR_PROCESSED, RECONCILIATION_AUTO, RISK_ALERT_TRIGGERED, USER_APPROVED_ACTION
    actor = Column(String(50), default="AI_AGENT")  # AI_AGENT, USER, RAZORPAY_WEBHOOK, POLICY_ENGINE
    details = Column(JSON, default=dict)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    user = relationship("User", back_populates="audit_logs")
