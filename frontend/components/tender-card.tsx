"use client";
import Link from "next/link";
import { useState } from "react";
import {
  activeCompany,
  api,
  formatDate,
  formatMoney,
  officialUrl,
  type Match,
  type Tender,
} from "@/lib/api";
export function TenderCard({
  tender,
  match,
}: {
  tender: Tender;
  match?: Match;
}) {
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const save = async () => {
    setBusy(true);
    try {
      const company = await activeCompany();
      if (!company)
        throw Error("Create a company profile before saving opportunities.");
      await api(`/tenders/${tender.id}/save`, {
        method: "POST",
        body: JSON.stringify({ company_id: company.id }),
      });
      setMessage("Saved to your shortlist.");
    } catch (cause) {
      setMessage(String(cause));
    } finally {
      setBusy(false);
    }
  };
  return (
    <article className="tender-card">
      <div className="card-topline">
        <span>
          {tender.country_code || "Location unavailable"} ·{" "}
          {tender.buyer_name || "Buyer not published"}
        </span>
        {match && (
          <strong className="match-score">
            {Math.round(match.overall_score)}/100 relevance
          </strong>
        )}
      </div>
      <Link href={`/tenders/${tender.id}`}>
        <h3>{tender.title}</h3>
      </Link>
      <p className="card-description">
        {tender.description ||
          "Read the official notice for the published scope and submission requirements."}
      </p>
      <div className="card-meta">
        <span>
          <b>Deadline</b>
          {formatDate(tender.submission_deadline)}
        </span>
        <span>
          <b>Value</b>
          {formatMoney(tender.estimated_value, tender.currency)}
        </span>
      </div>
      {match && (
        <div className="fit-notes">
          {match.reasons.slice(0, 2).map((reason) => (
            <p key={reason}>{reason}</p>
          ))}
          {match.blockers.slice(0, 2).map((blocker) => (
            <p key={blocker} className="caution">
              {blocker}
            </p>
          ))}
        </div>
      )}
      <div className="card-actions">
        <Link className="text-link" href={`/tenders/${tender.id}`}>
          Review opportunity
        </Link>
        {officialUrl(tender.source_url) && (
          <a
            className="text-link"
            href={officialUrl(tender.source_url)}
            target="_blank"
            rel="noopener noreferrer"
          >
            Official source
          </a>
        )}
        <button className="quiet-button" disabled={busy} onClick={save}>
          {busy ? "Saving…" : "Save"}
        </button>
      </div>
      {message && (
        <p role="status" className="source-note">
          {message}
        </p>
      )}
    </article>
  );
}
