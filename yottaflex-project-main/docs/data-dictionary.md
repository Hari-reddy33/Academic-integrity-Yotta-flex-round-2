# Data dictionary

All identities use immutable primary keys. `id` is an internal integer key; human-facing keys follow the documented deterministic patterns. Nullable means optional. Timestamps are UTC. Synthetic learner names, programs, work references, and cases contain no external or personally identifying source data.

## Master entities

| Entity | Field | Type / required | Allowed values / units | Uniqueness and validation |
|---|---|---|---|---|
| Learner | `id` | integer, required | — | Primary key |
| | `learner_key` | string, required | `LRN-2026-######` | Unique, immutable |
| | `display_name` | string, required | synthetic display label | Non-empty |
| | `program` | string, required | generated program catalogue | Non-empty |
| | `user_id` | integer, optional | `users.id` | Unique FK; demo login link |
| Assessment | `id` | integer, required | — | Primary key |
| | `assessment_key` | string, required | `ASM-2026-####` | Unique, immutable |
| | `title`, `course_code` | strings, required | generated catalogue / course label | Non-empty |
| | `due_at` | UTC timestamp, required | — | Must follow assessment creation period |
| IntegrityRule | `id` | integer, required | — | Primary key |
| | `rule_key` | string, required | `RULE-2026-###` | Unique |
| | `name`, `description` | strings, required | — | Non-empty |
| | `review_threshold` | float, required | 0–1 score | A score at/above it flags for human review only |
| | `effective_from` | UTC timestamp, required | — | Effective date |
| | `effective_to` | UTC timestamp, optional | — | Null means currently effective; if present must not predate `effective_from` |
| Reviewer | `id` | integer, required | — | Primary key |
| | `reviewer_key` | string, required | `REV-###` | Unique |
| | `user_id` | integer, required | `users.id` | Unique FK |
| | `department` | string, required | synthetic department | Non-empty |

## Submission and review entities

| Entity | Field | Type / required | Allowed values / units | Uniqueness and validation |
|---|---|---|---|---|
| Submission | `id` | integer, required | — | Primary key |
| | `submission_key` | string, required | `SUB-2026-######` | Unique, immutable |
| | `learner_id`, `assessment_id` | integer, required | respective master IDs | FKs; must resolve |
| | `submitted_at` | UTC timestamp, required | — | Submission date |
| | `content_ref` | string, required | synthetic URI or `submission://` reference | Non-empty reference |
| | `content_text` | text, optional | learner-submitted plain text; max 100,000 characters | Null for generated rows; available only to the owning learner through learner endpoints |
| | `analysis_status` | string, required | `pending`, `complete` | `pending` until a similarity-processing workflow has run; flags do not imply a finding |
| SimilarityReport | `id` | integer, required | — | Primary key |
| | `report_key` | string, required | `SIM-<submission-key>-01` | Unique |
| | `submission_id` | integer, required | `submissions.id` | Unique FK: one current report per submission |
| | `score`, `quoted_overlap`, `template_overlap`, `threshold` | float, required | 0–1 normalized score | `review_flag` is derived from `score >= threshold` |
| | `review_flag` | boolean, required | true/false | Workflow flag only; never guilt |
| | `generated_at` | UTC timestamp, required | — | At or after submission |
| Case | `id` | integer, required | — | Primary key |
| | `case_key` | string, required | `INT-2026-######` | Unique, immutable |
| | `submission_id`, `report_id` | integer, required | corresponding IDs | Unique FKs; each case references one report and submission |
| | `status` | string, required | `open`, `under_review`, `decided`, `appealed`, `closed` | Lifecycle state |
| | `created_at`, `due_at` | UTC timestamps, required | — | Due date must follow creation |
| | `closed_at` | UTC timestamp, optional | — | Required only when closed; at/after creation |
| EvidenceItem | `id` | integer, required | — | Primary key |
| | `evidence_key` | string, required | `EVD-<case-key>-###` | Unique, immutable |
| | `case_id`, `added_by` | integer, required | `cases.id`, `users.id` | FKs |
| | `kind` | string, required | `similarity_excerpt`, `source_context`, `review_note`, or extensible label | Non-empty |
| | `description`, `source_ref` | strings, required | synthetic context / URI | Non-empty; never a decision by itself |
| | `added_at` | UTC timestamp, required | — | Event time; additions after decisions remain visible |
| Decision | `id` | integer, required | — | Primary key |
| | `decision_key` | string, required | `DEC-2026-######` | Unique |
| | `case_id`, `reviewer_id` | integer, required | respective IDs | FKs |
| | `outcome` | string, required | `substantiated`, `not_substantiated`, `inconclusive` | Must follow documented review, not score alone |
| | `rationale` | string, required | free text | API requires at least 20 characters |
| | `decided_at` | UTC timestamp, required | — | At/after assignment and evidence considered |

