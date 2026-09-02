from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from apps.api.core.database import get_db
from apps.api.agents.assistant import EvidenceBackedAssistant
from apps.api.schemas.schemas import AssistantQueryRequest, AssistantQueryResponse

router = APIRouter(prefix="/assistant", tags=["Financial Memory Assistant"])

@router.post("/query", response_model=AssistantQueryResponse)
def query_financial_memory(payload: AssistantQueryRequest, db: Session = Depends(get_db)):
    """
    Evidence-Backed Financial AI Assistant: Always links answers back to actual transaction records.
    """
    user_id = "user_finova_master_001"
    res = EvidenceBackedAssistant.answer_query(db=db, query=payload.message, user_id=user_id)
    return res
