# User Prompt History

User messages only, listed in chronological order. Assistant responses are not included.

## 1. Original project brief

> Business Context / Problem  
> Manage similarity flags, evidence, reviewer assignment, case timelines and appeal outcomes with due process.
>
> Objective and Scope  
> Build a working solution for this end-to-end workflow: Manage similarity flags, evidence, reviewer assignment, case timelines and appeal outcomes with due process. The solution should expose key decisions and exceptions, preserve traceability, and produce measurable outputs. Medium complexity means multiple related entities, conditional rules, at least one exception path and meaningful evaluation metrics.
>
> Primary Actors / Systems  
> Learner, instructor, academic administrator, support staff and platform administrator
>
> Business Workflow and Rules  
> 1. Generate/reference master data first: Learner, Assessment, Submission, SimilarityReport, IntegrityRule.  
> 2. Generate dependent transaction/event records using valid parent IDs.  
> 3. Apply business logic: Create assessment submissions; generate synthetic similarity reports and evidence references; define thresholds that trigger review rather than automatic guilt; assign reviewers; capture decisions and rationale; support appeals and case closure.  
> 4. Persist state changes as explicit records/events where relevant; do not overwrite history.  
> 5. Generate outcomes and ground-truth labels from documented rules, not independent random assignment.
>
> Entities and Relationships  
> Core entities: Learner, Assessment, Submission, SimilarityReport, IntegrityRule, Case, EvidenceItem, Reviewer, Decision, Appeal. Define a primary key for every entity and foreign keys for every relationship. Document cardinality (1:1, 1:N, N:M), optional relationships, effective dates and lifecycle states. Use bridge tables for many-to-many relationships; retain event history for state changes; validate all joins. For deliberate anomaly cases, keep an issue_type/ground_truth label rather than silently corrupting unrelated rows.
>
> ID / Nomenclature Conventions  
> SUB-2026-000001; SIM-<submission-id>-01; INT-2026-000001; EVD-<case-id>-001; APL-<case-id>-01.
>
> Synthetic Data Generation Instructions (Granular)  
> Step 1 — Write a data dictionary for: Learner, Assessment, Submission, SimilarityReport, IntegrityRule, Case, EvidenceItem, Reviewer Decision, Appeal. For each field specify type, required/optional, allowed values, units, uniqueness and validation rule.  
> Step 2 — Create parent/master tables first, then child and event tables. Apply this domain-specific generation logic: Create assessment submissions; generate synthetic similarity reports and evidence references; define thresholds that trigger review rather than automatic guilt; assign reviewers; capture decisions and rationale; support appeals and case closure.  
> Step 3 — Apply deterministic IDs and naming: SUB-2026-000001; SIM-<submission-id>-01; INT-2026-000001; EVD-<case-id>-001; APL-<case-id>-01. Keep counters zero-padded, IDs immutable, and referenced IDs exactly consistent across files.  
> Step 4 — Generate the baseline volume: Generate 10,000 submissions, 1,000 flags and 300 cases. Include legitimate quoted material, shared templates, false positives, multiple reviewers and successful appeals. Use a fixed seed (e.g. 20261022) and parameterize scale so starter and full datasets use the same generator.  
> Step 5 — Generate valid baseline records first, then inject labelled edge cases: Flag automatically treated as guilt; reviewer has conflict; evidence added after decision without history; appeal closed without independent review.  
> Step 6 — Calculate derived values (totals, balances, scores, statuses and dates) from source records rather than generating them independently.  
> Step 7 — Produce a separate ground_truth.csv/json for known anomalies, expected decisions or labels; never leak it into input features.  
> Step 8 — Run validation: primary-key uniqueness, foreign-key integrity, allowed enums, date ordering, arithmetic reconciliation, lifecycle transitions and duplicate checks.  
> Step 9 — Export CSV/JSON/SQL seed data plus README, schema/data dictionary, generator command, fixed seed, source manifest and validation summary.  
> Step 10 — Regenerate twice with the same seed and compare row counts/checksums to demonstrate reproducibility.
>
> Suggested Volume and Coverage  
> Generate 10,000 submissions, 1,000 flags and 300 cases. Include legitimate quoted material, shared templates, false positives, multiple reviewers and successful appeals.
>
> Required Edge Cases / Negative Scenarios  
> Flag automatically treated as guilt; reviewer has conflict; evidence added after decision without history; appeal closed without independent review.
>
> Validation Rules / Acceptance Criteria  
> Case process preserves evidence and rationale; thresholds are transparent; false positives and appeals are represented; audit history is complete.
>
> Evaluation Focus for Generated Data  
> Review: (a) realistic distributions and meaningful variation; (b) consistent IDs and valid joins; (c) dependency/lifecycle consistency across entities; (d) correct derived values and reconciliation; (e) normal, boundary, failure and exception coverage; (f) separate ground truth; (g) fixed-seed reproducibility, documentation and lawful provenance.
>
> Public Data Guidance / Lawful Use  
> External data is optional. If used, record source URL, dataset/version, retrieval date, license/terms, attribution, transformations and fields discarded. Use only data you are legally permitted to access and redistribute; do not bypass access controls or collect confidential/personal information. If licensing or suitability is unclear, use synthetic data and cite public reference data only for schema inspiration.
>
> BEFORE YOU SUBMIT, MAKE SURE YOU HAVE  
> Pushed your code to a public GitHub repository  
> Added a README explaining how to run it  
> Included any tests the problem asks for
>
> The above is the project that I need to work on, I want to build a AI powered assignment plagarism or similarity detection tool, with various logins and features mentioned above
>
> I have python, docker, node installed
>
> Can you setup a fullstack project with fast-api, react, postgres database
>
> I want to use docker, so its easy to run, lets plan and implement these accordingly

