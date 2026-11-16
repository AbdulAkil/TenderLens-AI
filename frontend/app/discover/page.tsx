"use client";
import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { TenderCard } from "@/components/tender-card";
import { api, type TenderPage } from "@/lib/api";
export default function Discover() {
  return (
    <AppShell>
      <Content />
    </AppShell>
  );
}
function Content() {
  const [filters, setFilters] = useState<Record<string, string>>({
    query: "",
    country: "BEL",
    cpv: "",
    buyer: "",
    min_value: "",
    max_value: "",
    deadline_before: "",
  });
  const [data, setData] = useState<TenderPage | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const search = async (offset = 0, values = filters) => {
    setLoading(true);
    setError("");
    const params = new URLSearchParams({ limit: "20", offset: String(offset) });
    Object.entries(values).forEach(([key, value]) => {
      if (value.trim()) params.set(key, value.trim());
    });
    try {
      setData(await api<TenderPage>(`/tenders?${params}`));
    } catch (cause) {
      setError(String(cause));
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    search(0, { country: "BEL" });
  }, []);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    search();
  };
  return (
    <>
      <header className="page-header compact">
        <h1>Find the work worth pursuing.</h1>
      </header>
      <form className="discover-form" onSubmit={submit}>
        <label>
          Search tender text
          <input
            value={filters.query}
            onChange={(e) => setFilters({ ...filters, query: e.target.value })}
            placeholder="Software, electrical installation…"
            minLength={2}
            maxLength={500}
          />
        </label>
        <label>
          Country code
          <input
            value={filters.country}
            onChange={(e) =>
              setFilters({ ...filters, country: e.target.value.toUpperCase() })
            }
            minLength={2}
            maxLength={3}
          />
        </label>
        <button className="button" disabled={loading}>
          {loading ? "Searching…" : "Search tenders"}
        </button>
        <details className="filter-grid">
          <summary>More filters</summary>
          <div className="filter-grid">
            {[
              ["cpv", "CPV code", "text"],
              ["buyer", "Contracting authority", "text"],
              ["min_value", "Minimum value", "number"],
              ["max_value", "Maximum value", "number"],
              ["deadline_before", "Deadline before", "datetime-local"],
            ].map(([key, label, type]) => (
              <label key={key}>
                {label}
                <input
                  type={type}
                  min={type === "number" ? "0" : undefined}
                  value={filters[key]}
                  onChange={(e) =>
                    setFilters({ ...filters, [key]: e.target.value })
                  }
                />
              </label>
            ))}
          </div>
        </details>
      </form>
      <div className="result-bar" aria-live="polite">
        <span>
          {loading
            ? "Loading notices…"
            : data
              ? `${data.total} notices found`
              : "Search unavailable"}
        </span>
        <span>Official TED records. Coverage is not exhaustive.</span>
      </div>
      {error && (
        <p role="alert" className="notice error">
          {error}
        </p>
      )}
      <section className="tender-grid" aria-busy={loading}>
        {data?.items.map((tender) => (
          <TenderCard key={tender.id} tender={tender} />
        ))}
      </section>
      {data && !data.items.length && (
        <div className="empty-state">
          <h2>No notices match these filters.</h2>
          <p>
            Try fewer keywords or a broader region. New records depend on the
            configured official-source ingestion schedule.
          </p>
        </div>
      )}
      {data && data.total > 20 && (
        <nav className="pagination" aria-label="Tender results">
          <button
            className="quiet-button"
            disabled={loading || data.offset === 0}
            onClick={() => search(Math.max(0, data.offset - 20))}
          >
            Previous
          </button>
          <span>
            {data.offset + 1}–{Math.min(data.offset + 20, data.total)} of{" "}
            {data.total}
          </span>
          <button
            className="quiet-button"
            disabled={loading || data.offset + 20 >= data.total}
            onClick={() => search(data.offset + 20)}
          >
            Next
          </button>
        </nav>
      )}
    </>
  );
}
