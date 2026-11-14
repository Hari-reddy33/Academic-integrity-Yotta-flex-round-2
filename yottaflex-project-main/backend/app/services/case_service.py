from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import CaseReviewer, IntegrityCase, Learner, Reviewer, Submission, User


def load_case(db: Session, case_key: str) -> IntegrityCase:
    case = db.execute(
        select(IntegrityCase).where(IntegrityCase.case_key == case_key).options(
            joinedload(IntegrityCase.assignments).joinedload(CaseReviewer.reviewer),
            joinedload(IntegrityCase.evidence),
            joinedload(IntegrityCase.decisions),
            joinedload(IntegrityCase.appeals),
            joinedload(IntegrityCase.events),
        )
    ).unique().scalar_one_or_none()
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


def ensure_case_access(case: IntegrityCase, user: User, db: Session):
    if user.role == "learner":
        owns_case = db.scalar(
            select(Learner.id).join(Submission).where(
                Submission.id == case.submission_id, Learner.user_id == user.id
            )
        )
        if owns_case is None:
            raise HTTPException(status_code=403, detail="You may only access your own cases")
    elif user.role == "reviewer":
        assignment = db.scalar(
            select(CaseReviewer.id).join(Reviewer).where(
                CaseReviewer.case_id == case.id, Reviewer.user_id == user.id
            )
        )
        if assignment is None:
            raise HTTPException(status_code=403, detail="You may only access cases assigned to you")


def case_summary(case: IntegrityCase):
    return {
        "id": case.id,
        "case_key": case.case_key,
        "submission_key": case.submission.submission_key,
        "status": case.status,
        "created_at": case.created_at,
        "due_at": case.due_at,
        "evidence_count": len(case.evidence),
        "decision_count": len(case.decisions),
        "appeal_status": case.appeals[0].status if case.appeals else None,
    }


def case_detail(case: IntegrityCase, matching_submission: Submission | None = None):
    similarity = {
        "score": case.report.score,
        "quoted_overlap": case.report.quoted_overlap,
        "template_overlap": case.report.template_overlap,
        "threshold": case.report.threshold,
        "review_flag": case.report.review_flag,
    }
    if matching_submission is not None:
        similarity.update({
            "matching_submission_key": matching_submission.submission_key,
            "matching_content_text": matching_submission.content_text or "",
        })
    return {
        **case_summary(case),
        "submission": {
            "submission_key": case.submission.submission_key,
            "learner_key": case.submission.learner.learner_key,
            "assessment": case.submission.assessment.title,
            "submitted_at": case.submission.submitted_at,
            "content_text": case.submission.content_text or "",
        },
        "similarity": similarity,
        "reviewers": [
            {
                "id": assignment.reviewer.id,
                "user_id": assignment.reviewer.user_id,
                "name": assignment.reviewer.user.full_name,
                "conflict_declared": assignment.conflict_declared,
            }
            for assignment in case.assignments
        ],
        "evidence": [
            {
                "evidence_key": evidence.evidence_key,
                "kind": evidence.kind,
                "description": evidence.description,
                "source_ref": evidence.source_ref,
                "added_at": evidence.added_at,
            }
            for evidence in sorted(case.evidence, key=lambda item: item.added_at)
        ],
        "decisions": [
            {
                "decision_key": decision.decision_key,
                "outcome": decision.outcome,
                "rationale": decision.rationale,
                "decided_at": decision.decided_at,
            }
            for decision in sorted(case.decisions, key=lambda item: item.decided_at)
        ],
        "appeals": [
            {
                "appeal_key": appeal.appeal_key,
                "reason": appeal.reason,
                "status": appeal.status,
                "outcome": appeal.outcome,
                "submitted_at": appeal.submitted_at,
                "resolved_at": appeal.resolved_at,
            }
            for appeal in case.appeals
        ],
        "timeline": [
            {
                "event_type": event.event_type,
                "from_state": event.from_state,
                "to_state": event.to_state,
                "details": event.details,
                "created_at": event.created_at,
            }
            for event in sorted(case.events, key=lambda item: item.created_at)
        ],
    }
