from app.generator import build_dataset, checksum_rows
from app.services.similarity import compare_text


def test_generator_is_repeatable_and_keeps_flags_at_review_threshold():
    first = build_dataset(submissions=120, flags=24, cases=12, seed=20261022)
    second = build_dataset(submissions=120, flags=24, cases=12, seed=20261022)

    assert checksum_rows(first["submissions"]) == checksum_rows(second["submissions"])
    assert checksum_rows(first["reports"]) == checksum_rows(second["reports"])
    assert sum(report["review_flag"] for report in first["reports"]) == 24
    assert all(report["review_flag"] == (report["score"] >= report["threshold"]) for report in first["reports"])


def test_full_generator_volume_and_checksums_are_repeatable():
    first = build_dataset()
    expected = {
        "submissions": checksum_rows(first["submissions"]),
        "reports": checksum_rows(first["reports"]),
        "cases": checksum_rows(first["cases"]),
        "ground_truth": checksum_rows(first["ground_truth"]),
    }
    del first
    second = build_dataset()

    assert len(second["submissions"]) == 10_000
    assert sum(report["review_flag"] for report in second["reports"]) == 1_000
    assert len(second["cases"]) == 300
    assert {name: checksum_rows(second[name]) for name in expected} == expected


def test_generator_labels_exception_paths_without_masking_audit_gap():
    dataset = build_dataset(submissions=80, flags=20, cases=8)
    anomalies = {row["issue_type"] for row in dataset["ground_truth"] if row["anomaly"]}
    assert anomalies == {
        "automatic_guilt",
        "reviewer_conflict",
        "evidence_after_decision",
        "appeal_without_independent_review",
    }
    assert any(row["successful_appeal"] for row in dataset["ground_truth"])
    assert all(case["submission_id"] <= 80 for case in dataset["cases"])


def test_generator_rejects_impossible_scale():
    try:
        build_dataset(submissions=10, flags=2, cases=3)
    except ValueError as exc:
        assert "4 <= cases <= flags <= submissions" in str(exc)
    else:
        raise AssertionError("Invalid scale should fail explicitly.")


def test_text_similarity_flags_reused_passage_without_claiming_misconduct():
    passage = (
        "A reliable review process examines the source context, quoted material, shared assignment "
        "templates, citations, and the learner's explanation before drawing any conclusion."
    )
    result = compare_text(passage, passage + " The reviewer records a reasoned decision after checking context.")
    unrelated = compare_text(
        passage,
        "Marine ecosystems include coral reefs, plankton communities, ocean currents, and diverse coastal habitats.",
    )

    assert result["score"] > 0.72
    assert result["shared_terms"]
    assert unrelated["score"] < result["score"]

