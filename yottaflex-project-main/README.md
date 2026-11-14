# Integrity Desk

A Dockerized, multi-role academic-integrity application. It separates similarity signals from findings of misconduct and supports reviewer assignment, evidence, reasoned decisions, appeals, exception tracking, and an append-only case timeline.

> This is a local development/demo system, not a production student-records platform. The included records are synthetic. Do not enter real student information until authentication, authorization, privacy, retention, and institutional policy requirements have been independently reviewed.

## Run locally

Requirements: Docker Desktop with Compose. Node.js/Python are only needed if running the frontend or backend outside Docker.

```sh
cp .env.example .env
# Change POSTGRES_PASSWORD, DATABASE_URL (to use the same password), and JWT_SECRET in .env.
docker compose up --build
```

Open:

- Web app: http://localhost:5173
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

On startup, the API applies the Alembic schema migrations and then seeds the configured synthetic dataset if the database is empty. The initial migration creates all tables; it does not alter an existing unmanaged schema. The default generation is 10,000 submissions, 1,000 reports flagged for human review, and 300 cases. It exports CSV and JSON files into `data/`. The database volume is persistent; subsequent starts preserve existing data rather than reseeding it.

PostgreSQL 16 is the only application database. Compose starts the database service and publishes it to `localhost:${DB_PORT:-5432}` for local tools. The backend rejects SQLite `DATABASE_URL` values; the isolated API tests use an in-memory SQLite fixture only.

### Demo accounts

All demo accounts are seeded with the same demo password, `demo1234`, and the password is stored as a hash. Sign-in requires both the selected account's email and that password; the API issues a JWT used by protected endpoints. Selecting a demo role fills its email and resets the password field to `demo1234`; the email remains editable. Do not reuse these demo credentials outside a local demo.

| Role | Email |
|---|---|
| Learner 1 | `learner@demo.local` |
| Learner 2 (similarity test) | `learner2@demo.local` |
| Instructor | `instructor@demo.local` |
| Academic administrator | `admin@demo.local` |
| Support | `support@demo.local` |
| Platform administrator | `platform@demo.local` |
| Reviewer 1–4 | `reviewer1@demo.local` through `reviewer4@demo.local` |

Sign in with the role selector on the login screen. The application has separate Dashboard, Case management, Submissions, Similarity lab, Similarity reports, Appeals, and administrator-only Reviewer management workspaces. Use the two learner accounts to submit matching text and exercise the similarity-review workflow. A submission is compared with up to 1,000 recent text submissions by other learners for the same assessment. Every analyzed submission gets a report; a score at or above the active threshold creates an open human-review case, never an automatic misconduct finding. Instructors, support staff, and administrators can view submissions and reports; reviewers see submissions only for assigned cases. Administrators assign a reviewer, who can inspect the submitted work, add evidence, and record a reasoned decision. Learners see their own submissions and cases; after a decision they can appeal from **My cases** or select an eligible case and submission from **My appeals**. Administrators assign each pending appeal to an independent reviewer; only that assigned, unconflicted reviewer (not an original decision-maker) can resolve it.

The Similarity Lab uses a local TF-IDF word/bigram cosine baseline. It returns the score, common terms, and review threshold; text is processed for that request only and not persisted. This is an explainable NLP baseline, not a semantic embedding model or a misconduct classifier. A flag is only a request for human review.

## Dataset generation and validation

The generator is deterministic and uses seed `20261022`. Counts use the same generator and scale together; `4 <= cases <= flags <= submissions` is required. To change the full dataset, edit the `SEED_*` values in `.env`, then seed an empty database. Existing rows are intentionally not overwritten.

```sh
# Unit checks for deterministic generation, thresholds and known exception labels
docker compose run --rm --no-deps api pytest -q

# Re-create CSV/JSON exports without changing the persistent database
docker compose exec api python -m app.seed --export-only

# Reset this local demo database (this deletes its PostgreSQL volume and all rows)
docker compose down -v
docker compose up --build
```

