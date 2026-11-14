import hashlib
import json
import random
from datetime import datetime, timedelta, timezone
from typing import Any


SEED = 20261022
PROGRAMS = ("Computer Science", "Biology", "History", "Economics", "Engineering")
ASSESSMENTS = (
    "Research Methods Reflection", "Systems Design Brief", "Evidence-Based Essay",
    "Case Study Analysis", "Laboratory Report",
)


def derive_label(report: dict[str, Any]) -> str:
    if report["quoted_overlap"] >= 0.48 or report["template_overlap"] >= 0.42:
        return "legitimate"
    if (
        report["score"] >= 0.84
        and report["quoted_overlap"] < 0.40
        and report["template_overlap"] < 0.35
    ):
        return "misconduct"
    return "uncertain"


def build_dataset(submissions: int = 10_000, flags: int = 1_000, cases: int = 300, seed: int = SEED) -> dict[str, Any]:
    if not (4 <= cases <= flags <= submissions):
        raise ValueError("Scale must satisfy 4 <= cases <= flags <= submissions.")
    rng = random.Random(seed)
    start = datetime(2026, 1, 1, tzinfo=timezone.utc)
    users = [
        {"id": 1, "email": "learner@demo.local", "full_name": "Alex Learner", "role": "learner"},
        {"id": 2, "email": "instructor@demo.local", "full_name": "Morgan Instructor", "role": "instructor"},
        {"id": 3, "email": "admin@demo.local", "full_name": "Avery Administrator", "role": "academic_admin"},
        {"id": 4, "email": "support@demo.local", "full_name": "Jordan Support", "role": "support"},
        {"id": 5, "email": "platform@demo.local", "full_name": "Taylor Platform Admin", "role": "platform_admin"},
    ]
    reviewers = []
    for index in range(4):
        user_id = len(users) + 1
        users.append({
            "id": user_id, "email": f"reviewer{index + 1}@demo.local",
            "full_name": f"Reviewer {index + 1}", "role": "reviewer",
        })
        reviewers.append({
            "id": index + 1, "reviewer_key": f"REV-{index + 1:03d}", "user_id": user_id,
            "department": ("Humanities", "Sciences", "Engineering", "Social Sciences")[index],
        })
    second_learner_user_id = len(users) + 1
    users.append({
        "id": second_learner_user_id,
        "email": "learner2@demo.local",
        "full_name": "Casey Learner",
        "role": "learner",
    })

    learner_count = min(600, max(25, submissions // 10))
    learners = [
        {
            "id": index + 1, "learner_key": f"LRN-2026-{index + 1:06d}",
            "display_name": f"Synthetic Learner {index + 1:04d}",
            "program": PROGRAMS[index % len(PROGRAMS)],
            "user_id": 1 if index == 0 else second_learner_user_id if index == 1 else None,
        }
        for index in range(learner_count)
    ]
    assessment_rows = [
        {
            "id": index + 1, "assessment_key": f"ASM-2026-{index + 1:04d}",
            "title": ASSESSMENTS[index % len(ASSESSMENTS)],
            "course_code": f"COURSE-{(index % 12) + 1:02d}",
            "due_at": start + timedelta(days=30 + index),
        }
        for index in range(40)
    ]
    rules = [{
        "id": 1, "rule_key": "RULE-2026-001", "name": "Similarity review threshold",
        "review_threshold": 0.72, "effective_from": start,
        "effective_to": None,
        "description": "A score at or above 0.72 creates a human review flag only; it is not a finding of misconduct.",
    }]
    flag_indexes = set(rng.sample(range(1, submissions), flags - 1))
    flag_indexes.add(0)
    flag_indexes = sorted(flag_indexes)
    reports_by_submission: dict[int, dict[str, Any]] = {}
    submission_rows = []
    report_rows = []
    truth_by_submission: dict[int, str] = {}
    for index in range(submissions):
        submission_key = f"SUB-2026-{index + 1:06d}"
        learner_id = 1 if index == 0 else rng.randint(1, learner_count)
        assessment_id = rng.randint(1, len(assessment_rows))
        submitted_at = start + timedelta(days=rng.randint(0, 60), minutes=rng.randint(0, 1439))
        submission_rows.append({
            "id": index + 1, "submission_key": submission_key, "learner_id": learner_id,
            "assessment_id": assessment_id, "submitted_at": submitted_at,
            "content_ref": f"synthetic://submission/{submission_key}",
            "content_text": None, "analysis_status": "complete",
        })
        flagged = index in flag_indexes
        score = round(rng.uniform(0.72, 0.98), 4) if flagged else round(rng.uniform(0.03, 0.7199), 4)
        quoted = round(rng.uniform(0.05, 0.60) if flagged else rng.uniform(0.0, 0.16), 4)
        template = round(rng.uniform(0.03, 0.50) if flagged else rng.uniform(0.0, 0.14), 4)
        report = {
            "id": index + 1, "report_key": f"SIM-{submission_key}-01",
            "submission_id": index + 1, "score": score, "quoted_overlap": quoted,
            "template_overlap": template, "threshold": 0.72, "review_flag": flagged,
            "generated_at": submitted_at + timedelta(minutes=5),
        }
        report_rows.append(report)
        if flagged:
            reports_by_submission[index + 1] = report
            truth_by_submission[index + 1] = derive_label(report)

    case_rows = []
    assignment_rows = []
    evidence_rows = []
    decision_rows = []
    appeal_rows = []
    event_rows = []
    truth_rows = []
    selected_case_submissions = [index + 1 for index in flag_indexes[:cases]]
    success_positions = set()
    for position, submission_id in enumerate(selected_case_submissions, start=1):
        report = reports_by_submission[submission_id]
        has_decision = position != 2 and (position <= 6 or position % 5 != 0)
        if (
            position >= 5
            and has_decision
            and truth_by_submission[submission_id] == "legitimate"
            and report["score"] >= 0.85
            and (report["quoted_overlap"] >= 0.35 or report["template_overlap"] >= 0.30)
        ):
            success_positions.add(position)
            if len(success_positions) == 2:
                break
    for position, submission_id in enumerate((index + 1 for index in flag_indexes[:cases]), start=1):
        case_key = f"INT-2026-{position:06d}"
        report = reports_by_submission[submission_id]
        issue_type = {
            1: "automatic_guilt",
            2: "reviewer_conflict",
            3: "evidence_after_decision",
            4: "appeal_without_independent_review",
        }.get(position, "standard")
        truth = truth_by_submission[submission_id]
        reviewer_id = ((position - 1) % len(reviewers)) + 1
        conflict = position == 2
        has_decision = position != 2 and (position <= 6 or position % 5 != 0)
        appeal_case = (
            position in (4, 5, 6)
            or position in success_positions
            or (position > 6 and position % 13 == 0 and has_decision)
        )
        appeal_success = position in success_positions
        close_without_appeal = has_decision and not appeal_case and position % 17 == 0
        if position == 1:
            status = "decided"
        elif position == 2:
            status = "under_review"
        elif appeal_case:
            status = "closed" if position == 4 or appeal_success else "appealed"
        elif close_without_appeal:
            status = "closed"
        elif has_decision:
            status = "decided"
        else:
            status = "under_review"
        created_at = start + timedelta(days=62, hours=position % 24)
        due_at = created_at + timedelta(days=10)
        closed_at = created_at + timedelta(days=4) if status == "closed" else None
        case_rows.append({
            "id": position, "case_key": case_key, "submission_id": submission_id,
            "report_id": report["id"], "status": status,
            "created_at": created_at, "due_at": due_at, "closed_at": closed_at,
        })
        event_rows.append({
            "case_id": position, "actor_id": 3, "event_type": "case_created",
            "from_state": None, "to_state": "open", "details": "Review opened from similarity flag.",
            "created_at": created_at,
        })
        assignment_rows.append({
            "case_id": position, "reviewer_id": reviewer_id, "assigned_at": created_at + timedelta(minutes=10),
            "conflict_declared": conflict,
        })
        event_rows.append({
            "case_id": position, "actor_id": 3, "event_type": "reviewer_assigned",
            "from_state": "open", "to_state": "under_review",
            "details": f"Assigned {reviewers[reviewer_id - 1]['reviewer_key']}"
            + ("; conflict declared." if conflict else "."),
            "created_at": created_at + timedelta(minutes=10),
        })
        evidence_count = 2 if position != 3 else 3
        for item_index in range(1, evidence_count + 1):
            added_at = created_at + timedelta(hours=item_index)
            if position == 3 and item_index == 3:
                added_at = created_at + timedelta(days=2)
            ev_key = f"EVD-{case_key}-{item_index:03d}"
            evidence_rows.append({
                "id": len(evidence_rows) + 1, "evidence_key": ev_key, "case_id": position,
                "kind": ("similarity_excerpt", "source_context", "review_note")[(item_index - 1) % 3],
                "description": (
                    "Synthetic, non-identifying evidence reference; quoted/template context must be reviewed."
                    if item_index == 1 else "Synthetic source comparison context; not a conclusion of intent."
                ),
                "source_ref": f"synthetic://evidence/{case_key}/{item_index:03d}",
                "added_by": 2, "added_at": added_at,
            })
            if not (position == 3 and item_index == 3):
                event_rows.append({
                    "case_id": position, "actor_id": 2, "event_type": "evidence_added",
                    "from_state": "decided" if position == 3 and item_index == 3 else "under_review",
                    "to_state": "decided" if position == 3 and item_index == 3 else "under_review",
                    "details": ev_key, "created_at": added_at,
                })

        outcome = "not_substantiated" if truth == "legitimate" else (
            "substantiated" if truth == "misconduct" else "inconclusive"
        )
        if appeal_success:
            outcome = "substantiated"
        if position == 1:
            outcome = "substantiated"
        if has_decision:
            decision_time = created_at + timedelta(days=1)
            decision_id = len(decision_rows) + 1
            decision_rows.append({
                "id": decision_id, "decision_key": f"DEC-2026-{decision_id:06d}",
                "case_id": position, "reviewer_id": reviewer_id, "outcome": outcome,
                "rationale": (
                    "Synthetic training decision based on reviewed contextual evidence; similarity alone is not proof."
                ),
                "decided_at": decision_time,
            })
            event_rows.append({
                "case_id": position, "actor_id": 3 if position == 1 else users[5 + reviewer_id - 1]["id"],
                "event_type": "automatic_guilt" if position == 1 else "decision_recorded",
                "from_state": "under_review", "to_state": "decided",
                "details": "Automatic penalty from a similarity score; this intentionally violates due process."
                if position == 1 else f"{outcome}; rationale recorded.",
                "created_at": decision_time,
            })
            if close_without_appeal:
                event_rows.append({
                    "case_id": position, "actor_id": 3, "event_type": "case_closed",
                    "from_state": "decided", "to_state": "closed",
                    "details": "Case closed after documented review; no appeal was filed.",
                    "created_at": closed_at,
                })
        if appeal_case:
            appeal_id = len(appeal_rows) + 1
            appeal_status = "resolved" if position == 4 or appeal_success else "pending"
            appeal_outcome = "upheld" if position == 4 else ("overturned" if appeal_success else None)
            independent_id = None if position == 4 else (reviewer_id % len(reviewers)) + 1
            resolved_at = created_at + timedelta(days=4) if appeal_status == "resolved" else None
            appeal_rows.append({
                "id": appeal_id, "appeal_key": f"APL-{case_key}-01", "case_id": position,
                "appellant_id": 1, "reason": "Synthetic appeal citing quote context and requesting independent review.",
                "status": appeal_status, "independent_reviewer_id": independent_id,
                "outcome": appeal_outcome, "submitted_at": created_at + timedelta(days=2),
                "resolved_at": resolved_at,
            })
            event_rows.append({
                "case_id": position, "actor_id": 1, "event_type": "appeal_submitted",
                "from_state": "decided", "to_state": "appealed", "details": "Synthetic appeal filed.",
                "created_at": created_at + timedelta(days=2),
            })
            if appeal_status == "resolved":
                event_rows.append({
                    "case_id": position, "actor_id": users[5 + ((independent_id or 1) - 1)]["id"]
                    if independent_id else 3,
                    "event_type": "appeal_resolved" if independent_id else "appeal_closed_without_independent_review",
                    "from_state": "appealed", "to_state": "closed",
                    "details": f"{appeal_outcome}; independent reviewer "
                    + (str(independent_id) if independent_id else "missing (intentional anomaly)"),
                    "created_at": resolved_at,
                })
        truth_rows.append({
            "case_key": case_key, "expected_label": truth, "expected_decision": (
                "not_substantiated" if truth == "legitimate" else
                "substantiated" if truth == "misconduct" else "inconclusive"
            ),
            "issue_type": issue_type,
            "anomaly": issue_type != "standard",
            "successful_appeal": appeal_success,
        })

    dataset = {
        "users": users, "learners": learners, "assessments": assessment_rows, "rules": rules,
        "submissions": submission_rows, "reports": report_rows, "reviewers": reviewers,
        "cases": case_rows, "assignments": assignment_rows, "evidence": evidence_rows,
        "decisions": decision_rows, "appeals": appeal_rows, "events": event_rows,
        "ground_truth": truth_rows,
    }
    validate_dataset(dataset, submissions, flags, cases)
    return dataset


def validate_dataset(dataset: dict[str, Any], submissions: int, flags: int, cases: int) -> dict[str, Any]:
    assert len(dataset["submissions"]) == submissions
    assert len(dataset["reports"]) == submissions
    assert sum(row["review_flag"] for row in dataset["reports"]) == flags
    assert len(dataset["cases"]) == cases
    assert len({row["submission_key"] for row in dataset["submissions"]}) == submissions
    submission_ids = {row["id"] for row in dataset["submissions"]}
    report_ids = {row["id"] for row in dataset["reports"]}
    case_ids = {row["id"] for row in dataset["cases"]}
    learner_ids = {row["id"] for row in dataset["learners"]}
    assessment_ids = {row["id"] for row in dataset["assessments"]}
    reviewer_ids = {row["id"] for row in dataset["reviewers"]}
    user_ids = {row["id"] for row in dataset["users"]}
    assert all(row["learner_id"] in learner_ids and row["assessment_id"] in assessment_ids
               for row in dataset["submissions"])
    assert all(row["submission_id"] in submission_ids for row in dataset["reports"])
    report_by_id = {row["id"]: row for row in dataset["reports"]}
    assert all(
        row["submission_id"] in submission_ids and row["report_id"] in report_ids
        and report_by_id[row["report_id"]]["submission_id"] == row["submission_id"]
        and report_by_id[row["report_id"]]["review_flag"]
        for row in dataset["cases"]
    )
    assert all(row["case_id"] in case_ids for key in ("assignments", "evidence", "decisions", "appeals", "events") for row in dataset[key])
    assert all(row["reviewer_id"] in reviewer_ids for row in dataset["assignments"] + dataset["decisions"])
    assert all(row["added_by"] in user_ids for row in dataset["evidence"])
    assert all(row["appellant_id"] in user_ids and (
        row["independent_reviewer_id"] is None or row["independent_reviewer_id"] in reviewer_ids
    ) for row in dataset["appeals"])
    assert all(row["actor_id"] in user_ids for row in dataset["events"])
    for key in ("users", "learners", "assessments", "rules", "submissions", "reports", "reviewers",
                "cases", "evidence", "decisions", "appeals"):
        rows = dataset[key]
        assert len({row["id"] for row in rows}) == len(rows), f"Duplicate primary key in {key}"
    for key, field in (
        ("submissions", "submission_key"), ("reports", "report_key"), ("cases", "case_key"),
        ("evidence", "evidence_key"), ("decisions", "decision_key"), ("appeals", "appeal_key"),
    ):
        rows = dataset[key]
        assert len({row[field] for row in rows}) == len(rows), f"Duplicate {field}"
    assert all(row["review_flag"] == (row["score"] >= row["threshold"]) for row in dataset["reports"])
    report_by_submission = {row["submission_id"]: row for row in dataset["reports"]}
    assert all(
        row["expected_label"] == derive_label(report_by_submission[case["submission_id"]])
        for row, case in zip(dataset["ground_truth"], dataset["cases"])
    )
    audit_gap = {
        row["case_id"] for row in dataset["evidence"]
        if not any(event["case_id"] == row["case_id"] and event["details"] == row["evidence_key"]
                   for event in dataset["events"])
    }
    assert audit_gap == {3}, f"Unexpected evidence audit gaps: {audit_gap}"
    assert all(row["due_at"] > row["created_at"] for row in dataset["cases"])
    assert all(row["status"] in ("open", "under_review", "decided", "appealed", "closed")
               for row in dataset["cases"])
    assert all((row["closed_at"] is not None) == (row["status"] == "closed") for row in dataset["cases"])
    assert all(row["resolved_at"] is not None if row["status"] == "resolved" else row["resolved_at"] is None
               for row in dataset["appeals"])
    decisions_by_case = {row["case_id"]: row for row in dataset["decisions"]}
    appeals_by_case = {row["case_id"]: row for row in dataset["appeals"]}
    for case in dataset["cases"]:
        case_decision = decisions_by_case.get(case["id"])
        case_appeal = appeals_by_case.get(case["id"])
        if case["status"] == "under_review":
            assert case_decision is None and case_appeal is None
        if case["status"] == "decided":
            assert case_decision is not None and case_appeal is None
        if case["status"] == "appealed":
            assert case_decision is not None and case_appeal["status"] == "pending"
        if case["status"] == "closed" and case_appeal:
            assert case_appeal["status"] == "resolved"
            assert case_appeal["independent_reviewer_id"] is not None or case["id"] == 4
        if case["status"] == "closed" and not case_appeal:
            assert any(event["case_id"] == case["id"] and event["event_type"] == "case_closed"
                       for event in dataset["events"])
    assert all(row["independent_reviewer_id"] != decisions_by_case[row["case_id"]]["reviewer_id"]
               for row in dataset["appeals"] if row["independent_reviewer_id"] is not None)
    case_id_by_key = {row["case_key"]: row["id"] for row in dataset["cases"]}
    for truth in dataset["ground_truth"]:
        if truth["successful_appeal"]:
            case_id = case_id_by_key[truth["case_key"]]
            assert truth["expected_label"] == "legitimate"
            assert decisions_by_case[case_id]["outcome"] == "substantiated"
            assert appeals_by_case[case_id]["outcome"] == "overturned"
    assert all(
        row["independent_reviewer_id"] is not None
        for row in dataset["appeals"]
        if row["status"] == "resolved" and row["case_id"] != 4
    )
    return {
        "users": len(dataset["users"]), "learners": len(dataset["learners"]),
        "assessments": len(dataset["assessments"]), "rules": len(dataset["rules"]),
        "reviewers": len(dataset["reviewers"]), "submissions": submissions,
        "reports": len(dataset["reports"]), "flags": flags, "cases": cases,
        "evidence": len(dataset["evidence"]), "decisions": len(dataset["decisions"]),
        "appeals": len(dataset["appeals"]), "events": len(dataset["events"]),
        "label_counts": {label: sum(row["expected_label"] == label for row in dataset["ground_truth"])
                         for label in ("legitimate", "misconduct", "uncertain")},
        "anomaly_count": sum(row["anomaly"] for row in dataset["ground_truth"]),
    }


def checksum_rows(rows: list[dict[str, Any]]) -> str:
    data = json.dumps(rows, sort_keys=True, default=lambda value: value.isoformat(), separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

