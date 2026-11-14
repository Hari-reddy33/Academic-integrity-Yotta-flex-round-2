import json

from app.db.session import SessionLocal
from app.services.submission_service import analyze_pending_submissions


def main() -> None:
    with SessionLocal() as db:
        processed = analyze_pending_submissions(db)
    print(json.dumps({"pending_submissions_processed": processed}))


if __name__ == "__main__":
    main()
