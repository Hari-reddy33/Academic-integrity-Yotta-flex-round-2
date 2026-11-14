import { useCallback, useEffect, useState } from "react";
import type { FormEvent } from "react";

import { AppShell } from "./components/AppShell";
import { Button } from "./components/ui";
import { apiRequest, authenticate } from "./lib/api";
import { AppealsPage } from "./pages/AppealsPage";
import { DashboardPage } from "./pages/DashboardPage";
import { LoginPage } from "./pages/LoginPage";
import { ReportsPage } from "./pages/ReportsPage";
import { ReviewersPage } from "./pages/ReviewersPage";
import { SimilarityPage } from "./pages/SimilarityPage";
import { CaseWorkspace } from "./features/cases/CaseWorkspace";
import { SubmitAssignmentPage, MySubmissionsPage } from "./pages/SubmissionPages";
import type {
  AssessmentOption,
  AppealRow,
  CaseDetail,
  CaseSummary,
  Metrics,
  Page,
  Report,
  Reviewer,
  SimilarityResult,
  SubmissionDetail,
  SubmissionRow,
  User,
} from "./types";

const storedToken = () => localStorage.getItem("integrity-token") ?? "";

export default function App() {
  const [token, setToken] = useState(storedToken);
  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(Boolean(storedToken()));
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [page, setPage] = useState<Page>("dashboard");
  const [statusFilter, setStatusFilter] = useState("");
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [selectedCase, setSelectedCase] = useState<CaseDetail | null>(null);
  const [reports, setReports] = useState<Report[]>([]);
  const [appeals, setAppeals] = useState<AppealRow[]>([]);
  const [reviewers, setReviewers] = useState<Reviewer[]>([]);
  const [similarityResult, setSimilarityResult] = useState<SimilarityResult | null>(null);
  const [assessments, setAssessments] = useState<AssessmentOption[]>([]);
  const [submissions, setSubmissions] = useState<SubmissionRow[]>([]);
  const [selectedSubmission, setSelectedSubmission] = useState<SubmissionDetail | null>(null);
  const [submissionSuccess, setSubmissionSuccess] = useState("");

  const refresh = useCallback(async (activeToken: string) => {
    try {
      const [currentUser, currentMetrics, caseRows] = await Promise.all([
        apiRequest<User>("/auth/me", activeToken),
        apiRequest<Metrics>("/dashboard", activeToken),
        apiRequest<CaseSummary[]>(
          `/cases?limit=500${statusFilter ? `&status=${encodeURIComponent(statusFilter)}` : ""}`,
          activeToken,
        ),
      ]);
      setUser((previous) => (
        previous?.id === currentUser.id && previous.role === currentUser.role ? previous : currentUser
      ));
      setPage((current) => (
        currentUser.role === "learner" && current === "dashboard" ? "submit" : current
      ));
      setMetrics(currentMetrics);
      setCases(caseRows);
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to load the workspace");
    } finally {
      setAuthLoading(false);
    }
  }, [statusFilter]);

  useEffect(() => {
    if (token) void refresh(token);
    else setAuthLoading(false);
  }, [page, token, refresh]);

  useEffect(() => {
    if (!token || !user) return;
    const loadPageData = async () => {
      try {
        if (page === "reports") setReports(await apiRequest<Report[]>("/reports?limit=1000", token));
        if (page === "appeals") setAppeals(await apiRequest<AppealRow[]>("/appeals", token));
        if (page === "submit") setAssessments(await apiRequest<AssessmentOption[]>("/submissions/assessments", token));
        if (page === "submissions") {
          setSubmissions(await apiRequest<SubmissionRow[]>("/submissions?limit=100", token));
          setSelectedSubmission(null);
        }
      } catch (reason) {
        setError(reason instanceof Error ? reason.message : "Unable to load this workspace");
      }
    };
    void loadPageData();
  }, [page, token, user]);

  useEffect(() => {
    if (!token || !user || !["academic_admin", "platform_admin"].includes(user.role)) return;
    apiRequest<Reviewer[]>("/reviewers", token)
      .then(setReviewers)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : "Unable to load reviewers"));
  }, [token, user]);

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    try {
      const nextToken = await authenticate(String(form.get("email")), String(form.get("password")));
      localStorage.setItem("integrity-token", nextToken);
      setAuthLoading(true);
      setToken(nextToken);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Sign-in failed");
    } finally {
      setBusy(false);
    }
  }

  async function openSubmission(submissionKey: string) {
    if (!token) return;
    setBusy(true);
    setError("");
    try {
      setSelectedSubmission(await apiRequest<SubmissionDetail>(
        `/submissions/${submissionKey}`,
        token,
      ));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to open submission");
    } finally {
      setBusy(false);
    }
  }

  async function openCase(row: CaseSummary) {
    if (!token) return;
    try {
      const detail = await apiRequest<CaseDetail>(`/cases/${row.case_key}`, token);
      setSelectedCase(detail);
      setPage("cases");
      setError("");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Unable to open case");
    }
  }

  async function submitAction(event: FormEvent<HTMLFormElement>, path: string, values: Record<string, string>) {
    event.preventDefault();
    if (!token) return;
    setBusy(true);
    try {
      await apiRequest(path, token, { method: "POST", body: JSON.stringify(values) });
      await refresh(token);
      if (page === "appeals") {
        setAppeals(await apiRequest<AppealRow[]>("/appeals", token));
      }
      if (selectedCase) {
        setSelectedCase(await apiRequest<CaseDetail>(`/cases/${selectedCase.case_key}`, token));
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  async function resolveAppeal(event: FormEvent<HTMLFormElement>, appealKey: string, values: Record<string, string>) {
    event.preventDefault();
    if (!token) return;
    setBusy(true);
    try {
      await apiRequest(`/appeals/${appealKey}/resolve`, token, {
        method: "POST",
        body: JSON.stringify(values),
      });
      setAppeals(await apiRequest<AppealRow[]>("/appeals", token));
      await refresh(token);
      if (selectedCase) {
        setSelectedCase(await apiRequest<CaseDetail>(`/cases/${selectedCase.case_key}`, token));
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Appeal resolution failed");
    } finally {
      setBusy(false);
    }
  }

  async function analyzeSimilarity(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const payload = {
      text_a: String(form.get("text_a")),
      text_b: String(form.get("text_b")),
    };
    setBusy(true);
    setError("");
    try {
      setSimilarityResult(await apiRequest<SimilarityResult>("/similarity/compare", token, {
        method: "POST",
        body: JSON.stringify(payload),
      }));
      formElement.reset();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Similarity analysis failed");
    } finally {
      setBusy(false);
    }
  }

  async function submitAssignment(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    setBusy(true);
    setError("");
    setSubmissionSuccess("");
    try {
      const result = await apiRequest<{
        submission_key: string;
        similarity_score: number;
        threshold: number;
        review_flag: boolean;
        case_key: string | null;
        comparison_available: boolean;
      }>("/submissions", token, {
        method: "POST",
        body: JSON.stringify({
          assessment_id: Number(form.get("assessment_id")),
          content_text: String(form.get("content_text")),
        }),
      });
      formElement.reset();
      const score = `${(result.similarity_score * 100).toFixed(1)}%`;
      const threshold = `${(result.threshold * 100).toFixed(0)}%`;
      const outcome = result.review_flag
        ? `A human-review case (${result.case_key}) was opened. This is not a misconduct finding.`
        : result.comparison_available
          ? `The score is below the ${threshold} review threshold; no case was opened.`
          : "No comparable text was available yet, so no review case was opened.";
      setSubmissionSuccess(
        `${result.submission_key} was received. Analysis completed at ${score}. ${outcome}`,
      );
      setSubmissions(await apiRequest<SubmissionRow[]>("/submissions?limit=100", token));
      await refresh(token);
      setSelectedSubmission(null);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Assignment submission failed");
    } finally {
      setBusy(false);
    }
  }

  async function submitAppeal(event: FormEvent<HTMLFormElement>, caseKey: string, reason: string) {
    event.preventDefault();
    if (!token) return;
    setBusy(true);
    setError("");
    try {
      await apiRequest(`/cases/${caseKey}/appeals`, token, {
        method: "POST",
        body: JSON.stringify({ reason }),
      });
      setAppeals(await apiRequest<AppealRow[]>("/appeals", token));
      await refresh(token);
    } catch (reasonError) {
      setError(reasonError instanceof Error ? reasonError.message : "Appeal submission failed");
    } finally {
      setBusy(false);
    }
  }

  function signOut() {
    localStorage.removeItem("integrity-token");
    setToken("");
    setUser(null);
    setMetrics(null);
    setCases([]);
    setSelectedCase(null);
    setReports([]);
    setAppeals([]);
    setReviewers([]);
    setAssessments([]);
    setSubmissions([]);
    setSelectedSubmission(null);
    setPage("dashboard");
    setSimilarityResult(null);
    setError("");
    setSubmissionSuccess("");
  }

  if (authLoading) {
    return <main className="grid min-h-screen place-items-center bg-slate-50 text-sm text-slate-500">Checking your session…</main>;
  }

  if (!token || !user) return <LoginPage busy={busy} error={error} onSubmit={login} />;

  const isAdmin = ["academic_admin", "platform_admin"].includes(user.role);
  const handleReportCase = (caseKey: string | null) => {
    const row = cases.find((candidate) => candidate.case_key === caseKey);
    if (row) void openCase(row);
  };

  return (
    <AppShell user={user} page={page} onNavigate={setPage} onSignOut={signOut}>
      {error && (
        <div role="alert" className="mb-5 flex items-center justify-between gap-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-800">
          <span>{error}</span>
          <Button variant="quiet" className="min-h-8 px-2 text-xs" onClick={() => setError("")}>Dismiss</Button>
        </div>
      )}
      {page === "dashboard" && user.role !== "learner" && (
        <DashboardPage
          metrics={metrics}
          cases={cases}
          onNavigate={setPage}
          onOpenCase={(row) => void openCase(row)}
        />
      )}
      {page === "cases" && (
        <CaseWorkspace
          cases={cases}
          selected={selectedCase}
          statusFilter={statusFilter}
          setStatusFilter={setStatusFilter}
          onOpenCase={openCase}
          user={user}
          busy={busy}
          reviewers={reviewers}
          onAction={submitAction}
        />
      )}
      {page === "reports" && user.role !== "learner" && <ReportsPage reports={reports} onOpenCase={handleReportCase} />}
      {page === "appeals" && (
        <AppealsPage
          appeals={appeals}
          eligibleCases={user.role === "learner" ? cases.filter((item) => item.status === "decided" && item.decision_count > 0 && !item.appeal_status) : []}
          user={user}
          busy={busy}
          reviewers={reviewers}
          onAction={submitAction}
          onResolve={resolveAppeal}
          onSubmitAppeal={submitAppeal}
        />
      )}
      {page === "similarity" && user.role !== "learner" && <SimilarityPage busy={busy} result={similarityResult} onAnalyze={analyzeSimilarity} />}
      {page === "reviewers" && isAdmin && <ReviewersPage reviewers={reviewers} />}
      {page === "submit" && user.role === "learner" && (
        <SubmitAssignmentPage assessments={assessments} busy={busy} success={submissionSuccess} onSubmit={submitAssignment} />
      )}
      {page === "submissions" && (
        <MySubmissionsPage
          submissions={submissions}
          selected={selectedSubmission}
          user={user}
          busy={busy}
          onOpenSubmission={openSubmission}
          onOpenCase={handleReportCase}
        />
      )}
    </AppShell>
  );
}
