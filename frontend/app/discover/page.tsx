"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { TenderCard } from "@/components/tender-card";
import { api, type TenderPage } from "@/lib/api";

export default function DiscoverPage() {
  const [query, setQuery] = useState("");
  const [country, setCountry] = useState("");
  const [data, setData] = useState<TenderPage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const search = (event?: FormEvent) => {
    event?.preventDefault();
    const params = new URLSearchParams({ limit: "24" });
    if (query.trim().length >= 2) params.set("query", query.trim());
    if (country.trim()) params.set("country", country.trim().toUpperCase());
    api<TenderPage>(`/tenders?${params}`).then(setData).catch((cause: Error) => setError(cause.message));
  };
  useEffect(() => { search(); }, []);
  return <AppShell>
    <header className="page-header compact"><div><p className="eyebrow">Discover / official corpus</p><h1>Find the work worth pursuing.</h1></div></header>
    <form className="discover-form" onSubmit={search}>
      <label><span>Search tender text</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="AI, data engineering, cloud…" /></label>
      <label><span>Country code</span><input value={country} onChange={(event) => setCountry(event.target.value)} placeholder="BEL" maxLength={3} /></label>
      <button className="button" type="submit">Search <span>→</span></button>
    </form>
    <div className="result-bar"><span>{data ? `${data.total} notices found` : "Loading corpus…"}</span><span>Title, description, country, CPV, buyer, value, deadline filters are available through the API.</span></div>
    {error && <p className="notice error">{error}</p>}
    <section className="tender-grid">{data?.items.map((tender) => <TenderCard key={tender.id} tender={tender} />)}</section>
    {data && data.items.length === 0 && <div className="empty-state"><h2>No notices matched those filters.</h2><p>Broaden the keywords or run controlled ingestion to add more official notices.</p></div>}
  </AppShell>;
}
