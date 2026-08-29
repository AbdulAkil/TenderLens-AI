"use client";

import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { TenderCard } from "@/components/tender-card";
import { api, type Company, type Match } from "@/lib/api";

const split = (value: string) => value.split(",").map((item) => item.trim()).filter(Boolean);

export default function CompanyPage() {
  const [company, setCompany] = useState<Company | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  useEffect(() => { const id = window.localStorage.getItem("tenderlens.active-company"); if (id) api<Company>(`/companies/${id}`).then(setCompany).catch(() => window.localStorage.removeItem("tenderlens.active-company")); }, []);
  const save = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault(); const form = new FormData(event.currentTarget);
    const payload = { name: String(form.get("name")), description: String(form.get("description")) || null, services: split(String(form.get("services"))), industries: [], skills: split(String(form.get("skills"))), certifications: split(String(form.get("certifications"))), preferred_locations: split(String(form.get("locations"))), cpv_codes: [], languages: split(String(form.get("languages"))), minimum_contract_value: form.get("minimum") ? Number(form.get("minimum")) : null, maximum_contract_value: form.get("maximum") ? Number(form.get("maximum")) : null, company_size: null };
    try { const saved = company ? await api<Company>(`/companies/${company.id}`, { method: "PUT", body: JSON.stringify(payload) }) : await api<Company>("/companies", { method: "POST", body: JSON.stringify(payload) }); setCompany(saved); window.localStorage.setItem("tenderlens.active-company", saved.id); setMessage("Profile saved. Calculate matches when you are ready."); }
    catch (cause) { setMessage(cause instanceof Error ? cause.message : "Could not save profile."); }
  };
  const calculate = async () => { if (!company) return; try { const result = await api<{ items: Match[] }>(`/companies/${company.id}/matches/recalculate`, { method: "POST" }); setMatches(result.items); setMessage(`${result.items.length} deterministic tender matches calculated.`); } catch (cause) { setMessage(cause instanceof Error ? cause.message : "Could not calculate matches."); } };
  return <AppShell>
    <header className="page-header compact"><div><p className="eyebrow">Company profile / deterministic matching</p><h1>Define what a good opportunity looks like.</h1></div>{company && <button className="button" onClick={calculate}>Calculate matches <span>→</span></button>}</header>
    {message && <p className="notice">{message}</p>}
    <section className="profile-layout"><form className="profile-form" onSubmit={save}><label>Company name<input name="name" required defaultValue={company?.name} placeholder="Akil AI Consulting" /></label><label>Capabilities narrative<textarea name="description" defaultValue={company?.description || ""} placeholder="Describe the work you deliver and the outcomes you support." /></label><label>Services <small>Comma separated</small><input name="services" defaultValue={company?.services.join(", ")} placeholder="AI consulting, data engineering" /></label><label>Skills <small>Comma separated</small><input name="skills" defaultValue={company?.skills.join(", ")} placeholder="Python, machine learning, cloud" /></label><label>Certifications <small>Comma separated</small><input name="certifications" defaultValue={company?.certifications.join(", ")} placeholder="ISO 27001" /></label><label>Preferred locations <small>Country codes or EU</small><input name="locations" defaultValue={company?.preferred_locations.join(", ")} placeholder="BEL, EU" /></label><div className="two-fields"><label>Minimum value<input name="minimum" type="number" min="0" defaultValue={company?.minimum_contract_value || ""} /></label><label>Maximum value<input name="maximum" type="number" min="0" defaultValue={company?.maximum_contract_value || ""} /></label></div><label>Languages <small>Comma separated</small><input name="languages" defaultValue={company?.languages.join(", ")} placeholder="English, French, Dutch" /></label><button className="button" type="submit">Save profile <span>→</span></button></form>
      <aside className="profile-aside"><p className="eyebrow">Scoring model</p><h2>Explainable components</h2><p>Every score is calculated from transparent components—not an LLM opinion.</p><dl><div><dt>35%</dt><dd>Capability overlap</dd></div><div><dt>20%</dt><dd>Skill coverage</dd></div><div><dt>15%</dt><dd>Eligibility signals</dd></div><div><dt>30%</dt><dd>Location, value & CPV fit</dd></div></dl></aside></section>
    {matches.length > 0 && <section><div className="section-heading"><div><p className="eyebrow">Calculated opportunities</p><h2>Where the profile aligns</h2></div></div><div className="tender-grid">{matches.filter((match) => match.tender).map((match) => <TenderCard key={match.id} tender={match.tender!} match={match} />)}</div></section>}
  </AppShell>;
}