The generator validates primary IDs, foreign-key references, flag/threshold reconciliation, date ordering, required exception coverage, and the known synthetic evidence audit gap. `data/manifest.json` records counts, seed, provenance, validation metrics, and SHA-256 checksums. `data/ground_truth.json` is exported separately from operational records and is not served by the API. Each generated entity has a CSV export (including submissions, reports, cases, evidence, decisions, appeals, events and bridge assignments).

To check the API and frontend without Docker:

```sh
docker compose up -d db
export DATABASE_URL="postgresql+psycopg://integrity:change-me-for-local-use@localhost:5432/integrity"
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
pytest -q
alembic upgrade head
python -m app.seed
python -m app.process_pending
uvicorn app.main:app --reload
```

In another terminal:

```sh
cd frontend
npm install
npm run dev
```

## Workflow and due-process rules

1. Synthetic learners, assessments, effective-dated integrity rules and reviewers are generated before submissions and reports.
2. A score at or above the configured 0.72 threshold creates a review flag, not a guilt finding. Contextual quoted/template overlap is represented separately.
3. Cases can be assigned to reviewers; reviewer assignments carry explicit conflict declarations.
4. Decisions require a reviewer assignment and a written rationale. The decision, evidence additions, reviewer assignments, appeals and closure are separate records and timeline events; prior decisions are not overwritten.
5. Appeals require a decision and an administrator-assigned independent reviewer. Only the assigned, unconflicted reviewer who did not make the original decision can resolve the appeal. Assignment and resolution are recorded in the case timeline; cases cannot be closed through the API without that independent review.
6. Synthetic ground truth is derived from report fields: a flag with quoted overlap >= 0.48 or template overlap >= 0.42 is labelled `legitimate`; otherwise a score >= 0.84 with quoted overlap < 0.40 and template overlap < 0.35 is `misconduct`; remaining flagged reports are `uncertain`. Expected outcomes follow that label. The first two eligible legitimate, high-score cases in deterministic order model a false-positive finding that is overturned on appeal. Four deliberately labelled anomalies separately exercise automatic guilt, reviewer conflict, an evidence audit gap, and appeal closure without independent review. Labels and expected outcomes live only in `ground_truth.json`; do not use that file as an input feature.

## Architecture

- `frontend/`: React + TypeScript + Vite web app, served by Nginx in Compose.
- `frontend/src/components/`, `frontend/src/pages/`, `frontend/src/features/`: reusable Tailwind UI, role-aware pages and workflow features.
- `backend/app/controllers/`: FastAPI route controllers grouped by workflow.
- `backend/app/services/`: business logic, including the similarity baseline.
- `backend/app/core/`: configuration, role policy and authentication.
- `backend/app/db/`: PostgreSQL engine and SQLAlchemy session management.
- `backend/app/models/` and `backend/app/schemas/`: ORM entities and request validation packages.
- `backend/alembic/versions/`: versioned PostgreSQL schema migrations. The API runs `alembic upgrade head` before seed data.
- `backend/`: SQLAlchemy models, schemas, deterministic generator and API tests.
- `db`: PostgreSQL 16 with a named persistent volume.
- `data/`: deterministic synthetic CSV/JSON exports and manifest; safe to share because no real learner data or submission text is generated.

`docker-compose.yml` provides the local orchestration. The API schema is documented interactively at `/docs`.

The main API groups are `/auth`, `/dashboard`, `/cases`, `/reports`, `/appeals`, `/reviewers`, and `/similarity/compare`. JWT role checks and ownership/assignment filters are enforced server-side; hiding a page in the React app is not the security boundary.

## Next production-hardening steps

1. Replace demo accounts with institutional identity and managed user provisioning.
2. Add secure file ingest, malware scanning, retention controls, encryption, consent/notices, and institution-approved access policies before accepting real coursework.
3. Evaluate the lexical baseline on consented and appropriately licensed data; add semantic models only with privacy/security approval, bias evaluation, calibration, and human appeal safeguards.
4. Add deployment secrets, backups, audit retention, monitoring, rate limits, and production-grade authorization tests.

## Public repository

This workspace has no Git remote configured. After reviewing the demo credentials and `.env` handling, create or select your public GitHub repository and push the project from your account. Never commit `.env` or real learner data.
