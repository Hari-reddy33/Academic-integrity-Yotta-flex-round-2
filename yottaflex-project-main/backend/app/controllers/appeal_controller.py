from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.roles import ADMIN_ROLES, APPEAL_ROLES
from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models import (
    Appeal,
    CaseEvent,
    CaseReviewer,
    Decision,
    IntegrityCase,
    Learner,
    Reviewer,
    Submission,
    User,
)
from app.schemas import AppealAssign, AppealResolve

router = APIRouter(prefix="/appeals", tags=["appeals"])


@router.get("")
def list_appeals(
    user: User = Depends(require_roles(*APPEAL_ROLES)),
    db: Session = Depends(get_db),
):
    query = (
        select(Appeal, IntegrityCase)
        .join(IntegrityCase, Appeal.case_id == IntegrityCase.id)
        .options(selectinload(IntegrityCase.assignments))
    )
    if user.role == "learner":
        query = query.join(Submission).join(Learner).where(Learner.user_id == user.id)
    elif user.role == "reviewer":
        reviewer_id = db.scalar(select(Reviewer.id).where(Reviewer.user_id == user.id))
        if reviewer_id is None:
            return []
        query = query.where(Appeal.independent_reviewer_id == reviewer_id)
    rows = db.execute(query.order_by(Appeal.submitted_at.desc()))
    return [
        {
            "appeal_key": appeal.appeal_key,
            "case_key": case.case_key,
            "status": appeal.status,
            "outcome": appeal.outcome,
            "reason": appeal.reason,
            "submitted_at": appeal.submitted_at,
            "original_reviewer_id": case.decisions[0].reviewer_id if case.decisions else None,
            "original_reviewer_user_id": (
                case.decisions[0].reviewer.user_id if case.decisions else None
            ),
            "independent_reviewer_id": appeal.independent_reviewer_id,
            "conflicted_reviewer_ids": [
                assignment.reviewer_id
                for assignment in case.assignments
                if assignment.conflict_declared
            ],
        }
        for appeal, case in rows
    ]


@router.post("/{appeal_key}/assign")
def assign_appeal_reviewer(
    appeal_key: str,
    payload: AppealAssign,
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    appeal = db.scalar(
        select(Appeal).where(Appeal.appeal_key == appeal_key).options(
            joinedload(Appeal.case).joinedload(IntegrityCase.decisions)
        )
    )
    if appeal is None:
        raise HTTPException(status_code=404, detail="Appeal not found")
    if appeal.status != "pending" or appeal.case.status != "appealed":
        raise HTTPException(status_code=409, detail="Only pending appeals can be assigned")
    reviewer = db.get(Reviewer, payload.reviewer_id)
    if reviewer is None:
        raise HTTPException(status_code=404, detail="Reviewer not found")
    original_reviewer_ids = {decision.reviewer_id for decision in appeal.case.decisions}
    if reviewer.id in original_reviewer_ids:
        raise HTTPException(status_code=409, detail="The original decision-maker cannot review this appeal")
    conflict = db.scalar(
        select(CaseReviewer.id).where(
            CaseReviewer.case_id == appeal.case_id,
            CaseReviewer.reviewer_id == reviewer.id,
            CaseReviewer.conflict_declared.is_(True),
        )
    )
    if conflict:
        raise HTTPException(status_code=409, detail="A conflicted reviewer cannot review this appeal")

    appeal.independent_reviewer_id = reviewer.id
    db.add(CaseEvent(
        case_id=appeal.case_id,
        actor_id=user.id,
        event_type="appeal_reviewer_assigned",
        from_state=appeal.case.status,
        to_state=appeal.case.status,
        details=f"Assigned independent appeal reviewer {reviewer.reviewer_key}",
    ))
    db.commit()
    return {"appeal_key": appeal.appeal_key, "reviewer_id": reviewer.id, "status": appeal.status}


@router.post("/{appeal_key}/resolve")
def resolve_appeal(
    appeal_key: str,
    payload: AppealResolve,
    user: User = Depends(require_roles("reviewer")),
    db: Session = Depends(get_db),
):
    appeal = db.scalar(
        select(Appeal).where(Appeal.appeal_key == appeal_key).options(
            joinedload(Appeal.case).joinedload(IntegrityCase.decisions).joinedload(Decision.reviewer)
        )
    )
    if appeal is None:
        raise HTTPException(status_code=404, detail="Appeal not found")
    if appeal.status != "pending":
        raise HTTPException(status_code=409, detail="Appeal is already resolved")
    if appeal.case.status != "appealed" or not appeal.case.decisions:
        raise HTTPException(status_code=409, detail="The case is not in an appealable state")
    reviewer = db.scalar(select(Reviewer).where(Reviewer.user_id == user.id))
    if reviewer is None:
        raise HTTPException(status_code=403, detail="Appeal resolution requires an independent reviewer account")
    if appeal.independent_reviewer_id != reviewer.id:
        raise HTTPException(status_code=409, detail="This appeal is not assigned to you")
    original_reviewer_ids = {decision.reviewer_id for decision in appeal.case.decisions}
    if reviewer.id in original_reviewer_ids:
        raise HTTPException(status_code=409, detail="The original decision-maker cannot review this appeal")
    conflict = db.scalar(
        select(CaseReviewer.id).where(
            CaseReviewer.case_id == appeal.case_id,
            CaseReviewer.reviewer_id == reviewer.id,
            CaseReviewer.conflict_declared.is_(True),
        )
    )
    if conflict:
        raise HTTPException(status_code=409, detail="A conflicted reviewer cannot resolve this appeal")
    appeal.outcome = payload.outcome
    appeal.status = "resolved"
    appeal.resolved_at = datetime.now(timezone.utc)
    old_status = appeal.case.status
    appeal.case.status = "closed"
    appeal.case.closed_at = appeal.resolved_at
    db.add(CaseEvent(
        case_id=appeal.case_id,
        actor_id=user.id,
        event_type="appeal_resolved",
        from_state=old_status,
        to_state=appeal.case.status,
        details=f"{payload.outcome}: {payload.rationale}",
    ))
    db.commit()
    return {"appeal_key": appeal.appeal_key, "outcome": appeal.outcome, "status": appeal.status}
