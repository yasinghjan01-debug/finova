import datetime
from sqlalchemy.orm import Session
from apps.api.core.database import SessionLocal, engine, Base
from apps.api.models.schema import (
    User, Person, Identity, Obligation, PaymentEvent,
    ReconciliationRecord, RiskEvent, ApprovalRequest, AuditLog
)
from apps.api.core.auth import hash_password
from apps.api.services.graph_svc import GraphService
from apps.api.services.audit_svc import AuditChainService

def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    
    # Check if already seeded
    existing_user = db.query(User).filter(User.email == "demo@finova.ai").first()
    if existing_user:
        if not existing_user.password_hash:
            existing_user.password_hash = hash_password("FinovaSecure2026!")
            db.commit()
        db.close()
        return

    print("Seeding database with realistic Indian SMB data & cryptographic audit chain...")
    
    # 1. Create Primary User (Freelance Agency / Merchant)
    user = User(
        id="user_finova_master_001",
        email="demo@finova.ai",
        name="Arjun Mehta",
        password_hash=hash_password("FinovaSecure2026!"),
        phone="+919811223344",
        business_name="Mehta Digital & Infrastructure Solutions",
        role="merchant",
        is_active=True
    )
    db.add(user)
    db.flush()
    
    # 2. Create People & Verified Identities
    
    # Contact 1: Rahul Sharma (Key client)
    rahul = Person(
        id="person_rahul_001",
        user_id=user.id,
        canonical_name="Rahul Sharma",
        primary_phone="+919876543210",
        primary_vpa="rahul.sharma@okhdfcbank",
        category="client",
        trust_score=82.0,
        payment_reliability=78.0,
        avg_delay_days=4.2,
        notes="Key commercial client for Construction Project Phase 1 & 2"
    )
    db.add(rahul)
    db.flush()
    
    db.add_all([
        Identity(person_id=rahul.id, identity_type="alias_name", identity_value="Rahul", confidence_score=0.98, verified=True),
        Identity(person_id=rahul.id, identity_type="alias_name", identity_value="Rahul Bhai", confidence_score=0.92, verified=True),
        Identity(person_id=rahul.id, identity_type="phone", identity_value="+919876543210", confidence_score=1.0, verified=True),
        Identity(person_id=rahul.id, identity_type="upi_vpa", identity_value="rahul.sharma@okhdfcbank", confidence_score=1.0, verified=True),
        Identity(person_id=rahul.id, identity_type="upi_vpa", identity_value="rahul@upi", confidence_score=0.95, verified=True)
    ])
    
    # Contact 2: Anita Desai (Freelance UI/UX Designer)
    anita = Person(
        id="person_anita_002",
        user_id=user.id,
        canonical_name="Anita Desai",
        primary_phone="+919822334455",
        primary_vpa="anita.desai@paytm",
        category="vendor",
        trust_score=94.0,
        payment_reliability=96.0,
        avg_delay_days=1.1,
        notes="High-reliability design partner"
    )
    db.add(anita)
    db.flush()
    db.add_all([
        Identity(person_id=anita.id, identity_type="alias_name", identity_value="Anita", confidence_score=0.95, verified=True),
        Identity(person_id=anita.id, identity_type="phone", identity_value="+919822334455", confidence_score=1.0, verified=True),
        Identity(person_id=anita.id, identity_type="upi_vpa", identity_value="anita.desai@paytm", confidence_score=1.0, verified=True)
    ])

    # Contact 3: Vikram Mehta (Building Materials Supplier)
    vikram = Person(
        id="person_vikram_003",
        user_id=user.id,
        canonical_name="Vikram Mehta",
        primary_phone="+919833445566",
        primary_vpa="vikram.materials@icici",
        category="vendor",
        trust_score=68.0,
        payment_reliability=70.0,
        avg_delay_days=8.5,
        notes="Supplies cement and steel. Frequent payment delays."
    )
    db.add(vikram)
    db.flush()
    db.add_all([
        Identity(person_id=vikram.id, identity_type="alias_name", identity_value="Vikram Bhai Steel", confidence_score=0.90, verified=True),
        Identity(person_id=vikram.id, identity_type="phone", identity_value="+919833445566", confidence_score=1.0, verified=True)
    ])

    # 3. Create Obligations
    now = datetime.datetime.utcnow()
    
    ob_rahul_1 = Obligation(
        id="ob_rahul_001",
        user_id=user.id,
        person_id=rahul.id,
        title="Construction Project Advance",
        obligation_type="advance",
        total_amount=75000.0,
        settled_amount=45000.0,
        remaining_amount=30000.0,
        status="partial",
        due_date=now - datetime.timedelta(days=4),
        invoice_number="INV-2026-081",
        razorpay_order_id="order_finova_081_test",
        recovery_stage="due_reminder"
    )
    db.add(ob_rahul_1)
    
    ob_anita_1 = Obligation(
        id="ob_anita_001",
        user_id=user.id,
        person_id=anita.id,
        title="Mobile App Design Sprint",
        obligation_type="payable",
        total_amount=25000.0,
        settled_amount=25000.0,
        remaining_amount=0.0,
        status="settled",
        due_date=now - datetime.timedelta(days=12),
        invoice_number="INV-DESAI-409"
    )
    db.add(ob_anita_1)
    
    ob_vikram_1 = Obligation(
        id="ob_vikram_001",
        user_id=user.id,
        person_id=vikram.id,
        title="Material Return Refund",
        obligation_type="receivable",
        total_amount=48500.0,
        settled_amount=0.0,
        remaining_amount=48500.0,
        status="overdue",
        due_date=now - datetime.timedelta(days=16),
        invoice_number="RET-2026-004",
        recovery_stage="overdue_escalated"
    )
    db.add(ob_vikram_1)
    db.flush()

    # 4. Create Historical Payment Events & Reconciliations
    pay_rahul_1 = PaymentEvent(
        id="pay_rahul_001",
        user_id=user.id,
        person_id=rahul.id,
        utr_rrn="628192837191",
        amount=20000.0,
        currency="INR",
        direction="inbound",
        source="Google Pay",
        status="captured",
        purpose="Construction advance instalment 1",
        payment_date=now - datetime.timedelta(days=14),
        raw_proof_text="Google Pay\nPaid ₹20,000 to Arjun Mehta\nFrom: Rahul Sharma (rahul.sharma@okhdfcbank)\nUPI Ref: 628192837191\nDate: 10 Aug 2026"
    )
    db.add(pay_rahul_1)
    db.flush()
    db.add(ReconciliationRecord(
        obligation_id=ob_rahul_1.id,
        payment_event_id=pay_rahul_1.id,
        matched_amount=20000.0,
        match_confidence=0.99,
        match_strategy="exact_utr_amount"
    ))

    pay_rahul_2 = PaymentEvent(
        id="pay_rahul_002",
        user_id=user.id,
        person_id=rahul.id,
        utr_rrn="918237468921",
        amount=25000.0,
        currency="INR",
        direction="inbound",
        source="PhonePe",
        status="captured",
        purpose="Construction material milestone 2",
        payment_date=now - datetime.timedelta(days=7),
        raw_proof_text="PhonePe Transaction Successful\nAmount: ₹25,000\nSent by: Rahul Sharma\nUTR: 918237468921\n17 Aug 2026"
    )
    db.add(pay_rahul_2)
    db.flush()
    db.add(ReconciliationRecord(
        obligation_id=ob_rahul_1.id,
        payment_event_id=pay_rahul_2.id,
        matched_amount=25000.0,
        match_confidence=0.99,
        match_strategy="exact_utr_amount"
    ))

    # 5. Create Pending AI Approval Action
    approval_1 = ApprovalRequest(
        id="appr_risk_001",
        user_id=user.id,
        action_type="block_suspicious_transfer",
        title="⚠️ HIGH RISK: ₹75,000 request from Rahul Sharma (New Number)",
        description="Request originated from unverified phone +919876543999 asking for urgent ₹75,000 transfer to a new VPA 'rahul.urgent@paytm'. Amount is 7.5x historical average.",
        severity="HIGH",
        target_entity_name="Rahul Sharma",
        amount=75000.0,
        payload={
            "risk_score": 92.4,
            "flagged_signals": [
                "NEW_PHONE_NUMBER_ORIGIN",
                "NEW_PAYMENT_DESTINATION_VPA",
                "UNUSUAL_AMOUNT_7.5X_BASELINE",
                "COERCIVE_URGENCY_LANGUAGE"
            ],
            "destination_vpa": "rahul.urgent@paytm",
            "request_phone": "+919876543999"
        }
    )
    db.add(approval_1)
    db.commit()

    # 6. Initialize Cryptographic Audit Hash Chain
    AuditChainService.record_event(
        db=db,
        user_id=user.id,
        event_type="GENESIS_SYSTEM_INITIALIZED",
        actor="FINOVA_BOOTSTRAP",
        details={"version": "1.0.0", "status": "all_5_engines_online", "crypto_audit": "active"}
    )
    
    AuditChainService.record_event(
        db=db,
        user_id=user.id,
        event_type="INITIAL_LEDGER_SYNC",
        actor="RECONCILIATION_ENGINE",
        details={"counterparties_seeded": 3, "obligations_seeded": 3}
    )

    # Recalculate ledgers
    GraphService.recalculate_person_ledger(db, rahul.id)
    GraphService.recalculate_person_ledger(db, anita.id)
    GraphService.recalculate_person_ledger(db, vikram.id)
    
    print("Database successfully seeded with realistic entities and tamper-evident audit hash chain!")
    db.close()

if __name__ == "__main__":
    seed_database()
