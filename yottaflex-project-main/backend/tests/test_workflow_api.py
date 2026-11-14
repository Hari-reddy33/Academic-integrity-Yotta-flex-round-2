from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main
from app.db.session import Base, get_db
from app.models import (
    Assessment, CaseReviewer, IntegrityCase, IntegrityRule, Learner, Reviewer,
    SimilarityReport, Submission, User,
)
from app.core.security import hash_password


@pytest.fixture
def client(monkeypatch):
    test_engine = create_engine(
        "sqlite+pysqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(test_engine)
    test_session = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)
    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[get_db] = override_get_db
    now = datetime.now(timezone.utc)
    with test_session.begin() as db:
        demo_users = [
            User(id=1, email="learner@test.local", full_name="Learner", role="learner",
                 password_hash=hash_password("demo1234"), active=True),
            User(id=2, email="reviewer1@test.local", full_name="Reviewer One", role="reviewer",
                 password_hash=hash_password("demo1234"), active=True),
            User(id=3, email="reviewer2@test.local", full_name="Reviewer Two", role="reviewer",
                 password_hash=hash_password("demo1234"), active=True),
            User(id=4, email="reviewer3@test.local", full_name="Reviewer Three", role="reviewer",
                 password_hash=hash_password("demo1234"), active=True),
            User(id=5, email="admin@test.local", full_name="Admin", role="academic_admin",
                 password_hash=hash_password("demo1234"), active=True),
            User(id=6, email="instructor@test.local", full_name="Instructor", role="instructor",
                 password_hash=hash_password("demo1234"), active=True),
            User(id=7, email="learner2@test.local", full_name="Second Learner", role="learner",
                 password_hash=hash_password("demo1234"), active=True),
        ]
        db.add_all(demo_users)
        db.add_all([
            Learner(id=1, learner_key="LRN-2026-000001", display_name="Test Learner",
                    program="Test Program", user_id=1),
            Learner(id=2, learner_key="LRN-2026-000002", display_name="Second Test Learner",
                    program="Test Program", user_id=7),
            Assessment(id=1, assessment_key="ASM-2026-0001", title="Test Assessment",
                       course_code="TEST-01", due_at=now + timedelta(days=1)),
            IntegrityRule(id=1, rule_key="RULE-2026-001", name="Review threshold",
                          review_threshold=0.72, effective_from=now - timedelta(days=1),
                          effective_to=None, description="Human review only."),
            Reviewer(id=1, reviewer_key="REV-001", user_id=2, department="Test"),
            Reviewer(id=2, reviewer_key="REV-002", user_id=3, department="Test"),
            Reviewer(id=3, reviewer_key="REV-003", user_id=4, department="Test"),
        ])
        db.add(Submission(id=1, submission_key="SUB-2026-000001", learner_id=1, assessment_id=1,
                          submitted_at=now, content_ref="synthetic://test"))
        db.add(SimilarityReport(
            id=1, report_key="SIM-SUB-2026-000001-01", submission_id=1, score=0.81,
            quoted_overlap=0.1, template_overlap=0.05, threshold=0.72, review_flag=True,
            generated_at=now,
        ))
        db.add(IntegrityCase(
            id=1, case_key="INT-2026-000001", submission_id=1, report_id=1,
            status="under_review", created_at=now, due_at=now + timedelta(days=10),
        ))
        db.add(CaseReviewer(
            id=1, case_id=1, reviewer_id=2, assigned_at=now, conflict_declared=True,
        ))

    with TestClient(main.app) as test_client:
        yield test_client
    main.app.dependency_overrides.clear()
    test_engine.dispose()


def token_for(client, email):
    response = client.post("/auth/token", data={"username": email, "password": "demo1234"})
    assert response.status_code == 200
    return response.json()["access_token"]


def test_auth_requires_valid_password_and_returns_authenticated_user(client):
    invalid = client.post(
        "/auth/token",
        data={"username": "learner@test.local", "password": "incorrect"},
    )
    assert invalid.status_code == 401

    token = token_for(client, "learner@test.local")
    current_user = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert current_user.status_code == 200
    assert current_user.json()["email"] == "learner@test.local"
    assert current_user.json()["role"] == "learner"


