import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db
from models.user import User
from schemas.prospect import ChatRequest
from auth.dependencies import get_current_user
from services.chat_service import process_chat_request

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Conversational Intelligence"])

@router.post("/chat")
def chat_assistant(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return process_chat_request(req, current_user, db)
