import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import (
    CaseEvent,
    IntegrityCase,
    IntegrityRule,
    SimilarityReport,
    Submission,
)
from app.services.similarity import compare_to_candidates


COMPARISON_CANDIDATE_LIMIT = 1000
TOKEN_PATTERN = re.compile(r"(?u)\b\w\w+\b")


def analyze_submission(db: Session, submission: Submission, actor_id: int | None) -> SimilarityReport:
    report = db.scalar(
        select(SimilarityReport).where(SimilarityReport.submission_id == submission.id)
    )
    if report is not None:
        submission.analysis_status = "complete"
        return report

    now = datetime.now(timezone.utc)
    rule = db.scalar(
        select(IntegrityRule)
        .where(
            IntegrityRule.effective_from <= now,
            or_(IntegrityRule.effective_to.is_(None), IntegrityRule.effective_to >= now),
        )
        .order_by(IntegrityRule.effective_from.desc())
        .limit(1)
    )
    if rule is None:
        raise RuntimeError("No effective integrity review threshold is configured.")

    candidate_rows = db.execute(
        select(Submission.id, Submission.content_text)
        .where(
            Submission.assessment_id == submission.assessment_id,
            Submission.learner_id != submission.learner_id,
            Submission.id != submission.id,
            Submission.submitted_at <= submission.submitted_at,
            Submission.content_text.is_not(None),
        )
        .order_by(Submission.submitted_at.desc(), Submission.id.desc())
        .limit(COMPARISON_CANDIDATE_LIMIT)
    ).all()
    comparable_rows = [
        row for row in candidate_rows
        if row.content_text and TOKEN_PATTERN.search(row.content_text)
    ]
    score, match_index = compare_to_candidates(
        submission.content_text or "",
        [row.content_text for row in comparable_rows],
    )
    matching_submission_id = (
        comparable_rows[match_index].id if match_index is not None else None
    )
    review_flag = score >= rule.review_threshold
    report = SimilarityReport(
        report_key=f"SIM-{submission.submission_key}-01",
        submission_id=submission.id,
        score=score,
        quoted_overlap=None,
        template_overlap=None,
        threshold=rule.review_threshold,
        review_flag=review_flag,
        generated_at=now,
        matching_submission_id=matching_submission_id,
    )
    db.add(report)
    submission.analysis_status = "complete"
    db.flush()

    if review_flag:
        case = IntegrityCase(
            case_key=f"INT-2026-{submission.id:06d}",
            submission_id=submission.id,
            report_id=report.id,
            status="open",
            created_at=now,
            due_at=now + timedelta(days=14),
        )
        db.add(case)
        db.flush()
        if actor_id is None:
            raise RuntimeError("A learner account is required to record the review-flag event.")
        db.add(CaseEvent(
            case_id=case.id,
            actor_id=actor_id,
            event_type="similarity_flagged",
            from_state=None,
            to_state="open",
            details=(
                f"Similarity score {score:.4f} reached the review threshold "
                f"{rule.review_threshold:.4f}; human review is required."
            ),
            created_at=now,
        ))

    return report


def analyze_pending_submissions(db: Session) -> int:
    pending = db.scalars(
        select(Submission)
        .where(Submission.analysis_status == "pending")
        .order_by(Submission.submitted_at, Submission.id)
    ).all()
    for submission in pending:
        analyze_submission(db, submission, submission.learner.user_id)
        db.commit()
    return len(pending)
