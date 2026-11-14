"""SQLAlchemy ORM entities for the application."""

from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(32), index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Learner(Base):
    __tablename__ = "learners"
    id: Mapped[int] = mapped_column(primary_key=True)
    learner_key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(160))
    program: Mapped[str] = mapped_column(String(100))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), unique=True, nullable=True)
    submissions: Mapped[list["Submission"]] = relationship(back_populates="learner")


class Assessment(Base):
    __tablename__ = "assessments"
    id: Mapped[int] = mapped_column(primary_key=True)
    assessment_key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(200))
    course_code: Mapped[str] = mapped_column(String(24))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    submissions: Mapped[list["Submission"]] = relationship(back_populates="assessment")


class IntegrityRule(Base):
    __tablename__ = "integrity_rules"
    id: Mapped[int] = mapped_column(primary_key=True)
    rule_key: Mapped[str] = mapped_column(String(32), unique=True)
    name: Mapped[str] = mapped_column(String(120))
    review_threshold: Mapped[float] = mapped_column(Float)
    effective_from: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    effective_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    description: Mapped[str] = mapped_column(Text)


class Submission(Base):
    __tablename__ = "submissions"
    id: Mapped[int] = mapped_column(primary_key=True)
    submission_key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    learner_id: Mapped[int] = mapped_column(ForeignKey("learners.id"))
    assessment_id: Mapped[int] = mapped_column(ForeignKey("assessments.id"))
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    content_ref: Mapped[str] = mapped_column(String(120))
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_status: Mapped[str] = mapped_column(String(24), default="pending", server_default="pending")
    learner: Mapped[Learner] = relationship(back_populates="submissions")
    assessment: Mapped[Assessment] = relationship(back_populates="submissions")
    report: Mapped["SimilarityReport | None"] = relationship(
        back_populates="submission",
        uselist=False,
        foreign_keys="SimilarityReport.submission_id",
    )


class SimilarityReport(Base):
    __tablename__ = "similarity_reports"
    id: Mapped[int] = mapped_column(primary_key=True)
    report_key: Mapped[str] = mapped_column(String(48), unique=True, index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), unique=True)
    score: Mapped[float] = mapped_column(Float)
    quoted_overlap: Mapped[float | None] = mapped_column(Float, nullable=True)
    template_overlap: Mapped[float | None] = mapped_column(Float, nullable=True)
    threshold: Mapped[float] = mapped_column(Float)
    review_flag: Mapped[bool] = mapped_column(Boolean, index=True)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    matching_submission_id: Mapped[int | None] = mapped_column(
        ForeignKey(
            "submissions.id",
            name="fk_similarity_reports_matching_submission",
        ),
        nullable=True,
        index=True,
    )
    submission: Mapped[Submission] = relationship(
        back_populates="report",
        foreign_keys=[submission_id],
    )


class Reviewer(Base):
    __tablename__ = "reviewers"
    id: Mapped[int] = mapped_column(primary_key=True)
    reviewer_key: Mapped[str] = mapped_column(String(32), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    department: Mapped[str] = mapped_column(String(100))
    user: Mapped[User] = relationship()
    assignments: Mapped[list["CaseReviewer"]] = relationship(back_populates="reviewer")


class IntegrityCase(Base):
    __tablename__ = "cases"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_key: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), unique=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("similarity_reports.id"), unique=True)
    status: Mapped[str] = mapped_column(String(32), default="open", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    submission: Mapped[Submission] = relationship()
    report: Mapped[SimilarityReport] = relationship()
    assignments: Mapped[list["CaseReviewer"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    evidence: Mapped[list["EvidenceItem"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    decisions: Mapped[list["Decision"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    appeals: Mapped[list["Appeal"]] = relationship(back_populates="case", cascade="all, delete-orphan")
    events: Mapped[list["CaseEvent"]] = relationship(back_populates="case", cascade="all, delete-orphan")


class CaseReviewer(Base):
    __tablename__ = "case_reviewers"
    __table_args__ = (UniqueConstraint("case_id", "reviewer_id", name="uq_case_reviewer"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"))
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("reviewers.id"))
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    conflict_declared: Mapped[bool] = mapped_column(Boolean, default=False)
    case: Mapped[IntegrityCase] = relationship(back_populates="assignments")
    reviewer: Mapped[Reviewer] = relationship(back_populates="assignments")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    evidence_key: Mapped[str] = mapped_column(String(48), unique=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    kind: Mapped[str] = mapped_column(String(48))
    description: Mapped[str] = mapped_column(Text)
    source_ref: Mapped[str] = mapped_column(String(160))
    added_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    case: Mapped[IntegrityCase] = relationship(back_populates="evidence")


class Decision(Base):
    __tablename__ = "decisions"
    id: Mapped[int] = mapped_column(primary_key=True)
    decision_key: Mapped[str] = mapped_column(String(32), unique=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("reviewers.id"))
    outcome: Mapped[str] = mapped_column(String(32))
    rationale: Mapped[str] = mapped_column(Text)
    decided_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    reviewer: Mapped[Reviewer] = relationship()
    case: Mapped[IntegrityCase] = relationship(back_populates="decisions")


class Appeal(Base):
    __tablename__ = "appeals"
    id: Mapped[int] = mapped_column(primary_key=True)
    appeal_key: Mapped[str] = mapped_column(String(40), unique=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    appellant_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    reason: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    independent_reviewer_id: Mapped[int | None] = mapped_column(ForeignKey("reviewers.id"), nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(32), nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    case: Mapped[IntegrityCase] = relationship(back_populates="appeals")


class CaseEvent(Base):
    __tablename__ = "case_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    case_id: Mapped[int] = mapped_column(ForeignKey("cases.id"), index=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    event_type: Mapped[str] = mapped_column(String(48))
    from_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    to_state: Mapped[str | None] = mapped_column(String(32), nullable=True)
    details: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    case: Mapped[IntegrityCase] = relationship(back_populates="events")

