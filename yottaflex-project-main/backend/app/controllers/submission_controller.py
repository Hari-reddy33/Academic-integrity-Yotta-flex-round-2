from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select, text
from sqlalchemy.orm import Session, aliased

from app.core.roles import STAFF_ROLES
from app.core.security import get_current_user, require_roles
from app.db.session import get_db
from app.models import (
    Assessment,
    CaseReviewer,
    IntegrityCase,
    Learner,
    Reviewer,
    SimilarityReport,
    Submission,
    User,
)
from app.schemas import SubmissionCreate
from app.services.submission_service import analyze_submission

router = APIRouter(prefix="/submissions", tags=["learner submissions"])


def get_learner(db: Session, user: User) -> Learner:
    learner = db.scalar(select(Learner).where(Learner.user_id == user.id))
    if learner is None:
        raise HTTPException(status_code=403, detail="No learner profile is linked to this account")
    return learner


def submission_summary(
    submission: Submission,
    assessment: Assessment,
    learner: Learner,
    report: SimilarityReport | None,
    case: IntegrityCase | None,
    matching_submission: Submission | None,
    include_match: bool,
) -> dict:
    content = submission.content_text or ""
    return {
        "submission_key": submission.submission_key,
        "learner_key": learner.learner_key,
        "assessment_key": assessment.assessment_key,
        "assessment_title": assessment.title,
        "course_code": assessment.course_code,
        "submitted_at": submission.submitted_at,
        "analysis_status": submission.analysis_status,
        "text_preview": content[:220] + ("…" if len(content) > 220 else ""),
        "report_key": report.report_key if report else None,
        "similarity_score": report.score if report else None,
        "threshold": report.threshold if report else None,
        "review_flag": report.review_flag if report else None,
        "comparison_available": bool(report and report.matching_submission_id),
        "matching_submission_key": (
            matching_submission.submission_key
            if include_match and matching_submission
            else None
        ),
        "case_key": case.case_key if case else None,
        "case_status": case.status if case else None,
    }


def submission_query():
    matching_submission = aliased(Submission)
    query = (
        select(
            Submission,
            Assessment,
            Learner,
            SimilarityReport,
            IntegrityCase,
            matching_submission,
        )
        .join(Assessment, Submission.assessment_id == Assessment.id)
        .join(Learner, Submission.learner_id == Learner.id)
        .outerjoin(SimilarityReport, SimilarityReport.submission_id == Submission.id)
        .outerjoin(IntegrityCase, IntegrityCase.submission_id == Submission.id)
        .outerjoin(
            matching_submission,
            SimilarityReport.matching_submission_id == matching_submission.id,
        )
    )
    return query, matching_submission


@router.get("/assessments")
def list_assessments(
    user: User = Depends(require_roles("learner")),
    db: Session = Depends(get_db),
):
    get_learner(db, user)
    assessments = db.scalars(select(Assessment).order_by(Assessment.due_at, Assessment.id)).all()
    return [
        {
            "id": assessment.id,
            "assessment_key": assessment.assessment_key,
            "title": assessment.title,
            "course_code": assessment.course_code,
            "due_at": assessment.due_at,
        }
        for assessment in assessments
    ]


@router.get("")
def list_submissions(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query, _ = submission_query()
    include_match = user.role != "learner"
    if user.role == "learner":
        learner = get_learner(db, user)
        query = query.where(Submission.learner_id == learner.id)
    elif user.role == "reviewer":
        query = query.where(
            IntegrityCase.id.in_(
                select(CaseReviewer.case_id)
                .join(Reviewer)
                .where(Reviewer.user_id == user.id)
            )
        )
    elif user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Your role cannot view submissions")

    rows = db.execute(
        query.order_by(Submission.submitted_at.desc(), Submission.id.desc())
        .limit(limit)
        .offset(offset)
    )
    return [
        submission_summary(*row, include_match=include_match)
        for row in rows
    ]


@router.post("", status_code=201)
def submit_assignment(
    payload: SubmissionCreate,
    user: User = Depends(require_roles("learner")),
    db: Session = Depends(get_db),
):
    learner = get_learner(db, user)
    assessment = db.get(Assessment, payload.assessment_id)
    if assessment is None:
        raise HTTPException(status_code=404, detail="Assessment not found")

    if db.get_bind().dialect.name == "postgresql":
        submission_id = db.scalar(text("SELECT nextval(pg_get_serial_sequence('submissions', 'id'))"))
    else:
        submission_id = (db.scalar(select(func.max(Submission.id))) or 0) + 1
    if submission_id is None:
        raise RuntimeError("Unable to allocate a submission ID from PostgreSQL.")

    now = datetime.now(timezone.utc)
    submission = Submission(
        id=submission_id,
        submission_key=f"SUB-2026-{submission_id:06d}",
        learner_id=learner.id,
        assessment_id=assessment.id,
        submitted_at=now,
        content_ref=f"submission://SUB-2026-{submission_id:06d}",
        content_text=payload.content_text,
        analysis_status="pending",
    )
    try:
        db.add(submission)
        db.flush()
        report = analyze_submission(db, submission, user.id)
        db.commit()
    except Exception:
        db.rollback()
        raise

    case = db.scalar(select(IntegrityCase).where(IntegrityCase.submission_id == submission.id))
    return {
        "submission_key": submission.submission_key,
        "assessment_key": assessment.assessment_key,
        "assessment_title": assessment.title,
        "submitted_at": submission.submitted_at,
        "analysis_status": submission.analysis_status,
        "report_key": report.report_key,
        "similarity_score": report.score,
        "threshold": report.threshold,
        "review_flag": report.review_flag,
        "case_key": case.case_key if case else None,
        "comparison_available": bool(report.matching_submission_id),
    }


@router.get("/{submission_key}")
def get_submission(
    submission_key: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query, _ = submission_query()
    row = db.execute(query.where(Submission.submission_key == submission_key)).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    submission, assessment, learner, report, case, matching_submission = row

    if user.role == "learner":
        if learner.user_id != user.id:
            raise HTTPException(status_code=403, detail="You may only view your own submissions")
    elif user.role == "reviewer":
        assigned = db.scalar(
            select(CaseReviewer.id)
            .join(IntegrityCase, CaseReviewer.case_id == IntegrityCase.id)
            .join(SimilarityReport, SimilarityReport.id == IntegrityCase.report_id)
            .join(Reviewer, CaseReviewer.reviewer_id == Reviewer.id)
            .where(
                Reviewer.user_id == user.id,
                or_(
                    IntegrityCase.submission_id == submission.id,
                    SimilarityReport.matching_submission_id == submission.id,
                ),
            )
        )
        if assigned is None:
            raise HTTPException(status_code=403, detail="You may only view submissions for assigned cases")
    elif user.role not in STAFF_ROLES:
        raise HTTPException(status_code=403, detail="Your role cannot view submissions")

    return {
        **submission_summary(
            submission,
            assessment,
            learner,
            report,
            case,
            matching_submission,
            include_match=user.role != "learner",
        ),
        "content_text": submission.content_text or "",
    }
