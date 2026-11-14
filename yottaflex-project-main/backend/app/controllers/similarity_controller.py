from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.roles import SIMILARITY_ROLES
from app.core.security import require_roles
from app.db.session import get_db
from app.models import User
from app.schemas import TextComparison
from app.services.similarity_service import compare_with_active_rule

router = APIRouter(prefix="/similarity", tags=["similarity"])


@router.post("/compare")
def analyze_similarity(
    payload: TextComparison,
    _: User = Depends(require_roles(*SIMILARITY_ROLES)),
    db: Session = Depends(get_db),
):
    try:
        return compare_with_active_rule(payload.text_a, payload.text_b, db)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=f"Unable to compare text: {exc}") from exc
