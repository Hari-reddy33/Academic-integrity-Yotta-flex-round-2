import type { FormEvent } from "react";
import { ArrowUpRight, CheckCircle2, Clock3, Eye, FilePlus2, Files, ShieldAlert } from "lucide-react";

import { Button, Card, EmptyState, Eyebrow, SelectField, StatusBadge, TextAreaField } from "../components/ui";
import type { AssessmentOption, SubmissionDetail, SubmissionRow, User } from "../types";

export function SubmitAssignmentPage({ assessments, busy, success, onSubmit }: {
  assessments: AssessmentOption[];
  busy: boolean;
  success: string;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <div className="mx-auto grid max-w-4xl gap-5">
      {success && (
        <div role="status" className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800">
          <CheckCircle2 size={18} className="mt-0.5 shrink-0" />
          <span>{success}</span>
        </div>
      )}
      <Card className="overflow-hidden">
        <header className="border-b border-slate-100 px-5 py-5 sm:px-7">
          <div className="flex items-center gap-2 text-[#a9593e]"><FilePlus2 size={18} /><Eyebrow>Learner submission</Eyebrow></div>
          <h2 className="mt-2 text-xl font-bold tracking-tight text-slate-900">Submit an assignment</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
            Choose the assessment and submit your work as text. Your submission is stored in this application and linked to your learner account.
          </p>
        </header>
        <form className="grid gap-5 px-5 py-5 sm:px-7" onSubmit={onSubmit}>
          <SelectField label="Assessment" name="assessment_id" required defaultValue="">
            <option value="" disabled>Select an assessment</option>
            {assessments.map((assessment) => (
              <option value={assessment.id} key={assessment.id}>
                {assessment.course_code} · {assessment.title}
              </option>
            ))}
          </SelectField>
          <TextAreaField
            label="Assignment text"
            name="content_text"
            minLength={30}
            maxLength={100_000}
            required
            rows={14}
            placeholder="Paste or type your assignment text here (30–100,000 characters)."
          />
          <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4">
            <span className="text-xs text-slate-500">Plain text only · Maximum 100,000 characters</span>
            <Button type="submit" disabled={busy || assessments.length === 0}>
              <FilePlus2 size={15} />{busy ? "Submitting..." : "Submit assignment"}
            </Button>
          </div>
          {assessments.length === 0 && <p className="text-sm text-amber-700">No assessments are currently available.</p>}
        </form>
      </Card>
      <div className="flex items-start gap-3 rounded-xl border border-sky-100 bg-sky-50 px-4 py-3 text-xs leading-5 text-sky-900">
        <ShieldAlert size={16} className="mt-0.5 shrink-0" />
        <p>
          Similarity analysis runs after submission against available text from other learners in the same assessment. A flag opens a case for human review; it is not a finding of misconduct. Only authorized staff and you can access your submission text.
        </p>
      </div>
    </div>
  );
}

