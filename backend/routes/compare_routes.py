# ==============================================================================
# COMPANY PEERS / COMPARISON ROUTE (TEMPORARILY COMMENTED OUT FOR FUTURE USE)
# Focused solely on Prospect Analysis & Proposal-Based Analysis for now.
# ==============================================================================

# import logging
# from typing import List, Optional
# from fastapi import APIRouter, Depends, HTTPException, status
# from pydantic import BaseModel
# from sqlalchemy.orm import Session
# 
# from database import get_db
# from models.user import User
# from auth.dependencies import get_current_user
# from services.comparison_service import compare_multiple_prospects
# 
# logger = logging.getLogger(__name__)
# router = APIRouter(tags=["Peer Comparison"])
# 
# class CompareRequest(BaseModel):
#     prospect_names: Optional[List[str]] = None
#     prospects: Optional[List[str]] = None
#     domain: Optional[str] = "Insurance"
#     mock_mode: Optional[bool] = False
# 
# @router.post("/compare")
# def compare_prospects_endpoint(
#     req: CompareRequest,
#     current_user: User = Depends(get_current_user),
#     db: Session = Depends(get_db)
# ):
#     target_prospects = req.prospect_names or req.prospects or []
#     if not target_prospects or len(target_prospects) < 2:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Please provide at least 2 prospect names to compare (e.g. ['SBI Life Insurance', 'Allianz'])."
#         )
# 
#     try:
#         return compare_multiple_prospects(
#             prospect_names=target_prospects,
#             db=db,
#             current_user=current_user,
#             mock_mode=req.mock_mode or False
#         )
#     except ValueError as val_err:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(val_err))
#     except Exception as exc:
#         logger.error("Multi-Prospect Comparison Error: %s", exc)
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to generate comparison: {str(exc)}"
#         )
from fastapi import APIRouter

router = APIRouter(tags=["Peer Comparison (Disabled)"])

