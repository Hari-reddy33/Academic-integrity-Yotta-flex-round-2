import {
  Activity,
  ClipboardList,
  FileSearch,
  FilePlus2,
  Files,
  LayoutDashboard,
  LogOut,
  Scale,
  ScanSearch,
  UsersRound,
} from "lucide-react";
import type { ReactNode } from "react";

import type { Page, User } from "../types";

const staffNavItems = [
  { id: "dashboard", label: "Dashboard", icon: LayoutDashboard },
  { id: "cases", label: "Case management", icon: ClipboardList },
  { id: "submissions", label: "Submissions", icon: Files },
  { id: "reports", label: "Similarity reports", icon: FileSearch },
] as const;

export function AppShell({ user, page, onNavigate, onSignOut, children }: {
  user: User;
  page: Page;
  onNavigate: (page: Page) => void;
  onSignOut: () => void;
  children: ReactNode;
}) {
  const isLearner = user.role === "learner";
  const isAdmin = ["academic_admin", "platform_admin"].includes(user.role);
  const items = isLearner
    ? [
      { id: "submit" as const, label: "Submit assignment", icon: FilePlus2 },
      { id: "submissions" as const, label: "My submissions", icon: Files },
      { id: "cases" as const, label: "My cases", icon: ClipboardList },
      { id: "appeals" as const, label: "My appeals", icon: Scale },
    ]
    : [
      ...staffNavItems,
      ...(user.role === "instructor" || user.role === "reviewer" || isAdmin
        ? [{ id: "similarity" as const, label: "Similarity lab", icon: ScanSearch }]
        : []),
      ...(user.role === "reviewer" || user.role === "support" || isAdmin
        ? [{ id: "appeals" as const, label: "Appeals", icon: Scale }]
        : []),
      ...(isAdmin ? [{ id: "reviewers" as const, label: "Reviewer management", icon: UsersRound }] : []),
    ];
  const currentPage = items.find((item) => item.id === page);
  const title = currentPage?.label ?? "Dashboard";

  return (
    <div className="min-h-screen bg-[#f6f7f9] text-slate-800 lg:grid lg:grid-cols-[256px_minmax(0,1fr)]">
      <aside className="flex flex-col bg-[#162238] px-3 py-3 text-white lg:fixed lg:inset-y-0 lg:w-64 lg:px-5 lg:py-7">
        <a href="#" className="mb-4 flex items-center gap-3 px-2 lg:mb-8" onClick={(event) => { event.preventDefault(); onNavigate("dashboard"); }}>
          <span className="grid size-10 place-items-center rounded-xl bg-[#b66347] text-sm font-extrabold tracking-wide">ID</span>
          <span>
            <span className="block font-bold tracking-tight">Integrity Desk</span>
            <span className="mt-0.5 block text-xs text-slate-400">Review workspace</span>
          </span>
        </a>

        <p className="mb-2 hidden px-3 text-[10px] font-bold uppercase tracking-[0.17em] text-slate-500 lg:block">Workspace</p>
        <nav className="flex gap-1 overflow-x-auto lg:grid lg:overflow-visible" aria-label="Main navigation">
          {items.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => onNavigate(id)}
              className={`flex min-h-10 shrink-0 items-center gap-2 rounded-lg px-3 text-left text-xs transition lg:min-h-11 lg:gap-3 lg:text-sm ${
                page === id
                  ? "bg-white/10 font-semibold text-white ring-1 ring-inset ring-white/10"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon size={17} strokeWidth={1.8} />
              {label}
            </button>
          ))}
        </nav>

        <div className="mt-8 hidden rounded-xl border border-white/10 bg-white/[0.04] p-4 lg:block">
          <div className="flex items-center gap-2 text-xs font-semibold text-white">
            <Activity size={15} className="text-emerald-400" />
            Due process first
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-400">
            Similarity scores prompt contextual review; they are never verdicts.
          </p>
        </div>

        <div className="mt-3 border-t border-white/10 pt-3 lg:mt-auto lg:pt-5">
          <div className="flex items-center gap-3 px-1 lg:gap-3">
            <span className="grid size-9 shrink-0 place-items-center rounded-full bg-[#dbe7ef] text-xs font-bold text-[#314b68]">
              {user.full_name.split(" ").map((word) => word[0]).slice(0, 2).join("")}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block truncate text-xs font-semibold">{user.full_name}</span>
              <span className="mt-1 block truncate text-[11px] capitalize text-slate-400">{user.role.replaceAll("_", " ")}</span>
            </span>
            <button onClick={onSignOut} title="Sign out" className="rounded-md p-2 text-slate-400 transition hover:bg-white/10 hover:text-white">
              <LogOut size={16} />
            </button>
          </div>
        </div>
      </aside>

      <div className="min-w-0 lg:col-start-2 lg:pl-0">
        <header className="sticky top-0 z-10 flex min-h-20 items-center justify-between border-b border-slate-200/80 bg-white/90 px-5 backdrop-blur md:px-8">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-slate-400">Integrity Desk / {title}</p>
            <h1 className="mt-1 text-xl font-bold tracking-tight text-slate-900">{title}</h1>
          </div>
          <span className="hidden items-center gap-2 rounded-full border border-slate-200 bg-white px-3 py-1.5 text-xs capitalize text-slate-600 sm:inline-flex">
            <span className="size-1.5 rounded-full bg-emerald-500" />
            {user.role.replaceAll("_", " ")}
          </span>
        </header>
        <main className="mx-auto w-full max-w-[1500px] p-4 md:p-8">
          {children}
          <footer className="mt-8 flex items-center justify-between gap-4 border-t border-slate-200 pt-4 text-xs text-slate-400">
            <span>Human review required</span>
            <span>Evidence and rationale are retained in the case timeline</span>
          </footer>
        </main>
      </div>
    </div>
  );
}