export function MySubmissionsPage({ submissions, selected, user, busy, onOpenSubmission, onOpenCase }: {
  submissions: SubmissionRow[];
  selected: SubmissionDetail | null;
  user: User;
  busy: boolean;
  onOpenSubmission: (submissionKey: string) => void;
  onOpenCase: (caseKey: string | null) => void;
}) {
  const isLearner = user.role === "learner";
  const selectedMatchingKey = selected?.matching_submission_key;

  return (
    <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1fr)_minmax(320px,0.9fr)]">
      <Card className="overflow-hidden">
        <header className="flex items-center gap-3 border-b border-slate-100 px-5 py-4">
          <span className="grid size-10 place-items-center rounded-xl bg-slate-100 text-slate-600"><Files size={18} /></span>
          <div>
            <Eyebrow>{isLearner ? "Learner workspace" : "Academic records"}</Eyebrow>
            <h2 className="mt-1 text-lg font-bold text-slate-900">{isLearner ? "My submissions" : "Submissions"}</h2>
          </div>
        </header>
        {submissions.length === 0 ? (
          <div className="p-5">
            <EmptyState
              title={isLearner ? "No submissions yet" : "No submissions available"}
              description={isLearner
                ? "Your assignment submissions will be listed here after you submit your first assessment."
                : "Submissions are visible here after learners submit assignment text."}
            />
          </div>
        ) : (
          <div className="divide-y divide-slate-100">
            {submissions.map((submission) => (
              <article key={submission.submission_key} className="px-5 py-5 sm:px-6">
                <header className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-mono text-xs font-semibold text-slate-500">{submission.submission_key}</p>
                    <h3 className="mt-1 text-sm font-bold text-slate-900">{submission.assessment_title}</h3>
                    <p className="mt-1 text-xs text-slate-500">
                      {submission.course_code} · {submission.learner_key} · {new Date(submission.submitted_at).toLocaleString()}
                    </p>
                  </div>
                  <StatusBadge value={submission.analysis_status} />
                </header>
                <p className="mt-3 whitespace-pre-wrap rounded-lg bg-slate-50 p-3 text-xs leading-5 text-slate-600">{submission.text_preview}</p>
                {submission.similarity_score !== null && (
                  <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
                    <span className="text-slate-600">
                      Similarity <strong className="text-slate-900">{(submission.similarity_score * 100).toFixed(1)}%</strong>
                      {submission.threshold !== null && <> · Review threshold {(submission.threshold * 100).toFixed(0)}%</>}
                    </span>
                    <StatusBadge value={submission.review_flag ? "under_review" : "below_threshold"} />
                  </div>
                )}
                {submission.case_key && (
                  <button
                    className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[#a9593e] hover:underline"
                    onClick={() => onOpenCase(submission.case_key)}
                  >
                    {isLearner ? "Open my case" : `Open case ${submission.case_key}`} <ArrowUpRight size={13} />
                  </button>
                )}
                <div className="mt-3 flex items-center justify-between gap-3">
                  <span className="flex items-center gap-1.5 text-xs text-slate-500">
                    <Clock3 size={13} />
                    {submission.analysis_status === "pending"
                      ? "Similarity analysis is pending."
                      : submission.comparison_available
                        ? "Analysis compared this work with another submission for the assessment."
                        : "Analysis completed; no comparable submission was available."}
                  </span>
                  <Button
                    type="button"
                    variant="secondary"
                    disabled={busy}
                    className="min-h-8 shrink-0 px-2.5 text-xs"
                    onClick={() => onOpenSubmission(submission.submission_key)}
                  >
                    <Eye size={14} /> View text
                  </Button>
                </div>
              </article>
            ))}
          </div>
        )}
      </Card>

      <Card className="overflow-hidden">
        <header className="border-b border-slate-100 px-5 py-4">
          <Eyebrow>{selected ? selected.submission_key : "Submission detail"}</Eyebrow>
          <h2 className="mt-1 text-lg font-bold text-slate-900">Assignment text</h2>
        </header>
        {selected ? (
          <div className="p-5">
            <p className="mb-3 text-xs text-slate-500">
              {selected.assessment_title} · {selected.learner_key}
            </p>
            <pre className="max-h-[65vh] overflow-auto whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-4 font-sans text-sm leading-6 text-slate-700">
              {selected.content_text || "No text was stored for this synthetic submission."}
            </pre>
            {selected.similarity_score !== null && (
              <div className="mt-4 rounded-xl border border-slate-200 p-4">
                <p className="text-sm font-semibold text-slate-800">
                  Similarity score {(selected.similarity_score * 100).toFixed(1)}%
                  {selected.threshold !== null && ` · threshold ${(selected.threshold * 100).toFixed(0)}%`}
                </p>
                <p className="mt-1 text-xs leading-5 text-slate-500">
                  A score at or above the threshold opens a case for human review; it is not a misconduct finding.
                </p>
                {selectedMatchingKey && (
                  <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
                    <p className="text-xs text-slate-600">
                      Closest comparable submission: <strong>{selectedMatchingKey}</strong>
                    </p>
                    <Button
                      type="button"
                      variant="secondary"
                      disabled={busy}
                      className="min-h-8 px-2.5 text-xs"
                      onClick={() => onOpenSubmission(selectedMatchingKey)}
                    >
                      <Eye size={14} /> View comparison
                    </Button>
                  </div>
                )}
                {selected.case_key && (
                  <button
                    className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-[#a9593e] hover:underline"
                    onClick={() => onOpenCase(selected.case_key)}
                  >
                    Open case {selected.case_key} <ArrowUpRight size={13} />
                  </button>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="p-5"><EmptyState title="Choose a submission" description="Select View text to review a submission and its similarity result." /></div>
        )}
      </Card>
    </div>
  );
}
