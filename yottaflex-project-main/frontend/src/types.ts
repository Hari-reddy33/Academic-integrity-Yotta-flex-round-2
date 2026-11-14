import type { FormEvent } from "react";

export type User = { id: number; email: string; full_name: string; role: string };
export type Page = "dashboard" | "submit" | "submissions" | "cases" | "reports" | "appeals" | "similarity" | "reviewers";
export type AssessmentOption = {
  id: number;
  assessment_key: string;
  title: string;
  course_code: string;
  due_at: string;
};
export type SubmissionRow = {
  submission_key: string;
  learner_key: string;
  assessment_key: string;
  assessment_title: string;
  course_code: string;
  submitted_at: string;
  analysis_status: string;
  text_preview: string;
  report_key: string | null;
  similarity_score: number | null;
  threshold: number | null;
  review_flag: boolean | null;
  comparison_available: boolean;
  matching_submission_key: string | null;
  case_key: string | null;
  case_status: string | null;
};
export type SubmissionDetail = SubmissionRow & { content_text: string };

export type CaseSummary = {
  id: number;
  case_key: string;
  submission_key: string;
  status: string;
  created_at: string;
  due_at: string;
  evidence_count: number;
  decision_count: number;
  appeal_status: string | null;
};

export type CaseDetail = CaseSummary & {
  submission: {
    submission_key: string;
    learner_key: string;
    assessment: string;
    submitted_at: string;
    content_text: string;
  };
  similarity: {
    score: number;
    quoted_overlap: number | null;
    template_overlap: number | null;
    threshold: number;
    review_flag: boolean;
    matching_submission_key?: string;
    matching_content_text?: string;
  };
  reviewers: { id: number; user_id: number; name: string; conflict_declared: boolean }[];
  evidence: {
    evidence_key: string;
    kind: string;
    description: string;
    source_ref: string;
    added_at: string;
  }[];
  decisions: {
    decision_key: string;
    outcome: string;
    rationale: string;
    decided_at: string;
  }[];
  appeals: {
    appeal_key: string;
    reason: string;
    status: string;
    outcome: string | null;
    submitted_at: string;
  }[];
  timeline: {
    event_type: string;
    from_state: string | null;
    to_state: string | null;
    details: string;
    created_at: string;
  }[];
};

export type Metrics = {
  total_cases: number;
  open_cases: number;
  flagged_reports: number;
  pending_appeals: number;
};

export type Report = {
  report_key: string;
  submission_key: string;
  assessment: string;
  score: number;
  threshold: number;
  review_flag: boolean;
  matching_submission_key: string | null;
  case_key: string | null;
  generated_at: string;
};

export type AppealRow = {
  appeal_key: string;
  case_key: string;
  status: string;
  outcome: string | null;
  reason: string;
  submitted_at: string;
  original_reviewer_id: number | null;
  original_reviewer_user_id: number | null;
  independent_reviewer_id: number | null;
  conflicted_reviewer_ids: number[];
};

export type Reviewer = { id: number; name: string; department: string; active_cases: number };

export type SimilarityResult = {
  score: number;
  threshold: number;
  review_flag: boolean;
  model: string;
  notice: string;
  input_retained: boolean;
  shared_terms: { term: string; weight: number }[];
};

export type ActionHandler = (
  event: FormEvent<HTMLFormElement>,
  path: string,
  values: Record<string, string>,
) => void;
