from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from apps.api.core.database import get_db
from apps.api.engines.relationship_graph import RelationshipGraphEngine
from apps.api.models.schema import Person, Identity
from apps.api.schemas.schemas import PersonCreate

router = APIRouter(prefix="/people", tags=["Financial Relationship Graph"])

@router.get("")
def list_relationships(db: Session = Depends(get_db)):
    user_id = "user_finova_master_001"
    return RelationshipGraphEngine.get_all_relationships(db, user_id)

@router.get("/{person_id}")
def get_relationship_card(person_id: str, db: Session = Depends(get_db)):
    card = RelationshipGraphEngine.get_person_relationship_card(db, person_id)
    if not card:
        raise HTTPException(status_code=404, detail="Person not found")
    return card

@router.post("")
def create_person(payload: PersonCreate, db: Session = Depends(get_db)):
    user_id = "user_finova_master_001"
    person = Person(
        user_id=user_id,
        canonical_name=payload.canonical_name,
        primary_phone=payload.primary_phone,
        primary_vpa=payload.primary_vpa,
        category=payload.category,
        trust_score=payload.trust_score,
        payment_reliability=payload.payment_reliability,
        avg_delay_days=payload.avg_delay_days,
        notes=payload.notes
    )
    db.add(person)
    db.flush()
    
    # Add initial identities
    if payload.primary_phone:
        db.add(Identity(person_id=person.id, identity_type="phone", identity_value=payload.primary_phone))
    if payload.primary_vpa:
        db.add(Identity(person_id=person.id, identity_type="upi_vpa", identity_value=payload.primary_vpa))
    db.add(Identity(person_id=person.id, identity_type="alias_name", identity_value=payload.canonical_name))
    
    db.commit()
    db.refresh(person)
    return {"id": person.id, "canonical_name": person.canonical_name}
