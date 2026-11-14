import { FileSearch } from "lucide-react";

import { Card, Eyebrow, StatusBadge } from "../components/ui";
import type { Report } from "../types";

export function ReportsPage({ reports, onOpenCase }: {
  reports: Report[];
  onOpenCase: (caseKey: string | null) => void;
}) {
  return (
    <Card className="overflow-hidden">
      <header className="flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 px-5 py-4">
        <div><Eyebrow>Model outputs</Eyebrow><h2 className="mt-1 text-lg font-bold text-slate-900">Similarity reports</h2></div>
        <span className="text-xs text-slate-500">Flags request human review only</span>
      </header>
      {reports.length === 0 ? (
        <div className="p-5"><div className="grid min-h-44 place-items-center text-center"><div><FileSearch className="mx-auto text-slate-300" /><p className="mt-3 text-sm text-slate-600">No similarity reports available.</p></div></div></div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[980px] border-collapse text-left text-sm">
            <thead className="bg-slate-50 text-[11px] uppercase tracking-wide text-slate-500">
              <tr>{["Report / submission", "Assessment", "Compared with", "Score", "Threshold", "Review state", "Case"].map((item) => <th className="px-5 py-3 font-semibold" key={item}>{item}</th>)}</tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {reports.map((report) => (
                <tr key={report.report_key} className="hover:bg-slate-50/70">
                  <td className="px-5 py-3.5"><strong className="block text-xs font-semibold text-slate-800">{report.report_key}</strong><span className="mt-1 block text-xs text-slate-500">{report.submission_key}</span></td>
                  <td className="px-5 py-3.5 text-slate-600">{report.assessment}</td>
                  <td className="px-5 py-3.5 font-mono text-xs text-slate-500">{report.matching_submission_key ?? "No comparison"}</td>
                  <td className="px-5 py-3.5 font-semibold tabular-nums text-slate-800">{(report.score * 100).toFixed(1)}%</td>
                  <td className="px-5 py-3.5 tabular-nums text-slate-500">{(report.threshold * 100).toFixed(0)}%</td>
                  <td className="px-5 py-3.5"><StatusBadge value={report.review_flag ? "under_review" : "below_threshold"} /></td>
                  <td className="px-5 py-3.5">
                    {report.case_key
                      ? <button className="font-semibold text-[#a9593e] hover:underline" onClick={() => onOpenCase(report.case_key)}>{report.case_key} →</button>
                      : <span className="text-slate-400">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </Card>
  );
}
