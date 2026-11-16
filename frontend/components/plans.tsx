"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
type Plan = {
  name: string;
  monthly_eur: number;
  profiles: number;
  members: number;
  saved: number;
  daily: boolean;
  analysis: boolean;
  comparison: boolean;
  export: boolean;
};
export function Plans({ billing = false }: { billing?: boolean }) {
  const [plans, setPlans] = useState<Record<string, Plan>>({});
  const [error, setError] = useState("");
  const [busy, setBusy] = useState("");
  useEffect(() => {
    api<Record<string, Plan>>("/billing/plans")
      .then(setPlans)
      .catch((cause) => setError(String(cause)));
  }, []);
  const checkout = async (plan: string) => {
    setBusy(plan);
    try {
      const result = await api<{ url: string }>("/billing/checkout", {
        method: "POST",
        body: JSON.stringify({ plan }),
      });
      location.assign(result.url);
    } catch (cause) {
      setError(String(cause));
      setBusy("");
    }
  };
  return (
    <>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      {!Object.keys(plans).length && !error && (
        <p role="status">Loading current plans…</p>
      )}
      <div className="pricing-grid">
        {Object.entries(plans).map(([key, plan]) => (
          <article
            className={`plan ${key === "professional" ? "featured-plan" : ""}`}
            key={key}
          >
            <h2>{plan.name}</h2>
            <p className="plan-price">
              €{plan.monthly_eur}
              <span>/ month</span>
            </p>
            <p>
              {key === "starter"
                ? "A focused weekly shortlist."
                : key === "professional"
                  ? "For an active tender pipeline."
                  : "One workspace for your bid team."}
            </p>
            <ul>
              <li>
                {plan.profiles} company{" "}
                {plan.profiles === 1 ? "profile" : "profiles"}
              </li>
              <li>{plan.daily ? "Daily or weekly" : "Weekly"} tender digest</li>
              <li>{plan.saved} saved opportunities</li>
              <li>Explainable matching</li>
              {plan.analysis && <li>Detailed evidence analysis</li>}
              {plan.comparison && <li>Side-by-side comparison</li>}
              {plan.members > 1 && <li>Up to {plan.members} team members</li>}
              {plan.export && <li>Data export</li>}
            </ul>
            {billing ? (
              <button
                className="button"
                disabled={!!busy}
                onClick={() => checkout(key)}
              >
                {busy === key
                  ? "Opening checkout…"
                  : `Test ${plan.name} checkout`}
              </button>
            ) : (
              <Link className="button" href="/auth/signup">
                Start your trial
              </Link>
            )}
          </article>
        ))}
      </div>
      <p className="source-note">
        Pilot pricing hypotheses, excluding applicable VAT. Optional AI requires
        operator configuration. Billing currently accepts Stripe test-mode
        payments only.
      </p>
    </>
  );
}
