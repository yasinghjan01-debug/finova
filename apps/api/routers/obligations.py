import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from apps.api.core.database import get_db
from apps.api.models.schema import Obligation, Person
from apps.api.schemas.schemas import ObligationCreate, ObligationRead
from apps.api.services.graph_svc import GraphService

router = APIRouter(prefix="/obligations", tags=["Obligations & Ledgers"])

@router.get("")
def list_obligations(
    status: Optional[str] = None,
    obligation_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    user_id = "user_finova_master_001"
    query = db.query(Obligation).filter(Obligation.user_id == user_id)
    if status:
        query = query.filter(Obligation.status == status)
    if obligation_type:
        query = query.filter(Obligation.obligation_type == obligation_type)
        
    obs = query.order_by(Obligation.due_date.asc()).all()
    results = []
    for o in obs:
        results.append({
            "id": o.id,
            "person_id": o.person_id,
            "person_name": o.person.canonical_name if o.person else "Unknown",
            "title": o.title,
            "obligation_type": o.obligation_type,
            "total_amount": o.total_amount,
            "settled_amount": o.settled_amount,
            "remaining_amount": o.remaining_amount,
            "status": o.status,
            "due_date": o.due_date.strftime("%d %b %Y") if o.due_date else "No due date",
            "invoice_number": o.invoice_number,
            "recovery_stage": o.recovery_stage
        })
    return results

@router.post("")
def create_obligation(payload: ObligationCreate, db: Session = Depends(get_db)):
    user_id = "user_finova_master_001"
    person = db.query(Person).filter(Person.id == payload.person_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Person not found")
        
    ob = Obligation(
        user_id=user_id,
        person_id=payload.person_id,
        title=payload.title,
        obligation_type=payload.obligation_type,
        total_amount=payload.total_amount,
        settled_amount=0.0,
        remaining_amount=payload.total_amount,
        status="pending",
        due_date=payload.due_date or (datetime.datetime.utcnow() + datetime.timedelta(days=7)),
        invoice_number=payload.invoice_number,
        notes=payload.notes
    )
    db.add(ob)
    db.commit()
    db.refresh(ob)
    GraphService.recalculate_person_ledger(db, person.id)
    return {"id": ob.id, "title": ob.title, "remaining_amount": ob.remaining_amount}
