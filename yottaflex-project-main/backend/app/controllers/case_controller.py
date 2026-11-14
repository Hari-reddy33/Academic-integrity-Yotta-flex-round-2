from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import get_current_user, require_roles
from app.core.roles import ADMIN_ROLES, STAFF_ROLES
from app.db.session import get_db
from app.models import (
    Appeal,
    CaseEvent,
    CaseReviewer,
    Decision,
    EvidenceItem,
    IntegrityCase,
    Learner,
    Reviewer,
    Submission,
    User,
)
from app.schemas import AppealCreate, DecisionCreate, EvidenceCreate, ReviewerAssign
from app.services.case_service import case_detail, case_summary, ensure_case_access, load_case
router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("")
def list_cases(
    status_filter: str | None = Query(default=None, alias="status"),
    q: str | None = None,
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = select(IntegrityCase).options(
        joinedload(IntegrityCase.submission),
        joinedload(IntegrityCase.evidence),
        joinedload(IntegrityCase.decisions),
        joinedload(IntegrityCase.appeals),
    )
    if user.role == "learner":
        query = query.join(Submission).join(Learner).where(Learner.user_id == user.id)
    elif user.role == "reviewer":
        query = query.where(
            IntegrityCase.id.in_(
                select(CaseReviewer.case_id).join(Reviewer).where(Reviewer.user_id == user.id)
            )
        )
    if status_filter:
        query = query.where(IntegrityCase.status == status_filter)
    if q:
        query = query.where(IntegrityCase.case_key.ilike(f"%{q}%"))
    cases = db.scalars(
        query.order_by(IntegrityCase.created_at.desc()).limit(limit).offset(offset)
    ).unique().all()
    return [case_summary(case) for case in cases]


@router.get("/{case_key}")
def get_case(case_key: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    case = load_case(db, case_key)
    ensure_case_access(case, user, db)
    matching_submission = None
    if user.role != "learner" and case.report.matching_submission_id is not None:
        matching_submission = db.get(Submission, case.report.matching_submission_id)
    return case_detail(case, matching_submission)


@router.post("/{case_key}/evidence", status_code=201)
def add_evidence(
    case_key: str,
    payload: EvidenceCreate,
    user: User = Depends(require_roles(*STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    case = load_case(db, case_key)
    ensure_case_access(case, user, db)
    now = datetime.now(timezone.utc)
    evidence = EvidenceItem(
        evidence_key=f"EVD-{case.case_key}-{len(case.evidence) + 1:03d}",
        case_id=case.id,
        kind=payload.kind,
        description=payload.description,
        source_ref=payload.source_ref,
        added_by=user.id,
        added_at=now,
    )
    db.add(evidence)
    db.add(CaseEvent(
        case_id=case.id,
        actor_id=user.id,
        event_type="evidence_added",
        from_state=case.status,
        to_state=case.status,
        details=f"{evidence.evidence_key}: {payload.kind}",
    ))
    db.commit()
    db.refresh(evidence)
    return {"id": evidence.id, "evidence_key": evidence.evidence_key, "added_at": evidence.added_at}


@router.post("/{case_key}/reviewers", status_code=201)
def assign_reviewer(
    case_key: str,
    payload: ReviewerAssign,
    user: User = Depends(require_roles(*ADMIN_ROLES)),
    db: Session = Depends(get_db),
):
    case = load_case(db, case_key)
    reviewer = db.get(Reviewer, payload.reviewer_id)
    if reviewer is None:
        raise HTTPException(status_code=404, detail="Reviewer not found")
    if any(assignment.reviewer_id == reviewer.id for assignment in case.assignments):
        raise HTTPException(status_code=409, detail="Reviewer is already assigned")
    if case.status not in ("open", "under_review"):
        raise HTTPException(status_code=409, detail="Reviewers cannot be assigned after a decision or closure")
    old_status = case.status
    case.status = "under_review"
    db.add(CaseReviewer(case_id=case.id, reviewer_id=reviewer.id, assigned_at=datetime.now(timezone.utc)))
    db.add(CaseEvent(
        case_id=case.id,
        actor_id=user.id,
        event_type="reviewer_assigned",
        from_state=old_status,
        to_state=case.status,
        details=f"Assigned reviewer {reviewer.reviewer_key}",
    ))
    db.commit()
    return {"case_key": case.case_key, "reviewer_id": reviewer.id, "status": case.status}


@router.post("/{case_key}/decisions", status_code=201)
def decide(
    case_key: str,
    payload: DecisionCreate,
    user: User = Depends(require_roles("reviewer")),
    db: Session = Depends(get_db),
):
    case = load_case(db, case_key)
    ensure_case_access(case, user, db)
    assignment = db.scalar(
        select(CaseReviewer).join(Reviewer).where(
            CaseReviewer.case_id == case.id, Reviewer.user_id == user.id
        )
    )
    if assignment is None:
        raise HTTPException(status_code=403, detail="Only an assigned reviewer may decide this case")
    if assignment.conflict_declared:
        raise HTTPException(status_code=409, detail="A conflicted reviewer cannot decide this case")
    if case.status not in ("open", "under_review") or case.decisions:
        raise HTTPException(status_code=409, detail="This case is not awaiting an initial decision")
    reviewer = db.scalar(select(Reviewer).where(Reviewer.user_id == user.id))
    if reviewer is None:
        raise HTTPException(status_code=403, detail="A reviewer profile is required to record a decision")
    decision_id = len(case.decisions) + 1
    decision = Decision(
        decision_key=f"DEC-{case.id:06d}-{decision_id:02d}",
        case_id=case.id,
        reviewer_id=reviewer.id,
        outcome=payload.outcome,
        rationale=payload.rationale,
        decided_at=datetime.now(timezone.utc),
    )
    old_status = case.status
    case.status = "decided"
    db.add(decision)
    db.add(CaseEvent(
        case_id=case.id,
        actor_id=user.id,
        event_type="decision_recorded",
        from_state=old_status,
        to_state=case.status,
        details=f"{payload.outcome}: {payload.rationale}",
    ))
    db.commit()
    return {"decision_key": decision.decision_key, "outcome": decision.outcome, "status": case.status}


@router.post("/{case_key}/appeals", status_code=201)
def submit_appeal(
    case_key: str,
    payload: AppealCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.role not in ("learner", "support", "academic_admin", "platform_admin"):
        raise HTTPException(status_code=403, detail="Your role cannot submit appeals")
    case = load_case(db, case_key)
    ensure_case_access(case, user, db)
    if case.status != "decided" or not case.decisions:
        raise HTTPException(status_code=409, detail="An appeal requires a recorded decision")
    if case.appeals:
        raise HTTPException(status_code=409, detail="An appeal has already been submitted for this case")
    appeal = Appeal(
        appeal_key=f"APL-{case.case_key}-01",
        case_id=case.id,
        appellant_id=user.id,
        reason=payload.reason,
        submitted_at=datetime.now(timezone.utc),
    )
    old_status = case.status
    case.status = "appealed"
    db.add(appeal)
    db.add(CaseEvent(
        case_id=case.id,
        actor_id=user.id,
        event_type="appeal_submitted",
        from_state=old_status,
        to_state=case.status,
        details=payload.reason,
    ))
    db.commit()
    return {"appeal_key": appeal.appeal_key, "status": appeal.status}