def test_submission_similarity_case_review_and_appeal_work_end_to_end(client):
    original_text = (
        "Community gardens give neighbors a shared place to grow fresh produce. "
        "Residents exchange tools and gardening knowledge, turn unused lots into green space, "
        "and build stronger connections within their community."
    )
    matching_text = (
        "Community gardens give neighbors a shared place to grow fresh produce. "
        "Residents exchange tools and gardening knowledge, turn unused lots into green space, "
        "and build stronger connections within their community."
    )
    learner_one = token_for(client, "learner@test.local")
    learner_two = token_for(client, "learner2@test.local")
    instructor = token_for(client, "instructor@test.local")
    admin = token_for(client, "admin@test.local")
    reviewer_one = token_for(client, "reviewer1@test.local")
    independent_reviewer = token_for(client, "reviewer3@test.local")
    assert client.get(
        "/dashboard", headers={"Authorization": f"Bearer {learner_one}"}
    ).status_code == 200

    first = client.post(
        "/submissions",
        json={"assessment_id": 1, "content_text": original_text},
        headers={"Authorization": f"Bearer {learner_one}"},
    )
    assert first.status_code == 201
    first_result = first.json()
    assert first_result["analysis_status"] == "complete"
    assert first_result["comparison_available"] is False
    assert first_result["review_flag"] is False
    assert first_result["case_key"] is None

    second = client.post(
        "/submissions",
        json={"assessment_id": 1, "content_text": matching_text},
        headers={"Authorization": f"Bearer {learner_two}"},
    )
    assert second.status_code == 201
    second_result = second.json()
    assert second_result["analysis_status"] == "complete"
    assert second_result["comparison_available"] is True
    assert second_result["review_flag"] is True
    case_key = second_result["case_key"]
    assert case_key

    staff_submissions = client.get(
        "/submissions", headers={"Authorization": f"Bearer {instructor}"}
    )
    assert staff_submissions.status_code == 200
    submitted_row = next(
        row for row in staff_submissions.json()
        if row["submission_key"] == second_result["submission_key"]
    )
    assert submitted_row["review_flag"] is True
    assert submitted_row["matching_submission_key"] == first_result["submission_key"]

    report_rows = client.get(
        "/reports", headers={"Authorization": f"Bearer {instructor}"}
    ).json()
    report = next(row for row in report_rows if row["submission_key"] == second_result["submission_key"])
    assert report["case_key"] == case_key
    assert report["matching_submission_key"] == first_result["submission_key"]

    assignment = client.post(
        f"/cases/{case_key}/reviewers",
        json={"reviewer_id": 1},
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert assignment.status_code == 201
    case_detail = client.get(
        f"/cases/{case_key}", headers={"Authorization": f"Bearer {reviewer_one}"}
    ).json()
    assert case_detail["submission"]["content_text"] == matching_text
    assert case_detail["similarity"]["matching_submission_key"] == first_result["submission_key"]
    assert case_detail["similarity"]["matching_content_text"] == original_text

    source_access = client.get(
        f"/submissions/{first_result['submission_key']}",
        headers={"Authorization": f"Bearer {reviewer_one}"},
    )
    assert source_access.status_code == 200
    assert source_access.json()["content_text"] == original_text

    decision = client.post(
        f"/cases/{case_key}/decisions",
        json={
            "outcome": "substantiated",
            "rationale": "The submissions share extensive uncited language and context was reviewed.",
        },
        headers={"Authorization": f"Bearer {reviewer_one}"},
    )
    assert decision.status_code == 201

    learner_case = client.get(
        f"/cases/{case_key}", headers={"Authorization": f"Bearer {learner_two}"}
    ).json()
    assert learner_case["status"] == "decided"
    assert "matching_submission_key" not in learner_case["similarity"]
    learner_cases = client.get(
        "/cases", headers={"Authorization": f"Bearer {learner_two}"}
    ).json()
    assert next(row for row in learner_cases if row["case_key"] == case_key)["submission_key"] == (
        second_result["submission_key"]
    )
    appeal = client.post(
        f"/cases/{case_key}/appeals",
        json={"reason": "I request an independent review of the submitted work and cited context."},
        headers={"Authorization": f"Bearer {learner_two}"},
    )
    assert appeal.status_code == 201

    appeal_key = appeal.json()["appeal_key"]
    unassigned_resolution = client.post(
        f"/appeals/{appeal_key}/resolve",
        json={
            "outcome": "overturned",
            "rationale": "An independent reviewer must be assigned before resolving this appeal.",
        },
        headers={"Authorization": f"Bearer {independent_reviewer}"},
    )
    assert unassigned_resolution.status_code == 409
    appeal_assignment = client.post(
        f"/appeals/{appeal_key}/assign",
        json={"reviewer_id": 3},
        headers={"Authorization": f"Bearer {admin}"},
    )
    assert appeal_assignment.status_code == 200
    assert appeal_assignment.json()["reviewer_id"] == 3
    assert any(
        row["appeal_key"] == appeal_key
        for row in client.get(
            "/appeals", headers={"Authorization": f"Bearer {independent_reviewer}"}
        ).json()
    )

    resolved = client.post(
        f"/appeals/{appeal_key}/resolve",
        json={
            "outcome": "overturned",
            "rationale": "Independent review found the original finding was not sufficiently supported.",
        },
        headers={"Authorization": f"Bearer {independent_reviewer}"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"


def test_case_decision_and_appeal_require_independent_unconflicted_review(client):
    learner_token = token_for(client, "learner@test.local")
    reviewer_one_token = token_for(client, "reviewer1@test.local")
    conflicted_token = token_for(client, "reviewer2@test.local")
    independent_token = token_for(client, "reviewer3@test.local")
    admin_token = token_for(client, "admin@test.local")

    detail = client.get("/cases/INT-2026-000001", headers={"Authorization": f"Bearer {learner_token}"})
    assert detail.status_code == 200
    assert detail.json()["similarity"]["review_flag"] is True
    assert "issue_type" not in detail.json()

    blocked_decision = client.post(
        "/cases/INT-2026-000001/decisions",
        json={"outcome": "substantiated", "rationale": "This conflicted reviewer cannot submit a decision."},
        headers={"Authorization": f"Bearer {conflicted_token}"},
    )
    assert blocked_decision.status_code == 409
    unassigned_access = client.get(
        "/cases/INT-2026-000001",
        headers={"Authorization": f"Bearer {reviewer_one_token}"},
    )
    assert unassigned_access.status_code == 403

    assigned = client.post(
        "/cases/INT-2026-000001/reviewers",
        json={"reviewer_id": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert assigned.status_code == 201
    decision = client.post(
        "/cases/INT-2026-000001/decisions",
        json={"outcome": "not_substantiated", "rationale": "The contextual evidence does not establish misconduct."},
        headers={"Authorization": f"Bearer {reviewer_one_token}"},
    )
    assert decision.status_code == 201
    evidence = client.post(
        "/cases/INT-2026-000001/evidence",
        json={
            "kind": "source_context",
            "description": "A source passage was checked against the assignment context.",
            "source_ref": "synthetic://test/source",
        },
        headers={"Authorization": f"Bearer {reviewer_one_token}"},
    )
    assert evidence.status_code == 201

    appeal = client.post(
        "/cases/INT-2026-000001/appeals",
        json={"reason": "I request review of the decision and the cited context."},
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert appeal.status_code == 201
    appeal_row = next(
        row for row in client.get(
            "/appeals", headers={"Authorization": f"Bearer {admin_token}"}
        ).json()
        if row["appeal_key"] == appeal.json()["appeal_key"]
    )
    assert appeal_row["conflicted_reviewer_ids"] == [2]

    same_reviewer = client.post(
        "/appeals/APL-INT-2026-000001-01/resolve",
        json={"outcome": "upheld", "rationale": "This reviewer made the original case decision."},
        headers={"Authorization": f"Bearer {reviewer_one_token}"},
    )
    assert same_reviewer.status_code == 409
    conflicted_resolution = client.post(
        "/appeals/APL-INT-2026-000001-01/resolve",
        json={"outcome": "upheld", "rationale": "A conflicted reviewer must not resolve this appeal."},
        headers={"Authorization": f"Bearer {conflicted_token}"},
    )
    assert conflicted_resolution.status_code == 409

    blocked_assignment = client.post(
        "/appeals/APL-INT-2026-000001-01/assign",
        json={"reviewer_id": 2},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert blocked_assignment.status_code == 409
    original_reviewer_assignment = client.post(
        "/appeals/APL-INT-2026-000001-01/assign",
        json={"reviewer_id": 1},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert original_reviewer_assignment.status_code == 409
    independent_assignment = client.post(
        "/appeals/APL-INT-2026-000001-01/assign",
        json={"reviewer_id": 3},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert independent_assignment.status_code == 200
    assert client.get(
        "/appeals", headers={"Authorization": f"Bearer {reviewer_one_token}"}
    ).json() == []

    resolved = client.post(
        "/appeals/APL-INT-2026-000001-01/resolve",
        json={"outcome": "overturned", "rationale": "Independent review found the initial finding unsupported."},
        headers={"Authorization": f"Bearer {independent_token}"},
    )
    assert resolved.status_code == 200
    final = client.get("/cases/INT-2026-000001", headers={"Authorization": f"Bearer {learner_token}"})
    assert final.json()["status"] == "closed"
    assert [event["event_type"] for event in final.json()["timeline"]][-3:] == [
        "appeal_submitted",
        "appeal_reviewer_assigned",
        "appeal_resolved",
    ]
    assert any(event["event_type"] == "evidence_added" for event in final.json()["timeline"])


def test_similarity_analysis_is_transient_and_contextual(client):
    token = token_for(client, "reviewer1@test.local")
    response = client.post(
        "/similarity/compare",
        json={
            "text_a": "A fair review examines source context, quotations, shared templates and attribution before deciding.",
            "text_b": "A fair review examines source context, quotations, shared templates and attribution before deciding.",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["score"] == 1.0
    assert response.json()["review_flag"] is True
    assert response.json()["input_retained"] is False


def test_learner_can_submit_text_but_cannot_access_staff_workspaces(client):
    learner_token = token_for(client, "learner@test.local")
    instructor_token = token_for(client, "instructor@test.local")
    assignment_text = (
        "This is a sufficiently long synthetic assignment passage submitted by the learner "
        "for the selected assessment in the local development workflow."
    )

    submitted = client.post(
        "/submissions",
        json={"assessment_id": 1, "content_text": assignment_text},
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert submitted.status_code == 201
    assert submitted.json()["submission_key"] == "SUB-2026-000002"
    assert submitted.json()["analysis_status"] == "complete"
    assert submitted.json()["comparison_available"] is False
    assert submitted.json()["review_flag"] is False

    own_submissions = client.get(
        "/submissions",
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert own_submissions.status_code == 200
    assert own_submissions.json()[0]["text_preview"].startswith("This is a sufficiently long")
    assert own_submissions.json()[0]["report_key"] == submitted.json()["report_key"]
    own_detail = client.get(
        f"/submissions/{submitted.json()['submission_key']}",
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert own_detail.status_code == 200
    assert own_detail.json()["content_text"] == assignment_text

    staff_submissions = client.get(
        "/submissions",
        headers={"Authorization": f"Bearer {instructor_token}"},
    )
    assert staff_submissions.status_code == 200
    assert submitted.json()["submission_key"] in {
        row["submission_key"] for row in staff_submissions.json()
    }

    assert client.get("/reports", headers={"Authorization": f"Bearer {learner_token}"}).status_code == 403
    assert client.get("/reviewers", headers={"Authorization": f"Bearer {learner_token}"}).status_code == 403
    assert client.get("/appeals", headers={"Authorization": f"Bearer {instructor_token}"}).status_code == 403
    assert client.post(
        "/submissions",
        json={"assessment_id": 1, "content_text": assignment_text},
        headers={"Authorization": f"Bearer {instructor_token}"},
    ).status_code == 403
    assert client.post(
        "/cases/INT-2026-000001/decisions",
        json={"outcome": "substantiated", "rationale": "An instructor cannot issue a case decision."},
        headers={"Authorization": f"Bearer {instructor_token}"},
    ).status_code == 403
