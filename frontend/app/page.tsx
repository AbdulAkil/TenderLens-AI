"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { TenderCard } from "@/components/tender-card";
import { api, type Match, type TenderPage } from "@/lib/api";

export default function Home() {
  const [tenders, setTenders] = useState<TenderPage | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api<TenderPage>("/tenders?limit=4").then(setTenders).catch((cause: Error) => setError(cause.message));
    const companyId = window.localStorage.getItem("tenderlens.active-company");
    if (companyId) api<Match[]>(`/companies/${companyId}/matches?limit=4`).then(setMatches).catch(() => undefined);
  }, []);

  const deadlineCount = tenders?.items.filter((item) => item.submission_deadline).length || 0;
  return <AppShell>
    <header className="page-header"><div><p className="eyebrow">Overview / evidence-led</p><h1>Procurement, with a clearer line of sight.</h1></div><Link className="button" href="/discover">Discover tenders <span>→</span></Link></header>
    {error && <p className="notice error">The workspace could not reach the API: {error}</p>}
    <section className="metric-grid" aria-label="Workspace summary">
      <article><p>Ingested notices</p><strong>{tenders?.total ?? "—"}</strong><span>Official TED corpus</span></article>
      <article><p>Deadline signals</p><strong>{deadlineCount || "—"}</strong><span>In current view</span></article>
      <article><p>Profile matches</p><strong>{matches.length || "—"}</strong><span>Calculated opportunities</span></article>
    </section>
    <section className="section-heading"><div><p className="eyebrow">Latest source records</p><h2>Newly ingested opportunities</h2></div><Link href="/discover">View all</Link></section>
    <section className="tender-grid">
      {tenders?.items.map((tender) => <TenderCard key={tender.id} tender={tender} match={matches.find((match) => match.tender_id === tender.id)} />)}
    </section>
    {!tenders?.items.length && !error && <div className="empty-state"><h2>No notices in the local corpus yet.</h2><p>Run a controlled TED ingestion, then return here to explore source-backed opportunities.</p></div>}
    <section className="workflow-banner"><p className="eyebrow">How the workspace decides</p><h2>Evidence first. Interpretation second.</h2><p>Search, extraction, match components, and every AI answer remain connected to the tender record and its official source documents.</p><Link href="/company">Set up a company profile →</Link></section>
  </AppShell>;
}
