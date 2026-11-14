import type { FormEvent } from "react";
import { ScanSearch, ShieldCheck } from "lucide-react";

import { Button, Card, Eyebrow, StatusBadge, TextAreaField } from "../components/ui";
import type { SimilarityResult } from "../types";

export function SimilarityPage({ busy, result, onAnalyze }: {
  busy: boolean;
  result: SimilarityResult | null;
  onAnalyze: (event: FormEvent<HTMLFormElement>) => void;
}) {
  return (
    <div className="grid items-start gap-5 xl:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.75fr)]">
      <Card className="p-5 sm:p-6">
        <div className="flex items-center gap-2 text-[#a9593e]"><ScanSearch size={18} /><Eyebrow>Local NLP baseline</Eyebrow></div>
        <h2 className="mt-2 text-lg font-bold text-slate-900">Compare two text passages</h2>
        <p className="mt-2 max-w-2xl text-sm leading-6 text-slate-500">
          TF-IDF word and phrase overlap runs for this request only. Text is not retained. The score is a review signal, not a finding.
        </p>
        <form className="mt-6 grid gap-4" onSubmit={onAnalyze}>
          <TextAreaField
            label="Submission passage"
            name="text_a"
            minLength={30}
            maxLength={100_000}
            required
            rows={7}
            placeholder="Paste an assignment passage (30–100,000 characters)."
          />
          <TextAreaField
            label="Reference passage"
            name="text_b"
            minLength={30}
            maxLength={100_000}
            required
            rows={7}
            placeholder="Paste a comparison passage."
          />
          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={busy}>{busy ? "Comparing..." : "Compare passages"}</Button>
            <span className="text-xs text-slate-400">Inputs clear after submit</span>
          </div>
        </form>
      </Card>

      <Card className="p-5 sm:p-6">
        <div className="flex items-center gap-2 text-[#a9593e]"><ShieldCheck size={18} /><Eyebrow>Analysis result</Eyebrow></div>
        {!result ? (
          <div className="grid min-h-56 place-items-center text-center">
            <div><ScanSearch size={26} className="mx-auto text-slate-300" /><p className="mt-3 text-sm text-slate-500">Run a comparison to see a transparent score, shared terms and review threshold.</p></div>
          </div>
        ) : (
          <>
            <div className="mt-5 flex items-end gap-1 text-[#a9593e]">
              <span className="text-5xl font-bold tracking-tight tabular-nums">{(result.score * 100).toFixed(1)}</span>
              <span className="mb-1 text-xl font-semibold">%</span>
            </div>
            <div className="mt-3"><StatusBadge value={result.review_flag ? "under_review" : "below_threshold"} /></div>
            <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100">
              <div className="h-full rounded-full bg-[#b66347] transition-all" style={{ width: `${result.score * 100}%` }} />
            </div>
            <p className="mt-2 text-xs text-slate-500">Review threshold {(result.threshold * 100).toFixed(0)}% · {result.model}</p>
            <p className="mt-4 rounded-xl bg-[#fbf6f2] p-3 text-xs leading-5 text-[#826b5f]">{result.notice}</p>
            <h3 className="mt-5 text-sm font-semibold text-slate-800">Shared terms</h3>
            <div className="mt-2 flex flex-wrap gap-2">
              {result.shared_terms.map((term) => (
                <span key={term.term} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs text-slate-600">{term.term}</span>
              ))}
              {result.shared_terms.length === 0 && <span className="text-xs text-slate-500">No shared terms identified.</span>}
            </div>
            <p className="mt-4 text-xs text-slate-400">Input retained: {result.input_retained ? "yes" : "no"}</p>
          </>
        )}
      </Card>
    </div>
  );
}
