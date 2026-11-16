"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { activeCompany, api, formatDate, type SavedTender } from "@/lib/api";
export default function Saved() {
  return (
    <AppShell>
      <Content />
    </AppShell>
  );
}
function Content() {
  const [saved, setSaved] = useState<SavedTender[]>([]);
  const [companyId, setCompanyId] = useState("");
  const [message, setMessage] = useState("Loading saved opportunities…");
  const [busy, setBusy] = useState("");
  useEffect(() => {
    activeCompany()
      .then(async (company) => {
        if (!company) {
          setMessage("Create a company profile to start your shortlist.");
          return;
        }
        setCompanyId(company.id);
        const rows = await api<SavedTender[]>(`/companies/${company.id}/saved`);
        setSaved(rows);
        setMessage(rows.length ? "" : "No saved opportunities yet.");
      })
      .catch((cause) => setMessage(String(cause)));
  }, []);
  const remove = async (id: string) => {
    setBusy(id);
    try {
      await api(`/companies/${companyId}/saved/${id}`, { method: "DELETE" });
      setSaved(saved.filter((item) => item.tender_id !== id));
      setMessage("Opportunity removed.");
    } catch (cause) {
      setMessage(String(cause));
    } finally {
      setBusy("");
    }
  };
  return (
    <>
      <header className="page-header compact">
        <h1>Keep the strongest signals close.</h1>
        <Link className="button" href="/compare">
          Compare your shortlist
        </Link>
      </header>
      {message && (
        <p role="status" className="notice">
          {message}
        </p>
      )}
      <section>
        {saved.map((item) => (
          <article className="saved-opportunity" key={item.id}>
            <div>
              <p>
                {item.tender.country_code} · {item.tender.buyer_name} · Deadline{" "}
                {formatDate(item.tender.submission_deadline)}
              </p>
              <h2>
                <Link href={`/tenders/${item.tender_id}`}>
                  {item.tender.title}
                </Link>
              </h2>
              {item.notes && <p>{item.notes}</p>}
              <Link className="text-link" href={`/tenders/${item.tender_id}`}>
                Review evidence
              </Link>
            </div>
            <button
              className="quiet-button"
              disabled={busy === item.tender_id}
              onClick={() => remove(item.tender_id)}
            >
              Remove from saved
            </button>
          </article>
        ))}
      </section>
      {!saved.length && (
        <Link className="text-link" href="/discover">
          Discover opportunities
        </Link>
      )}
    </>
  );
}
