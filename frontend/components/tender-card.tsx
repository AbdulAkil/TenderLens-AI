import Link from "next/link";
import { formatDate, formatMoney, type Match, type Tender } from "@/lib/api";

export function TenderCard({ tender, match }: { tender: Tender; match?: Match }) {
  return (
    <article className="tender-card">
      <div className="card-topline">
        <span>{tender.country_code || "EU"} · {tender.buyer_name || "Official TED notice"}</span>
        {match && <strong className="match-score">{Math.round(match.overall_score)}% fit</strong>}
      </div>
      <Link href={`/tenders/${tender.id}`}><h3>{tender.title}</h3></Link>
      <p className="card-description">{tender.description || "Official notice metadata is available; process the source document for evidence."}</p>
      <div className="card-meta">
        <span><b>Deadline</b>{formatDate(tender.submission_deadline)}</span>
        <span><b>Value</b>{formatMoney(tender.estimated_value, tender.currency)}</span>
      </div>
      {match && (match.reasons.length > 0 || match.blockers.length > 0) && <div className="fit-notes">
        {match.reasons.slice(0, 2).map((reason) => <p key={reason} className="positive">{reason}</p>)}
        {match.blockers.slice(0, 1).map((blocker) => <p key={blocker} className="caution">{blocker}</p>)}
      </div>}
    </article>
  );
}
