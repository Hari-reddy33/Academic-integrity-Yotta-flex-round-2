from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, aliased

from app.db.session import get_db
from app.models import (
    Appeal,
    Assessment,
    CaseReviewer,
    IntegrityCase,
    Learner,
    Reviewer,
    SimilarityReport,
    Submission,
    User,
)
from app.core.roles import STAFF_ROLES
from app.core.security import get_current_user, require_roles

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    cases_query = select(func.count(IntegrityCase.id))
    if user.role == "learner":
        cases_query = cases_query.join(Submission).join(Learner).where(Learner.user_id == user.id)
    elif user.role == "reviewer":
        cases_query = cases_query.where(
            IntegrityCase.id.in_(
                select(CaseReviewer.case_id).join(Reviewer).where(Reviewer.user_id == user.id)
            )
        )

    active_statuses = ("open", "under_review", "appealed")
    open_query = select(func.count(IntegrityCase.id)).where(IntegrityCase.status.in_(active_statuses))
    if user.role == "learner":
        open_query = open_query.join(Submission).join(Learner).where(Learner.user_id == user.id)
    elif user.role == "reviewer":
        open_query = open_query.where(
            IntegrityCase.id.in_(
                select(CaseReviewer.case_id).join(Reviewer).where(Reviewer.user_id == user.id)
            )
        )

    flagged_query = select(func.count(SimilarityReport.id)).where(SimilarityReport.review_flag.is_(True))
    appeals_query = select(func.count(Appeal.id)).where(Appeal.status == "pending")
    if user.role == "learner":
        flagged_query = flagged_query.join(
            Submission, SimilarityReport.submission_id == Submission.id
        ).join(Learner).where(Learner.user_id == user.id)
        appeals_query = appeals_query.join(IntegrityCase).join(Submission).join(Learner).where(
            Learner.user_id == user.id
        )
    elif user.role == "reviewer":
        flagged_query = flagged_query.join(IntegrityCase).join(CaseReviewer).join(Reviewer).where(
            Reviewer.user_id == user.id
        )
        appeals_query = appeals_query.join(IntegrityCase).join(CaseReviewer).join(Reviewer).where(
            Reviewer.user_id == user.id
        )

    return {
        "total_cases": db.scalar(cases_query) or 0,
        "open_cases": db.scalar(open_query) or 0,
        "flagged_reports": db.scalar(flagged_query) or 0,
        "pending_appeals": db.scalar(appeals_query) or 0,
    }


@router.get("/reports")
def list_reports(
    limit: int = Query(default=100, ge=1, le=1000),
    user: User = Depends(require_roles(*STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    MatchingSubmission = aliased(Submission)
    query = select(SimilarityReport, Submission, Assessment, IntegrityCase).join(
        Submission, SimilarityReport.submission_id == Submission.id
    ).join(Assessment, Submission.assessment_id == Assessment.id).outerjoin(
        IntegrityCase, IntegrityCase.report_id == SimilarityReport.id
    ).outerjoin(
        MatchingSubmission, SimilarityReport.matching_submission_id == MatchingSubmission.id
    )
    if user.role == "reviewer":
        query = query.where(
            IntegrityCase.id.in_(
                select(CaseReviewer.case_id).join(Reviewer).where(Reviewer.user_id == user.id)
            )
        )
    rows = db.execute(
        query.with_only_columns(
            SimilarityReport,
            Submission,
            Assessment,
            IntegrityCase,
            MatchingSubmission,
        )
        .order_by(SimilarityReport.generated_at.desc())
        .limit(limit)
    )
    return [
        {
            "report_key": report.report_key,
            "submission_key": submission.submission_key,
            "assessment": assessment.title,
            "score": report.score,
            "threshold": report.threshold,
            "review_flag": report.review_flag,
            "matching_submission_key": (
                matching_submission.submission_key if matching_submission else None
            ),
            "case_key": case.case_key if case else None,
            "generated_at": report.generated_at,
        }
        for report, submission, assessment, case, matching_submission in rows
    ]
