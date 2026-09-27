from fastapi import APIRouter
from .auth_routes import router as auth_router
from .analysis_routes import router as analysis_router
from .chat_routes import router as chat_router
# from .compare_routes import router as compare_router  # Disabled for now (Peers Comparison)
from .prospect_routes import router as prospect_router
from .proposal_routes import router as proposal_router

router = APIRouter()

# Include all sub-routers
router.include_router(auth_router)
router.include_router(analysis_router)
router.include_router(chat_router)
# router.include_router(compare_router)  # Disabled for now (Peers Comparison)
router.include_router(prospect_router)
router.include_router(proposal_router)

__all__ = [
    "router",
    "auth_router",
    "analysis_router",
    "chat_router",
    # "compare_router",
    "prospect_router",
    "proposal_router"
]

