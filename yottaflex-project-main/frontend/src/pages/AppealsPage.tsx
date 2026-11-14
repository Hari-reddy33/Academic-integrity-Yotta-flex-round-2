import { Scale } from "lucide-react";
import type { FormEvent } from "react";

import { Button, Card, Eyebrow, SelectField, StatusBadge, TextAreaField } from "../components/ui";
import type { ActionHandler, AppealRow, CaseSummary, Reviewer, User } from "../types";

export function AppealsPage({ appeals, eligibleCases, user, busy, reviewers, onAction, onResolve, onSubmitAppeal }: {
  appeals: AppealRow[];
  eligibleCases: CaseSummary[];
  user: User;
  busy: boolean;
  reviewers: Reviewer[];
  onAction: ActionHandler;
  onResolve: (event: FormEvent<HTMLFormElement>, appealKey: string, values: Record<string, string>) => void;
  onSubmitAppeal: (event: FormEvent<HTMLFormElement>, caseKey: string, reason: string) => void;
}) {
  return (
    <Card className="p-5">
      <header className="mb-5 flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 pb-4">
        <div><Eyebrow>Independent review</Eyebrow><h2 className="mt-1 text-lg font-bold text-slate-900">Appeals</h2></div>
        <span className="text-xs text-slate-500">{appeals.length} record(s)</span>
      </header>
      {appeals.length === 0 ? (
        <div className="grid min-h-36 place-items-center text-center">
          <div><Scale className="mx-auto text-slate-300" /><p className="mt-3 text-sm text-slate-600">No appeals are available for this account.</p></div>
        </div>
      ) : (
        <div className="grid gap-3">
          {appeals.map((appeal) => {
            const isOriginalReviewer = appeal.original_reviewer_user_id === user.id;
            const assignedReviewer = reviewers.find((reviewer) => reviewer.id === appeal.independent_reviewer_id);
            const assignableReviewers = reviewers.filter(
              (reviewer) => reviewer.id !== appeal.original_reviewer_id
                && !appeal.conflicted_reviewer_ids.includes(reviewer.id),
            );
            return (
              <article key={appeal.appeal_key} className="rounded-xl border border-slate-200 p-4">
                <header className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <strong className="text-sm font-bold text-slate-800">{appeal.appeal_key}</strong>
                    <p className="mt-1 text-xs text-slate-500">
                      Case {appeal.case_key} · {new Date(appeal.submitted_at).toLocaleDateString()}
                    </p>
                  </div>
                  <StatusBadge value={appeal.status === "resolved" ? appeal.outcome ?? "resolved" : appeal.status} />
                </header>
                <p className="mt-4 text-sm leading-6 text-slate-600">{appeal.reason}</p>
                {appeal.independent_reviewer_id !== null && (
                  <p className="mt-3 text-xs text-slate-500">
                    Independent reviewer: {assignedReviewer?.name ?? `Reviewer ${appeal.independent_reviewer_id}`}
                  </p>
                )}
                {appeal.status === "pending" && ["academic_admin", "platform_admin"].includes(user.role) && (
                  <form
                    className="mt-4 flex flex-wrap gap-2 rounded-xl bg-slate-50 p-4"
                    onSubmit={(event) => {
                      const data = new FormData(event.currentTarget);
                      onAction(event, `/appeals/${appeal.appeal_key}/assign`, {
                        reviewer_id: String(data.get("reviewer_id")),
                      });
                    }}
                  >
                    <SelectField name="reviewer_id" label="Assign independent reviewer">
                      <option value="">Select an unconflicted reviewer</option>
                      {assignableReviewers.map((reviewer) => (
                        <option key={reviewer.id} value={reviewer.id}>{reviewer.name} · {reviewer.department}</option>
                      ))}
                    </SelectField>
                    <Button type="submit" disabled={busy || assignableReviewers.length === 0} className="self-end">
                      Assign reviewer
                    </Button>
                  </form>
                )}
                {appeal.status === "pending" && user.role === "reviewer" && (
                  isOriginalReviewer ? (
                    <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2.5 text-sm text-amber-800">
                      You made the original decision and cannot resolve this appeal.
                    </p>
                  ) : (
                    <form
                      className="mt-4 grid gap-3 rounded-xl bg-slate-50 p-4 md:grid-cols-[180px_minmax(0,1fr)_auto]"
                      onSubmit={(event) => {
                        const data = new FormData(event.currentTarget);
                        onResolve(event, appeal.appeal_key, {
                          outcome: String(data.get("outcome")),
                          rationale: String(data.get("rationale")),
                        });
                      }}
                    >
                      <SelectField name="outcome" label="Appeal outcome">
                        <option value="overturned">Overturned</option>
                        <option value="upheld">Upheld</option>
                        <option value="remanded">Remanded</option>
                      </SelectField>
                      <TextAreaField name="rationale" label="Independent rationale" minLength={20} required rows={2} placeholder="Document the independent review rationale." />
                      <Button type="submit" disabled={busy} className="self-end">Resolve appeal</Button>
                    </form>
                  )
                )}
                {appeal.status === "pending" && user.role !== "reviewer" && (
                  !["academic_admin", "platform_admin"].includes(user.role) && (
                    <p className="mt-4 text-xs text-slate-500">Pending independent reviewer review.</p>
                  )
                )}
              </article>
            );
          })}
        </div>
      )}
      {user.role === "learner" && (
        <section className="mt-7 border-t border-slate-100 pt-5">
          <Eyebrow>Due process</Eyebrow>
          <h3 className="mt-1 text-base font-bold text-slate-900">Decisions you may appeal</h3>
          <p className="mt-1 text-sm text-slate-500">Submit an appeal for a decided case that does not already have one.</p>
          {eligibleCases.length === 0 ? (
            <p className="mt-4 rounded-lg bg-slate-50 p-4 text-sm text-slate-500">There are no decisions currently eligible for appeal.</p>
          ) : (
            <form
              className="mt-4 grid gap-3 rounded-xl border border-slate-200 p-4"
              onSubmit={(event) => {
                const data = new FormData(event.currentTarget);
                onSubmitAppeal(
                  event,
                  String(data.get("case_key")),
                  String(data.get("reason")),
                );
              }}
            >
              <SelectField label="Case and submission" name="case_key" required defaultValue="">
                <option value="" disabled>Select the decision you want to appeal</option>
                {eligibleCases.map((item) => (
                  <option key={item.case_key} value={item.case_key}>
                    {item.case_key} · {item.submission_key}
                  </option>
                ))}
              </SelectField>
              <TextAreaField label="Appeal grounds" name="reason" minLength={10} required rows={3} placeholder="Explain why you are appealing this decision." />
              <Button type="submit" disabled={busy} className="sm:justify-self-start">Submit appeal</Button>
            </form>
          )}
        </section>
      )}
    </Card>
  );
}
