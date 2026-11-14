import { AlertTriangle, ArrowUpRight, CheckCircle2, Clock3, FileText, Plus, Scale } from "lucide-react";

import { Button, Card, EmptyState, Eyebrow, SelectField, StatusBadge, TextAreaField } from "../../components/ui";
import type { ActionHandler, CaseDetail, CaseSummary, Reviewer, User } from "../../types";

export function CaseWorkspace({ cases, selected, statusFilter, setStatusFilter, onOpenCase, user, busy, reviewers, onAction }: {
  cases: CaseSummary[];
  selected: CaseDetail | null;
  statusFilter: string;
  setStatusFilter: (status: string) => void;
  onOpenCase: (row: CaseSummary) => Promise<void>;
  user: User;
  busy: boolean;
  reviewers: Reviewer[];
  onAction: ActionHandler;
}) {
  return (
    <div className="grid items-start gap-5 xl:grid-cols-[minmax(300px,0.82fr)_minmax(0,1.4fr)]">
      <Card className="overflow-hidden">
        <header className="flex items-end justify-between gap-3 border-b border-slate-100 px-4 py-4">
          <div><Eyebrow>Review queue</Eyebrow><h2 className="mt-1 text-base font-bold text-slate-900">Integrity cases</h2></div>
          <select
            aria-label="Filter by status"
            value={statusFilter}
            onChange={(event) => setStatusFilter(event.target.value)}
            className="max-w-36 rounded-lg border border-slate-200 bg-white px-2.5 py-2 text-xs text-slate-600 outline-none focus:border-[#b96b4e]"
          >
            <option value="">All statuses</option>
            <option value="open">Open</option>
            <option value="under_review">Under review</option>
            <option value="decided">Decided</option>
            <option value="appealed">Appealed</option>
            <option value="closed">Closed</option>
          </select>
        </header>
        <div className="max-h-[calc(100vh-235px)] overflow-auto">
          {cases.map((row) => (
            <button
              key={row.case_key}
              onClick={() => void onOpenCase(row)}
              className={`w-full border-b border-slate-100 px-4 py-4 text-left transition ${
                selected?.case_key === row.case_key
                  ? "bg-[#fbf6f3] shadow-[inset_3px_0_0_#b66347]"
                  : "hover:bg-slate-50"
              }`}
            >
              <span className="flex items-center justify-between gap-2">
                <strong className="font-mono text-xs font-semibold text-slate-800">{row.case_key}</strong>
                <StatusBadge value={row.status} />
              </span>
              <span className="mt-2 flex items-center justify-between gap-2 text-[11px] text-slate-500">
                <span>Evidence {row.evidence_count} · Decisions {row.decision_count}</span>
                <span className="inline-flex items-center gap-1"><Clock3 size={12} />{new Date(row.due_at).toLocaleDateString()}</span>
              </span>
            </button>
          ))}
          {cases.length === 0 && (
            <div className="p-4"><EmptyState title="No cases found" description="No cases match this status or are available to this account." /></div>
          )}
        </div>
      </Card>

      <div>
        {selected ? (
          <CaseDetailPanel item={selected} user={user} busy={busy} reviewers={reviewers} onAction={onAction} />
        ) : (
          <Card className="p-4"><EmptyState title="Select a case" description="Choose a case to review its similarity context, evidence, decisions and appeal history." /></Card>
        )}
      </div>
    </div>
  );
}

