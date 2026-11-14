import { Scale } from "lucide-react";
import { useState, type FormEvent } from "react";

import { Button, Card, Eyebrow, Field, SelectField } from "../components/ui";

const demoAccounts = [
  { email: "learner@demo.local", role: "Learner" },
  { email: "learner2@demo.local", role: "Learner 2 (similarity test)" },
  { email: "instructor@demo.local", role: "Instructor" },
  { email: "admin@demo.local", role: "Academic administrator" },
  { email: "support@demo.local", role: "Support staff" },
  { email: "platform@demo.local", role: "Platform administrator" },
  { email: "reviewer1@demo.local", role: "Reviewer 1" },
  { email: "reviewer2@demo.local", role: "Reviewer 2 (conflict case)" },
  { email: "reviewer3@demo.local", role: "Reviewer 3" },
  { email: "reviewer4@demo.local", role: "Reviewer 4" },
];
const demoPassword = "demo1234";

export function LoginPage({ busy, error, onSubmit }: {
  busy: boolean;
  error: string;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
}) {
  const [selectedAccountEmail, setSelectedAccountEmail] = useState("reviewer1@demo.local");
  const [email, setEmail] = useState("reviewer1@demo.local");
  const [password, setPassword] = useState(demoPassword);

  return (
    <main className="grid min-h-screen place-items-center bg-[#f6f7f9] px-4 py-10">
      <Card className="w-full max-w-[440px] p-7 shadow-lg shadow-slate-900/[0.04] sm:p-9">
        <div className="mb-7 grid size-12 place-items-center rounded-2xl bg-[#a9593e] text-white shadow-md shadow-[#a9593e]/20">
          <Scale size={23} />
        </div>
        <Eyebrow>Academic integrity</Eyebrow>
        <h1 className="mt-2 text-3xl font-bold tracking-tight text-slate-900">Integrity Desk</h1>
        <p className="mt-2 text-sm leading-6 text-slate-500">
          A human-centered workspace for fair, evidence-based review.
        </p>

        <form className="mt-7 grid gap-4" onSubmit={onSubmit}>
          <SelectField
            label="Choose a demo role"
            name="demoAccount"
            value={selectedAccountEmail}
            onChange={(event) => {
              const account = demoAccounts.find((item) => item.email === event.target.value);
              setSelectedAccountEmail(account?.email ?? "");
              setEmail(account?.email ?? "");
              setPassword(demoPassword);
            }}
          >
            <option value="">Custom email</option>
            {demoAccounts.map((account) => (
              <option value={account.email} key={account.email}>{account.role}</option>
            ))}
          </SelectField>
          <Field
            label="Email"
            name="email"
            type="email"
            autoComplete="username"
            value={email}
            onChange={(event) => {
              setEmail(event.target.value);
              if (event.target.value !== selectedAccountEmail) setSelectedAccountEmail("");
            }}
            required
          />
          <label className="grid gap-1.5 text-sm font-medium text-slate-700">
            Password
            <input
              name="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              required
              className="min-h-11 w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm outline-none transition focus:border-[#b96b4e] focus:ring-4 focus:ring-[#b96b4e]/10"
            />
          </label>
          {error && <p role="alert" className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2.5 text-sm text-rose-700">{error}</p>}
          <Button type="submit" disabled={busy} className="mt-1 w-full">
            {busy ? "Signing in..." : "Sign in"}
          </Button>
        </form>

        <div className="mt-6 rounded-xl bg-slate-50 p-3.5 text-xs leading-5 text-slate-500">
          Demo password: <strong className="font-semibold text-slate-700">{demoPassword}</strong>. Similarity flags initiate human review; they never establish guilt.
        </div>
      </Card>
    </main>
  );
}
