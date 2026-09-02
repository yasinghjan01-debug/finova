from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import Optional

from apps.api.core.database import get_db
from apps.api.engines.payment_memory import PaymentMemoryEngine
from apps.api.schemas.schemas import ProofOCRRequest, ProofOCRResponse, SearchQuery, SearchResponse

router = APIRouter(prefix="/memory", tags=["Payment Memory"])

@router.post("/find-my-money", response_model=SearchResponse)
def find_my_money(payload: SearchQuery, db: Session = Depends(get_db)):
    """
    Hero Feature: 'Find My Money' Search
    """
    user_id = "user_finova_master_001"
    res = PaymentMemoryEngine.find_my_money(db=db, query=payload.query, user_id=user_id, limit=payload.limit)
    return res

@router.post("/ingest-proof", response_model=ProofOCRResponse)
def ingest_payment_proof(payload: ProofOCRRequest, db: Session = Depends(get_db)):
    """
    Flagship Workflow: Upload screenshot OCR / raw text -> Extract -> Entity Resolution -> Reconcile
    """
    user_id = "user_finova_master_001"
    if not payload.raw_text:
        raise HTTPException(status_code=400, detail="raw_text or extracted OCR content is required")
        
    res = PaymentMemoryEngine.ingest_unstructured_proof(
        db=db,
        raw_text=payload.raw_text,
        user_id=user_id,
        proof_image_url=payload.image_base64
    )
    
    return {
        "extracted_amount": res.get("amount"),
        "extracted_utr": res.get("utr"),
        "extracted_sender_name": res.get("sender_name"),
        "extracted_vpa": res.get("sender_vpa"),
        "matched_person_id": res.get("matched_person_id"),
        "matched_person_name": res.get("matched_person_name"),
        "entity_confidence": res.get("entity_confidence", 0.0),
        "auto_reconciled": res.get("auto_reconciled", False),
        "reconciled_obligation_id": res.get("reconciled_obligation_id"),
        "matched_obligation_title": res.get("matched_obligation_title"),
        "proof_summary": res.get("proof_summary", "")
    }