function CaseDetailPanel({ item, user, busy, reviewers, onAction }: {
  item: CaseDetail;
  user: User;
  busy: boolean;
  reviewers: Reviewer[];
  onAction: ActionHandler;
}) {
  const isAdmin = ["academic_admin", "platform_admin"].includes(user.role);
  const isReviewer = user.role === "reviewer";
  const canAddEvidence = ["reviewer", "instructor", "academic_admin", "support", "platform_admin"].includes(user.role);
  const ownAssignment = item.reviewers.find((reviewer) => reviewer.user_id === user.id);
  const canDecide = isReviewer && ownAssignment && !ownAssignment.conflict_declared;
  const hasDecision = item.decisions.length > 0;
  const appeal = item.appeals[0];
  const availableReviewers = reviewers.filter((reviewer) => !item.reviewers.some((assigned) => assigned.id === reviewer.id));

  return (
    <div className="grid gap-4">
      <Card className="overflow-hidden">
        <header className="flex flex-wrap items-start justify-between gap-4 border-b border-slate-100 px-5 py-4">
          <div>
            <Eyebrow>{item.submission.submission_key}</Eyebrow>
            <h2 className="mt-1 text-xl font-bold tracking-tight text-slate-900">{item.case_key}</h2>
            <p className="mt-1 text-xs text-slate-500">{item.submission.assessment} · {item.submission.learner_key}</p>
          </div>
          <StatusBadge value={item.status} />
        </header>

        <section className="bg-[#fbf8f5] px-5 py-4">
          <div className="flex items-center justify-between gap-3">
            <div><Eyebrow>Similarity signal</Eyebrow><strong className="mt-1 block text-2xl font-bold tabular-nums text-[#a9593e]">{(item.similarity.score * 100).toFixed(1)}%</strong></div>
            {item.similarity.review_flag && <span className="rounded-full bg-[#f3e5dd] px-3 py-1 text-xs font-semibold text-[#914832]">Review flag</span>}
          </div>
          <div className="mt-3 h-2 overflow-hidden rounded-full bg-[#eaded6]">
            <div className="h-full rounded-full bg-[#b66347]" style={{ width: `${item.similarity.score * 100}%` }} />
          </div>
          <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-slate-500">
            <span>Threshold <strong className="text-slate-700">{(item.similarity.threshold * 100).toFixed(0)}%</strong></span>
            <span>Quoted overlap <strong className="text-slate-700">{item.similarity.quoted_overlap === null ? "Not evaluated" : `${(item.similarity.quoted_overlap * 100).toFixed(1)}%`}</strong></span>
            <span>Template overlap <strong className="text-slate-700">{item.similarity.template_overlap === null ? "Not evaluated" : `${(item.similarity.template_overlap * 100).toFixed(1)}%`}</strong></span>
          </div>
          <p className="mt-3 text-xs leading-5 text-[#826b5f]">Similarity requests contextual review only. It is not proof of intent or misconduct.</p>
        </section>

        <section className="border-t border-slate-100 px-5 py-4">
          <SectionHeading title="Submitted assignment" />
          <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-4 font-sans text-sm leading-6 text-slate-700">
            {item.submission.content_text || "Original synthetic assignment text is not available."}
          </pre>
          {item.similarity.matching_submission_key && (
            <div className="mt-4 border-t border-slate-100 pt-4">
              <SectionHeading title={`Closest comparable · ${item.similarity.matching_submission_key}`} />
              <p className="mt-1 text-xs text-slate-500">Shown to authorized reviewers and staff for contextual comparison.</p>
              <pre className="mt-3 max-h-80 overflow-auto whitespace-pre-wrap break-words rounded-xl bg-slate-50 p-4 font-sans text-sm leading-6 text-slate-700">
                {item.similarity.matching_content_text || "Comparable submission text is unavailable."}
              </pre>
            </div>
          )}
        </section>

        <section className="border-t border-slate-100 px-5 py-4">
          <SectionHeading title="Assigned reviewers" count={item.reviewers.length} />
          <div className="mt-3 grid gap-2 sm:grid-cols-2">
            {item.reviewers.map((reviewer) => (
              <div key={reviewer.id} className="flex items-center gap-2.5 rounded-lg border border-slate-100 p-2.5">
                <span className="grid size-8 shrink-0 place-items-center rounded-full bg-slate-100 text-[10px] font-bold text-slate-600">
                  {reviewer.name.split(" ").map((part) => part[0]).join("")}
                </span>
                <span className="min-w-0 flex-1 text-xs font-medium text-slate-700">{reviewer.name}</span>
                {reviewer.conflict_declared && <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-amber-700"><AlertTriangle size={12} />Conflict</span>}
              </div>
            ))}
            {item.reviewers.length === 0 && <p className="text-xs text-slate-500">No reviewer assigned yet.</p>}
          </div>
          {isAdmin && ["open", "under_review"].includes(item.status) && (
            <form
              className="mt-3 flex flex-wrap gap-2"
              onSubmit={(event) => {
                const data = new FormData(event.currentTarget);
                onAction(event, `/cases/${item.case_key}/reviewers`, { reviewer_id: String(data.get("reviewer_id")) });
              }}
            >
              <select name="reviewer_id" required className="min-h-10 flex-1 rounded-lg border border-slate-200 bg-white px-3 text-xs text-slate-700 outline-none focus:border-[#b96b4e]">
                <option value="">Select a reviewer to assign</option>
                {availableReviewers.map((reviewer) => <option key={reviewer.id} value={reviewer.id}>{reviewer.name} · {reviewer.department}</option>)}
              </select>
              <Button type="submit" disabled={busy || availableReviewers.length === 0}><Plus size={14} />Assign</Button>
            </form>
          )}
        </section>

        <section className="border-t border-slate-100 px-5 py-4">
          <SectionHeading title="Evidence" count={item.evidence.length} />
          <div className="mt-3 grid gap-2">
            {item.evidence.map((evidence) => (
              <article key={evidence.evidence_key} className="flex gap-3 rounded-xl border border-slate-100 p-3">
                <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-slate-50 text-slate-500"><FileText size={15} /></span>
                <div className="min-w-0">
                  <strong className="text-xs font-semibold capitalize text-slate-800">{evidence.kind.replaceAll("_", " ")}</strong>
                  <p className="mt-1 text-xs leading-5 text-slate-600">{evidence.description}</p>
                  <p className="mt-1 break-all text-[10px] text-slate-400">{evidence.evidence_key} · {new Date(evidence.added_at).toLocaleString()}</p>
                </div>
              </article>
            ))}
            {item.evidence.length === 0 && <p className="text-xs text-slate-500">No evidence recorded.</p>}
          </div>
          {canAddEvidence && (
            <form
              className="mt-3 grid gap-3 rounded-xl bg-slate-50 p-3 sm:grid-cols-2"
              onSubmit={(event) => {
                const data = new FormData(event.currentTarget);
                onAction(event, `/cases/${item.case_key}/evidence`, {
                  kind: String(data.get("kind")),
                  source_ref: String(data.get("source_ref")),
                  description: String(data.get("description")),
                });
              }}
            >
              <SelectField label="Evidence type" name="kind">
                <option value="source_context">Source context</option>
                <option value="similarity_excerpt">Similarity excerpt</option>
                <option value="review_note">Review note</option>
              </SelectField>
              <label className="grid gap-1.5 text-sm font-medium text-slate-700">
                Source reference
                <input name="source_ref" minLength={2} required placeholder="URI or citation" className="min-h-11 rounded-lg border border-slate-200 px-3 text-sm outline-none focus:border-[#b96b4e]" />
              </label>
              <TextAreaField className="sm:col-span-2" label="Description and context" name="description" minLength={5} required rows={2} />
              <Button type="submit" disabled={busy} className="sm:col-span-2 sm:justify-self-start"><Plus size={14} />Add evidence to timeline</Button>
            </form>
          )}
        </section>

        {item.decisions.map((decision) => (
          <section key={decision.decision_key} className="border-t border-slate-100 px-5 py-4">
            <SectionHeading title={`Decision · ${decision.outcome.replaceAll("_", " ")}`} />
            <p className="mt-2 text-sm leading-6 text-slate-600">{decision.rationale}</p>
            <p className="mt-2 text-[11px] text-slate-400">{decision.decision_key} · {new Date(decision.decided_at).toLocaleString()}</p>
          </section>
        ))}

        {appeal && (
          <section className="border-t border-slate-100 px-5 py-4">
            <div className="flex items-center justify-between gap-3"><SectionHeading title="Appeal" /><StatusBadge value={appeal.status} /></div>
            <p className="mt-2 text-sm leading-6 text-slate-600">{appeal.reason}</p>
          </section>
        )}
      </Card>

      {isReviewer && !hasDecision && !["closed", "appealed"].includes(item.status) && (
        <Card className="p-5">
          <SectionHeading title="Record a decision" />
          {ownAssignment?.conflict_declared ? (
            <p className="mt-3 rounded-lg bg-amber-50 p-3 text-sm text-amber-800">You declared a conflict for this case and cannot decide it.</p>
          ) : !ownAssignment ? (
            <p className="mt-3 text-sm text-slate-500">Only an assigned, non-conflicted reviewer can record a decision.</p>
          ) : canDecide && (
            <form
              className="mt-4 grid gap-3"
              onSubmit={(event) => {
                const data = new FormData(event.currentTarget);
                onAction(event, `/cases/${item.case_key}/decisions`, {
                  outcome: String(data.get("outcome")),
                  rationale: String(data.get("rationale")),
                });
              }}
            >
              <p className="text-xs leading-5 text-slate-500">Consider the contextual evidence; do not treat the similarity score as a verdict.</p>
              <SelectField label="Decision outcome" name="outcome">
                <option value="not_substantiated">Not substantiated</option>
                <option value="inconclusive">Inconclusive</option>
                <option value="substantiated">Substantiated</option>
              </SelectField>
              <TextAreaField label="Rationale" name="rationale" minLength={20} required rows={3} placeholder="Document the reasoning and evidence considered." />
              <Button type="submit" disabled={busy}><CheckCircle2 size={15} />Save decision</Button>
            </form>
          )}
        </Card>
      )}

      {user.role === "learner" && item.status === "decided" && !appeal && (
        <Card className="p-5">
          <SectionHeading title="Submit an appeal" />
          <form
            className="mt-4 grid gap-3"
            onSubmit={(event) => {
              const data = new FormData(event.currentTarget);
              onAction(event, `/cases/${item.case_key}/appeals`, { reason: String(data.get("reason")) });
            }}
          >
            <TextAreaField label="Appeal grounds" name="reason" minLength={10} required rows={3} placeholder="Explain why you are appealing this decision." />
            <Button type="submit" disabled={busy}><Scale size={15} />Submit appeal</Button>
          </form>
        </Card>
      )}

      <Card className="p-5">
        <SectionHeading title="Case timeline" count={item.timeline.length} />
        <ol className="mt-4 border-l border-slate-200 pl-5">
          {item.timeline.map((event, index) => (
            <li className="relative pb-5 last:pb-0" key={`${event.event_type}-${event.created_at}-${index}`}>
              <span className="absolute -left-[25px] top-1 grid size-3 place-items-center rounded-full border-2 border-white bg-[#b66347] ring-1 ring-[#b66347]" />
              <strong className="text-xs font-semibold capitalize text-slate-800">{event.event_type.replaceAll("_", " ")}</strong>
              <p className="mt-1 text-xs leading-5 text-slate-600">{event.details}</p>
              <time className="mt-1 block text-[10px] text-slate-400">{new Date(event.created_at).toLocaleString()}</time>
            </li>
          ))}
        </ol>
        {item.timeline.length === 0 && <p className="mt-3 text-xs text-slate-500">No timeline events recorded.</p>}
      </Card>
    </div>
  );
}

function SectionHeading({ title, count }: { title: string; count?: number }) {
  return (
    <h3 className="flex items-center gap-2 text-sm font-bold text-slate-800">
      {title}
      {count !== undefined && <span className="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-500">{count}</span>}
      {title === "Appeal" && <ArrowUpRight size={14} className="text-slate-400" />}
    </h3>
  );
}
