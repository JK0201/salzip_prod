from fastapi import APIRouter

from app.api.v1 import analyze as analyze_module
from app.api.v1 import auth as auth_module
from app.api.v1 import favorites as favorites_module
from app.api.v1 import recommend as recommend_module
from app.api.v1 import session as session_module

router = APIRouter()
router.include_router(session_module.router)
router.include_router(recommend_module.router)
router.include_router(auth_module.router, prefix="/auth")
router.include_router(favorites_module.router)
router.include_router(analyze_module.router)
