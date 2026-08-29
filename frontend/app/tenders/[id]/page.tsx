"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { api, formatDate, formatMoney, type Analysis, type Answer, type DocumentSource, type Tender } from "@/lib/api";

export default function TenderDetailPage() {
  const params = useParams<{ id: string }>();
  const id = params.id;
  const [tender, setTender] = useState<Tender | null>(null);
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [documents, setDocuments] = useState<DocumentSource[]>([]);
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  useEffect(() => {
    api<Tender>(`/tenders/${id}`).then(setTender).catch((cause: Error) => setNotice(cause.message));
    api<DocumentSource[]>(`/tenders/${id}/documents`).then(setDocuments).catch(() => undefined);
    api<Analysis>(`/tenders/${id}/analysis`).then(setAnalysis).catch(() => undefined);
  }, [id]);

  const buildAnalysis = async () => {
    try {
      await api(`/tenders/${id}/extract`, { method: "POST" });
      setAnalysis(await api<Analysis>(`/tenders/${id}/analysis`, { method: "POST" }));
    } catch (cause) { setNotice(cause instanceof Error ? cause.message : "Could not build the analysis."); }
  };
  const ask = async (event: FormEvent) => {
    event.preventDefault();
    if (!question.trim()) return;
    try { setAnswer(await api<Answer>(`/tenders/${id}/ask`, { method: "POST", body: JSON.stringify({ question }) })); }
    catch (cause) { setNotice(cause instanceof Error ? cause.message : "Could not retrieve evidence."); }
  };
  const save = async () => {
    const companyId = window.localStorage.getItem("tenderlens.active-company");
    if (!companyId) { setNotice("Create or select a company profile before saving opportunities."); return; }
    try { await api(`/tenders/${id}/save`, { method: "POST", body: JSON.stringify({ company_id: companyId }) }); setNotice("Saved to the active company profile."); }
    catch (cause) { setNotice(cause instanceof Error ? cause.message : "Could not save tender."); }
  };

  if (!tender && !notice) return <AppShell><p className="loading">Loading official notice…</p></AppShell>;
  if (!tender) return <AppShell><div className="empty-state"><h2>That tender is unavailable.</h2><p>{notice}</p><Link href="/discover">Return to discovery</Link></div></AppShell>;
  return <AppShell>
    <Link className="back-link" href="/discover">← Discover</Link>
    <header className="detail-hero"><div><p className="eyebrow">{tender.country_code || "EU"} / {tender.buyer_name || "Official TED notice"}</p><h1>{tender.title}</h1><p>{tender.description || "Official source metadata is available below."}</p></div><button className="quiet-button" onClick={save}>Save opportunity</button></header>
    {notice && <p className="notice">{notice}</p>}
    <section className="detail-metrics"><div><b>Deadline</b><span>{formatDate(tender.submission_deadline)}</span></div><div><b>Estimated value</b><span>{formatMoney(tender.estimated_value, tender.currency)}</span></div><div><b>Procedure</b><span>{tender.procedure_type || "Not published"}</span></div><div><b>CPV</b><span>{tender.cpv_code_values.join(", ") || "Not published"}</span></div></section>
    <section className="detail-layout">
      <div className="detail-main">
        <div className="section-heading"><div><p className="eyebrow">Tender analysis</p><h2>What the record tells us</h2></div>{!analysis && <button className="button" onClick={buildAnalysis}>Build evidence summary <span>→</span></button>}</div>
        {analysis ? <div className="analysis-block"><p className="summary">{analysis.summary}</p><FactList title="Key requirements" items={analysis.key_requirements} /><FactList title="Potential blockers" items={analysis.potential_blockers} caution /><FactList title="Required documents" items={analysis.required_documents} /><FactList title="Evaluation criteria" items={analysis.evaluation_criteria} /><p className="source-note">Generated with {analysis.generation_method} from stored tender evidence.</p></div> : <div className="empty-state compact-empty"><p>Run the analysis to create a source-backed overview. It does not infer missing procurement requirements.</p></div>}
        <section className="ask-panel"><p className="eyebrow">Ask TenderLens</p><h2>Interrogate the source, not a black box.</h2><form onSubmit={ask}><input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="What certifications are required?" /><button className="button" type="submit">Ask <span>→</span></button></form>{answer && <div className="answer"><p className="answer-status">{answer.status.replace("_", " ")} · {answer.retrieval_method}</p><p>{answer.answer}</p>{answer.citations.map((citation) => <a key={citation.chunk_id} href={citation.source_url} target="_blank">Source excerpt: {citation.excerpt.slice(0, 140)}…</a>)}</div>}</section>
      </div>
      <aside className="detail-aside"><p className="eyebrow">Source documents</p><h2>Evidence trail</h2>{documents.length ? documents.map((document) => <a className="document-link" key={document.id} href={document.source_url} target="_blank"><span>{document.media_type || "Official source"}</span><strong>{document.file_name || "TED notice representation"}</strong><small>{document.processing_status} · {document.chunk_count} chunks</small></a>) : <p>No processed source document has been registered yet.</p>}<a className="official-link" href={tender.source_url} target="_blank">Open official TED notice ↗</a></aside>
    </section>
  </AppShell>;
}

function FactList({ title, items, caution = false }: { title: string; items: string[]; caution?: boolean }) {
  if (!items.length) return null;
  return <div className={`fact-list ${caution ? "caution-list" : ""}`}><h3>{title}</h3><ul>{items.map((item) => <li key={item}>{item}</li>)}</ul></div>;
}
