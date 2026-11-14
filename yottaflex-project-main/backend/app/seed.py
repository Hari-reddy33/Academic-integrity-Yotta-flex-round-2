import csv
import argparse
import json
import os
from pathlib import Path

from sqlalchemy import func, insert, select, text

from app.core.config import settings
from app.db.session import SessionLocal, engine
from app.generator import build_dataset, checksum_rows, validate_dataset
from app.models import (
    Appeal, Assessment, CaseEvent, CaseReviewer, Decision, EvidenceItem, IntegrityCase,
    IntegrityRule, Learner, Reviewer, SimilarityReport, Submission, User,
)
from app.core.security import hash_password


OUTPUT_DIR = Path(os.getenv("DATA_DIR", "/app/data"))
TABLES = {
    "users": User, "learners": Learner, "assessments": Assessment, "rules": IntegrityRule,
    "submissions": Submission, "reports": SimilarityReport, "reviewers": Reviewer,
    "cases": IntegrityCase, "assignments": CaseReviewer, "evidence": EvidenceItem,
    "decisions": Decision, "appeals": Appeal, "events": CaseEvent,
}


def sync_postgres_sequences(db):
    if db.get_bind().dialect.name != "postgresql":
        return
    for model in TABLES.values():
        sequence = db.scalar(
            text("SELECT pg_get_serial_sequence(:table_name, 'id')"),
            {"table_name": model.__tablename__},
        )
        if not sequence:
            continue
        max_id = db.scalar(select(func.max(model.id)))
        db.execute(
            text(
                "SELECT setval(CAST(:sequence_name AS regclass), :last_id, :is_called)"
            ),
            {"sequence_name": sequence, "last_id": max_id or 1, "is_called": max_id is not None},
        )
    db.commit()


def write_exports(dataset: dict, summary: dict):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    checksums = {}
    for name in TABLES:
        path = OUTPUT_DIR / f"{name}.csv"
        rows = dataset[name]
        if not rows:
            continue
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        checksums[path.name] = checksum_rows(rows)
    ground_truth_path = OUTPUT_DIR / "ground_truth.json"
    ground_truth_path.write_text(json.dumps(dataset["ground_truth"], indent=2) + "\n", encoding="utf-8")
    checksums[ground_truth_path.name] = checksum_rows(dataset["ground_truth"])
    manifest = {
        "generator": "app.generator.build_dataset",
        "seed": settings.seed_seed,
        "parameters": {
            "submissions": settings.seed_submissions,
            "flags": settings.seed_flags,
            "cases": settings.seed_cases,
        },
        "validation": summary,
        "checksums_sha256": checksums,
        "provenance": "Entirely synthetic records; no external learner data or source content.",
    }
    (OUTPUT_DIR / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def ensure_demo_learner_account(db, dataset: dict) -> None:
    learner_account = next(
        user for user in dataset["users"] if user["email"] == "learner2@demo.local"
    )
    existing = db.scalar(select(User).where(User.email == learner_account["email"]))
    if existing is not None:
        return

    user = User(
        email=learner_account["email"],
        full_name=learner_account["full_name"],
        role=learner_account["role"],
        password_hash=hash_password("demo1234"),
        active=True,
    )
    db.add(user)
    db.flush()
    learner = db.scalar(select(Learner).where(Learner.learner_key == "LRN-2026-000002"))
    if learner is None:
        raise RuntimeError("The second synthetic learner profile is missing.")
    if learner.user_id is None:
        learner.user_id = user.id
    elif learner.user_id != user.id:
        raise RuntimeError("The second synthetic learner profile is linked to another account.")
    db.commit()


def main():
    parser = argparse.ArgumentParser(description="Generate deterministic synthetic integrity-review data.")
    parser.add_argument("--export-only", action="store_true", help="Write deterministic CSV/JSON files without modifying PostgreSQL.")
    args = parser.parse_args()
    dataset = build_dataset(settings.seed_submissions, settings.seed_flags, settings.seed_cases, settings.seed_seed)
    summary = validate_dataset(
        dataset, settings.seed_submissions, settings.seed_flags, settings.seed_cases
    )
    if args.export_only:
        write_exports(dataset, summary)
        print(json.dumps({"exported": summary, "export_dir": str(OUTPUT_DIR)}, indent=2))
        return
    with SessionLocal() as db:
        sync_postgres_sequences(db)
        existing = db.scalar(select(func.count(User.id))) or 0
        if existing:
            ensure_demo_learner_account(db, dataset)
            print("Database already contains users; preserving existing data.")
            return
        try:
            for name, model in TABLES.items():
                rows = dataset[name]
                if name == "users":
                    rows = [
                        {**row, "password_hash": hash_password("demo1234"), "active": True}
                        for row in rows
                    ]
                if rows:
                    db.execute(insert(model), rows)
            db.commit()
        except Exception:
            db.rollback()
            raise
        sync_postgres_sequences(db)
    write_exports(dataset, summary)
    print(json.dumps({"seeded": summary, "export_dir": str(OUTPUT_DIR)}, indent=2))


if __name__ == "__main__":
    main()

