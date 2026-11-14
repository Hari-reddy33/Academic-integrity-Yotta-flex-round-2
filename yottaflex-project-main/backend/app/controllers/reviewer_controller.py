from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.roles import ADMIN_ROLES
from app.core.security import require_roles
from app.db.session import get_db
from app.models import CaseReviewer, IntegrityCase, Reviewer, User

router = APIRouter(prefix="/reviewers", tags=["reviewers"])


@router.get("")
def list_reviewers(
    _: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    rows = db.execute(
        select(Reviewer, User).join(User, Reviewer.user_id == User.id).order_by(Reviewer.id)
    ).all()
    result = []
    for reviewer, user in rows:
        active_cases = db.scalar(
            select(func.count(CaseReviewer.id)).join(IntegrityCase).where(
                CaseReviewer.reviewer_id == reviewer.id,
                IntegrityCase.status.in_(("open", "under_review", "appealed")),
            )
        ) or 0
        result.append({
            "id": reviewer.id,
            "name": user.full_name,
            "department": reviewer.department,
            "active_cases": active_cases,
        })
    return result
