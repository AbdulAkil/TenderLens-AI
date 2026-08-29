"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { api, type SavedTender } from "@/lib/api";

export default function SavedPage() {
  const [saved, setSaved] = useState<SavedTender[]>([]);
  const [message, setMessage] = useState("Loading saved opportunities…");
  useEffect(() => { const id = window.localStorage.getItem("tenderlens.active-company"); if (!id) { setMessage("Create a company profile to save and track opportunities."); return; } api<SavedTender[]>(`/companies/${id}/saved`).then((data) => { setSaved(data); setMessage(data.length ? "" : "No saved opportunities yet."); }).catch((cause: Error) => setMessage(cause.message)); }, []);
  return <AppShell><header className="page-header compact"><div><p className="eyebrow">Saved / opportunity desk</p><h1>Keep the strongest signals close.</h1></div></header>{message && <div className="empty-state"><p>{message}</p><Link href="/company">Open company profile →</Link></div>}<section className="saved-list">{saved.map((item) => <Link href={`/tenders/${item.tender_id}`} key={item.id}><span className="match-score">Saved</span><div><p>{item.tender.country_code} · {item.tender.buyer_name}</p><h2>{item.tender.title}</h2></div><span>Review →</span></Link>)}</section></AppShell>;
}
