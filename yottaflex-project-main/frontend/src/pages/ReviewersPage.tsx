import { UsersRound } from "lucide-react";

import { Card, Eyebrow } from "../components/ui";
import type { Reviewer } from "../types";

export function ReviewersPage({ reviewers }: { reviewers: Reviewer[] }) {
  return (
    <Card className="p-5">
      <header className="mb-5 flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 pb-4">
        <div><Eyebrow>Administration</Eyebrow><h2 className="mt-1 text-lg font-bold text-slate-900">Reviewer directory</h2></div>
        <span className="text-xs text-slate-500">Assignment is managed from an open case</span>
      </header>
      {reviewers.length === 0 ? (
        <div className="grid min-h-40 place-items-center text-center">
          <div><UsersRound className="mx-auto text-slate-300" /><p className="mt-3 text-sm text-slate-600">No reviewers found.</p></div>
        </div>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
          {reviewers.map((reviewer) => (
            <article key={reviewer.id} className="flex items-center gap-3 rounded-xl border border-slate-200 p-4">
              <span className="grid size-10 shrink-0 place-items-center rounded-full bg-[#f7eae5] text-xs font-bold text-[#9b5038]">
                {reviewer.name.split(" ").map((part) => part[0]).join("")}
              </span>
              <span className="min-w-0 flex-1">
                <strong className="block truncate text-sm font-semibold text-slate-800">{reviewer.name}</strong>
                <span className="mt-1 block text-xs text-slate-500">{reviewer.department}</span>
              </span>
              <span className="shrink-0 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-semibold text-emerald-700">
                {reviewer.active_cases} active
              </span>
            </article>
          ))}
        </div>
      )}
      <p className="mt-5 text-xs leading-5 text-slate-500">
        Reviewer conflicts are declared per case and prevent that reviewer from recording decisions or resolving appeals.
      </p>
    </Card>
  );
}
