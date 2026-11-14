import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "secondary" | "quiet" | "danger" };

const buttonStyles = {
  primary: "bg-[#a9593e] text-white shadow-sm hover:bg-[#914832] focus-visible:ring-[#d9a28d]",
  secondary: "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50 focus-visible:ring-slate-300",
  quiet: "text-slate-500 hover:bg-slate-100 hover:text-slate-800 focus-visible:ring-slate-300",
  danger: "bg-rose-50 text-rose-700 hover:bg-rose-100 focus-visible:ring-rose-300",
};

export function Button({ variant = "primary", className = "", ...props }: ButtonProps) {
  return (
    <button
      className={`inline-flex min-h-10 items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 disabled:cursor-not-allowed disabled:opacity-50 ${buttonStyles[variant]} ${className}`}
      {...props}
    />
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-2xl border border-slate-200/80 bg-white shadow-sm ${className}`}>{children}</section>;
}

export function Eyebrow({ children }: { children: ReactNode }) {
  return <p className="text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">{children}</p>;
}

export function Field({ label, className = "", ...props }: InputHTMLAttributes<HTMLInputElement> & { label: string }) {
  return (
    <label className={`grid gap-1.5 text-sm font-medium text-slate-700 ${className}`}>
      {label}
      <input
        className="min-h-11 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-[#b96b4e] focus:ring-4 focus:ring-[#b96b4e]/10"
        {...props}
      />
    </label>
  );
}

export function SelectField({ label, className = "", children, ...props }: SelectHTMLAttributes<HTMLSelectElement> & { label: string; children: ReactNode }) {
  return (
    <label className={`grid gap-1.5 text-sm font-medium text-slate-700 ${className}`}>
      {label}
      <select
        className="min-h-11 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm text-slate-800 outline-none transition focus:border-[#b96b4e] focus:ring-4 focus:ring-[#b96b4e]/10"
        {...props}
      >
        {children}
      </select>
    </label>
  );
}

export function TextAreaField({ label, className = "", ...props }: TextareaHTMLAttributes<HTMLTextAreaElement> & { label: string }) {
  return (
    <label className={`grid gap-1.5 text-sm font-medium text-slate-700 ${className}`}>
      {label}
      <textarea
        className="min-h-24 w-full resize-y rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm leading-6 text-slate-800 outline-none transition focus:border-[#b96b4e] focus:ring-4 focus:ring-[#b96b4e]/10"
        {...props}
      />
    </label>
  );
}

const statusStyles: Record<string, string> = {
  open: "bg-sky-50 text-sky-700 ring-sky-200",
  under_review: "bg-amber-50 text-amber-800 ring-amber-200",
  appealed: "bg-violet-50 text-violet-700 ring-violet-200",
  decided: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  closed: "bg-slate-100 text-slate-600 ring-slate-200",
  resolved: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  overturned: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  upheld: "bg-slate-100 text-slate-600 ring-slate-200",
  below_threshold: "bg-slate-100 text-slate-600 ring-slate-200",
  pending: "bg-amber-50 text-amber-800 ring-amber-200",
  complete: "bg-emerald-50 text-emerald-700 ring-emerald-200",
};

export function StatusBadge({ value }: { value: string }) {
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold capitalize ring-1 ring-inset ${statusStyles[value] ?? statusStyles.closed}`}>
      {value.replaceAll("_", " ")}
    </span>
  );
}

export function EmptyState({ title, description }: { title: string; description: string }) {
  return (
    <div className="grid min-h-48 place-items-center rounded-xl border border-dashed border-slate-200 bg-slate-50/70 px-6 text-center">
      <div>
        <p className="font-semibold text-slate-700">{title}</p>
        <p className="mt-1 max-w-sm text-sm leading-6 text-slate-500">{description}</p>
      </div>
    </div>
  );
}