## Relationship, lifecycle, and history entities

| Entity | Field | Type / required | Allowed values / units | Uniqueness and validation |
|---|---|---|---|---|
| CaseReviewer (bridge) | `id` | integer, required | — | Primary key |
| | `case_id`, `reviewer_id` | integers, required | respective IDs | FKs; unique pair; implements Case N:M Reviewer |
| | `assigned_at` | UTC timestamp, required | — | At/after case creation |
| | `conflict_declared` | boolean, required | true/false | A conflicted reviewer cannot decide |
| Appeal | `id` | integer, required | — | Primary key |
| | `appeal_key` | string, required | `APL-<case-key>-01` | Unique |
| | `case_id`, `appellant_id` | integers, required | respective IDs | FKs; one appeal per case in this MVP |
| | `reason` | string, required | free text | API requires at least 10 characters |
| | `status` | string, required | `pending`, `resolved` | Lifecycle |
| | `independent_reviewer_id` | integer, optional | `reviewers.id` | Required to resolve; cannot be an original decision-maker |
| | `outcome` | string, optional | `upheld`, `overturned`, `remanded` | Required when resolved |
| | `submitted_at`, `resolved_at` | UTC timestamps; latter optional | — | Resolution must follow submission |
| CaseEvent | `id` | integer, required | — | Primary key, append-only |
| | `case_id`, `actor_id` | integers, required | respective IDs | FKs |
| | `event_type` | string, required | assignment/evidence/decision/appeal/state event | Non-empty |
| | `from_state`, `to_state` | strings, optional | lifecycle states | Records transitions; events are not overwritten |
| | `details` | string, required | free text/reference | Non-empty audit detail |
| | `created_at` | UTC timestamp, required | — | Event ordering |
| User | `id` | integer, required | — | Primary key |
| | `email` | string, required | email | Unique |
| | `full_name` | string, required | — | Non-empty |
| | `role` | string, required | `learner`, `instructor`, `academic_admin`, `support`, `platform_admin`, `reviewer` | Role authorization |
| | `password_hash` | string, required | Argon2 encoded | Never returned by API |
| | `active` | boolean, required | true/false | Inactive users cannot log in |

## Cardinality and optionality

- Learner 1:N Submission; Assessment 1:N Submission.
- Submission 1:1 SimilarityReport and Submission 0:1 Case in the generated baseline.
- SimilarityReport 0:1 Case; a Case 1:N EvidenceItem, 0:N Decision history, 0:1 Appeal in this MVP, and 1:N CaseEvent.
- Case N:M Reviewer through CaseReviewer. Assignment conflict status is specific to a case/reviewer pair.
- Reviewer 1:N Decision and 0:N independently resolved Appeals. Appeal's independent reviewer is optional while pending, mandatory when resolved.
- User 0:1 Learner, 0:1 Reviewer, 1:N evidence/event/appeal actions.
- Effective dates apply to IntegrityRule. Event timestamps and state history preserve lifecycle; mutable current status is a convenience projection over recorded events.

The SQLAlchemy schema in `backend/app/models.py` defines relational keys and constraints. Synthetic anomaly `issue_type` labels exist only in `data/ground_truth.json`, not in operational case rows or API features; the ground-truth file must remain evaluation-only.

The `/similarity/compare` analyzer accepts two bounded text inputs, builds local TF-IDF word/bigram vectors, and returns cosine similarity, shared terms, the active review threshold, and a review-only flag. It does not retain source text or generate an outcome. This baseline does not establish semantic equivalence, attribution, intent, or misconduct.