## 2. Follow-up prompts

### Prompt 2

> docker compose should also work now

### Prompt 3

> why do we have node modules in outer directory, we need to removeit?  
> I need a proper application, with api backend and frontend  
> I need various user roles and logins  
> Not just a single page to show the app, need a proper application

### Prompt 4

> The overall implementation or the project structure is poor, we need to have react components, ideally with tailwing, not such bad css files
>
> Also the backend should be properly structed into various folders like controllers, not just the individual python files
>
> Why is the config using sqlite db, we need a proper postgres database

### Prompt 5

> I need role based controls properly built at the frontend and backend
>
> A learner, can only submit a assignment, maybe as a text for now
>
> And manage his appeals, likewise different roles should have their features controlled

### Prompt 6

> we should have migrations to create tables and then seed the data, lets not implement the alter migrations as we are just starting out

### Prompt 7

> we can drop and create tables

### Prompt 8

> similarity.py should be in core right?
>
> models.py and schems.py should be in their own folders

### Prompt 11

> I also want to implement proper authentication, lets seed the users with some sample data, all can have same password
>
> When we select the role in the dropdown, we can temporarily autopopulate the same default password like we are doing now to test
>
> Are we having users table? with email field?

### Prompt 12

> Are we having the backend implemented for authentication and authorizatino?

### Prompt 13

> ok, do we already have the users with email and password seeded in the tables?

### Prompt 14

> each role to have different email

### Prompt 15

> give me some sample texts to test the platform

### Prompt 16

> When I select a role, can we populate the email field in the frontend? these can be hardcoded or part of the frontend env

### Prompt 17

> I just submitted a assignment as a learner, where can the other roles view that assignment?
>
> Also, against the submission if it fails at the similarity report, where can we view them?
>
> How can a learner appeal for it in the UI?
>
> I need a completed E2E functionality

### Prompt 18

> can you drop the migrations and drop the db, so inital seed will have these all?
>
> This is still an initial commit, so may not need individual migrations

### Prompt 19

> learner login isn't working, dashbaord api is 500

## 3. Testing and workflow prompts

### Prompt 20

> Give me some sample assignment tests

### Prompt 21

> If we found the submission is similar, then would that create a case by default?
>
> I do not understand the flow, whats happening?

### Prompt 22

> Apart from the exact match, can you give a case where the % be > 72, sample text

### Prompt 23

> Can't we select a submission or a case during an appeal?

### Prompt 24

> Also, who can change the case and appeal status?
>
> I am not seeing that option, reviewer isn't able to see the open cases?
