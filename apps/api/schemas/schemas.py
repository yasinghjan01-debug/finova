import datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

# Identity schemas
class IdentityBase(BaseModel):
    identity_type: str
    identity_value: str
    confidence_score: float = 1.0
    verified: bool = True
    source: str = "manual"

class IdentityCreate(IdentityBase):
    pass

class IdentityRead(IdentityBase):
    id: str
    person_id: str
    created_at: datetime.datetime
    class Config:
        from_attributes = True

# Person / Counterparty schemas
class PersonBase(BaseModel):
    canonical_name: str
    primary_phone: Optional[str] = None
    primary_vpa: Optional[str] = None
    category: str = "counterparty"
    trust_score: float = 80.0
    payment_reliability: float = 85.0
    avg_delay_days: float = 2.5
    notes: Optional[str] = None

class PersonCreate(PersonBase):
    initial_identities: Optional[List[IdentityCreate]] = None

class PersonRead(PersonBase):
    id: str
    user_id: str
    total_given: float
    total_received: float
    outstanding_balance: float
    created_at: datetime.datetime
    updated_at: datetime.datetime
    identities: List[IdentityRead] = []
    class Config:
        from_attributes = True

# Obligation schemas
class ObligationBase(BaseModel):
    person_id: str
    title: str
    obligation_type: str = "receivable"  # receivable, payable, invoice, advance, loan, emi
    total_amount: float
    due_date: Optional[datetime.datetime] = None
    invoice_number: Optional[str] = None
    notes: Optional[str] = None

class ObligationCreate(ObligationBase):
    pass

class ObligationRead(ObligationBase):
    id: str
    user_id: str
    settled_amount: float
    remaining_amount: float
    status: str
    recovery_stage: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    class Config:
        from_attributes = True

# Payment Event schemas
class PaymentEventBase(BaseModel):
    amount: float
    currency: str = "INR"
    direction: str = "inbound"  # inbound, outbound
    source: str = "razorpay"  # razorpay, screenshot_ocr, upi_sms, manual
    utr_rrn: Optional[str] = None
    razorpay_payment_id: Optional[str] = None
    razorpay_order_id: Optional[str] = None
    purpose: Optional[str] = None
    payment_date: Optional[datetime.datetime] = None
    raw_proof_text: Optional[str] = None
    proof_image_url: Optional[str] = None

class PaymentEventCreate(PaymentEventBase):
    person_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_vpa: Optional[str] = None
    sender_phone: Optional[str] = None

class PaymentEventRead(PaymentEventBase):
    id: str
    user_id: str
    person_id: Optional[str] = None
    status: str
    confidence: float
    created_at: datetime.datetime
    class Config:
        from_attributes = True

# Screenshot OCR Upload
class ProofOCRRequest(BaseModel):
    raw_text: Optional[str] = None
    image_base64: Optional[str] = None
    filename: Optional[str] = None

class ProofOCRResponse(BaseModel):
    extracted_amount: Optional[float] = None
    extracted_utr: Optional[str] = None
    extracted_sender_name: Optional[str] = None
    extracted_vpa: Optional[str] = None
    extracted_date: Optional[str] = None
    matched_person_id: Optional[str] = None
    matched_person_name: Optional[str] = None
    entity_confidence: float = 0.0
    auto_reconciled: bool = False
    reconciled_obligation_id: Optional[str] = None
    matched_obligation_title: Optional[str] = None
    proof_summary: str

# Find My Money Search
class SearchQuery(BaseModel):
    query: str
    limit: int = 20

class SearchMatch(BaseModel):
    payment_id: str
    amount: float
    utr_rrn: Optional[str]
    person_name: str
    payment_date: str
    purpose: Optional[str]
    source: str
    proof_available: bool
    status: str
    confidence: float
    matched_obligation: Optional[str] = None
    evidence_snippet: str

class SearchResponse(BaseModel):
    query: str
    total_matches: int
    total_amount_matched: float
    matches: List[SearchMatch]

# Risk and Impersonation
class RiskAnalysisRequest(BaseModel):
    person_name: str
    claimed_person_id: Optional[str] = None
    request_phone: Optional[str] = None
    destination_vpa: Optional[str] = None
    amount: float
    message_text: Optional[str] = None

class RiskAnalysisResponse(BaseModel):
    risk_score: float  # 0 to 100
    risk_level: str  # LOW, MEDIUM, HIGH, CRITICAL
    ml_probability: float
    flagged_signals: List[str]
    explanation: str
    recommendation: str
    requires_approval: bool
    approval_request_id: Optional[str] = None

# Approval Request
class ApprovalAction(BaseModel):
    decision: str  # approve, reject, escalate
    note: Optional[str] = None

class ApprovalRead(BaseModel):
    id: str
    action_type: str
    title: str
    description: str
    severity: str
    target_entity_name: Optional[str] = None
    amount: Optional[float] = None
    payload: Dict[str, Any]
    status: str
    created_at: datetime.datetime
    class Config:
        from_attributes = True

# Razorpay Webhook & Payment Link
class RazorpayWebhookPayload(BaseModel):
    event: str
    payload: Dict[str, Any]

class PaymentLinkCreate(BaseModel):
    obligation_id: str
    amount: float
    customer_name: str
    customer_phone: Optional[str] = None
    description: str

class PaymentLinkResponse(BaseModel):
    payment_link_id: str
    short_url: str
    amount: float
    status: str
    expires_at: Optional[str] = None

# AI Assistant Query
class AssistantQueryRequest(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, str]]] = []

class EvidenceItem(BaseModel):
    title: str
    date: str
    amount: Optional[float] = None
    utr: Optional[str] = None
    type: str

class AssistantQueryResponse(BaseModel):
    answer: str
    evidence: List[EvidenceItem]
    action_suggested: Optional[str] = None
