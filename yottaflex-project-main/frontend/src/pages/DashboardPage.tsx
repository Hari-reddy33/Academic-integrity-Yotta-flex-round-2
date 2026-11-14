import { ArrowRight, ClipboardList, FileSearch, Scale, ScanSearch, ShieldCheck } from "lucide-react";

import { Button, Card, Eyebrow, StatusBadge } from "../components/ui";
import type { CaseSummary, Metrics, Page } from "../types";

const metricCards = [
  { key: "total_cases", label: "All cases", icon: ClipboardList, color: "bg-slate-100 text-slate-600" },
  { key: "open_cases", label: "Open reviews", icon: ScanSearch, color: "bg-amber-50 text-amber-700" },
  { key: "flagged_reports", label: "Similarity flags", icon: FileSearch, color: "bg-sky-50 text-sky-700" },
  { key: "pending_appeals", label: "Pending appeals", icon: Scale, color: "bg-violet-50 text-violet-700" },
] as const;

export function DashboardPage({ metrics, cases, onNavigate, onOpenCase }: {
  metrics: Metrics | null;
  cases: CaseSummary[];
  onNavigate: (page: Page) => void;
  onOpenCase: (row: CaseSummary) => void;
}) {
  return (
    <div className="grid gap-5">
      <section className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-4">
        {metricCards.map(({ key, label, icon: Icon, color }) => (
          <Card key={key} className="flex items-center gap-4 p-5">
            <span className={`grid size-11 shrink-0 place-items-center rounded-xl ${color}`}><Icon size={20} /></span>
            <span>
              <span className="block text-sm text-slate-500">{label}</span>
              <strong className="mt-1 block text-2xl font-bold tracking-tight text-slate-900">
                {metrics?.[key] ?? "—"}
              </strong>
            </span>
          </Card>
        ))}
      </section>

      <section className="grid gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.8fr)]">
        <Card className="overflow-hidden">
          <header className="flex items-end justify-between gap-4 border-b border-slate-100 px-5 py-4">
            <div><Eyebrow>Recent activity</Eyebrow><h2 className="mt-1 text-lg font-bold text-slate-900">Case queue</h2></div>
            <Button variant="quiet" className="min-h-9 px-2 text-xs" onClick={() => onNavigate("cases")}>
              View all <ArrowRight size={14} />
            </Button>
          </header>
          <div className="divide-y divide-slate-100 px-5">
            {cases.slice(0, 6).map((row) => (
              <button
                key={row.case_key}
                onClick={() => onOpenCase(row)}
                className="flex w-full items-center justify-between gap-4 py-4 text-left transition hover:bg-slate-50"
              >
                <span className="min-w-0">
                  <strong className="block text-sm font-semibold text-slate-800">{row.case_key}</strong>
                  <span className="mt-1 block text-xs text-slate-500">
                    Evidence {row.evidence_count} · Decisions {row.decision_count}
                  </span>
                </span>
                <StatusBadge value={row.status} />
              </button>
            ))}
            {cases.length === 0 && (
              <p className="py-12 text-center text-sm text-slate-500">No cases are currently available to this account.</p>
            )}
          </div>
        </Card>

        <Card className="p-5">
          <div className="flex items-center gap-2 text-[#a9593e]"><ShieldCheck size={18} /><Eyebrow>Review standard</Eyebrow></div>
          <h2 className="mt-2 text-lg font-bold text-slate-900">Signals are not verdicts</h2>
          <p className="mt-2 text-sm leading-6 text-slate-500">
            Similarity scores identify work that may need contextual review. They do not prove copying or intent.
          </p>
          <div className="mt-5 grid gap-4 border-l border-slate-200 pl-4">
            {[
              ["Review context", "Check quotations, shared templates and attribution."],
              ["Record evidence", "Keep sources, rationale and timeline events."],
              ["Allow appeal", "Send appeals to a different reviewer."],
            ].map(([title, detail], index) => (
              <div key={title} className="relative">
                <span className="absolute -left-[21px] top-0.5 grid size-3.5 place-items-center rounded-full bg-[#f6e8e2] text-[8px] font-bold text-[#a9593e]">
                  {index + 1}
                </span>
                <strong className="block text-sm font-semibold text-slate-800">{title}</strong>
                <span className="mt-1 block text-xs leading-5 text-slate-500">{detail}</span>
              </div>
            ))}
          </div>
          <Button variant="secondary" className="mt-6 w-full" onClick={() => onNavigate("similarity")}>
            Open Similarity Lab <ArrowRight size={15} />
          </Button>
        </Card>
      </section>
    </div>
  );
}
