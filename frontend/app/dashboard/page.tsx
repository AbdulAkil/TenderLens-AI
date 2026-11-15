"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { TenderCard } from "@/components/tender-card";
import {
  activeCompany,
  api,
  type Account,
  type Company,
  type Match,
} from "@/lib/api";
export default function Dashboard() {
  return (
    <AppShell>
      <Content />
    </AppShell>
  );
}
function Content() {
  const [company, setCompany] = useState<Company | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [account, setAccount] = useState<Account | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    Promise.all([
      activeCompany().then(async (company) => {
        setCompany(company);
        if (company)
          setMatches(
            await api<Match[]>(`/companies/${company.id}/matches?limit=20`),
          );
      }),
      api<Account>("/auth/me").then(setAccount),
    ])
      .catch((cause) => setError(String(cause)))
      .finally(() => setLoading(false));
  }, []);
  const refresh = async () => {
    if (!company) return;
    setBusy(true);
    try {
      const result = await api<{ items: Match[] }>(
        `/companies/${company.id}/matches/recalculate`,
        { method: "POST" },
      );
      setMatches(result.items);
      setError("");
    } catch (cause) {
      setError(String(cause));
    } finally {
      setBusy(false);
    }
  };
  const upcoming = matches.filter(
    (match) =>
      match.tender?.submission_deadline &&
      new Date(match.tender.submission_deadline).getTime() > Date.now() &&
      new Date(match.tender.submission_deadline).getTime() <
        Date.now() + 7 * 86400000,
  );
  const missing = company
    ? [
        !company.services.length ? "services" : null,
        !company.description ? "company description" : null,
        !company.preferred_locations.length ? "delivery regions" : null,
      ].filter(Boolean)
    : [];
  return (
    <>
      <header className="page-header">
        <div>
          <h1>
            Your opportunities,
            <br />
            in focus.
          </h1>
          <p>{company?.name || "Start with your company profile."}</p>
        </div>
        {company && (
          <button className="button" disabled={busy} onClick={refresh}>
            {busy ? "Updating matches…" : "Refresh matches"}
          </button>
        )}
      </header>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {loading && <p role="status">Loading your shortlist…</p>}
      {!loading && !company && (
        <section className="onboarding-callout">
          <h2>What does your company do best?</h2>
          <p>
            Add your services and delivery preferences. We’ll use them to
            surface opportunities and explain the fit.
          </p>
          <Link className="button" href="/onboarding">
            Set up your company
          </Link>
        </section>
      )}
      {account && (
        <div className="workspace-status">
          <span>
            {account.plan} · {account.subscription_status}
          </span>
          <Link href="/notifications">Configure your digest</Link>
          <Link href="/billing">Manage subscription</Link>
        </div>
      )}
      {company && (
        <>
          {missing.length > 0 && (
            <p className="notice">
              Improve your profile by adding {missing.join(", ")}.{" "}
              <Link className="text-link" href="/company">
                Edit company profile
              </Link>
            </p>
          )}
          {upcoming.length > 0 && (
            <section className="notice">
              <h2>Deadlines this week</h2>
              <ul>
                {upcoming.map((match) => (
                  <li key={match.id}>
                    <Link
                      className="text-link"
                      href={`/tenders/${match.tender_id}`}
                    >
                      {match.tender!.title}
                    </Link>{" "}
                    ·{" "}
                    {new Date(
                      match.tender!.submission_deadline!,
                    ).toLocaleString("en-BE", { timeZone: "Europe/Brussels" })}
                  </li>
                ))}
              </ul>
              <p>Verify the official source time and submission conditions.</p>
            </section>
          )}
          <div className="section-heading">
            <h2>Highest relevance</h2>
            <Link href="/discover">Browse all notices</Link>
          </div>
          <p className="source-note">
            Scores are experimental relevance signals, not eligibility
            decisions. Review the source and uncertainties.
          </p>
          <section className="tender-grid">
            {matches
              .filter((match) => match.tender)
              .map((match) => (
                <TenderCard
                  key={match.id}
                  tender={match.tender!}
                  match={match}
                />
              ))}
          </section>
          {!loading && !matches.length && (
            <div className="empty-state">
              <h2>Your shortlist is ready to begin.</h2>
              <p>
                Refresh matches after official notices have been ingested.
                Adjust your profile if results are too broad or too narrow.
              </p>
              <Link href="/company">Review your profile</Link>
            </div>
          )}
        </>
      )}
    </>
  );
}
