"use client";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { api, type Company } from "@/lib/api";
const split = (value: FormDataEntryValue | null) =>
  String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
export function CompanyEditor({
  onboarding = false,
}: {
  onboarding?: boolean;
}) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [company, setCompany] = useState<Company | null>(null);
  const [step, setStep] = useState(onboarding ? 1 : 0);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    api<Company[]>("/companies")
      .then((rows) => {
        setCompanies(rows);
        const active =
          rows.find(
            (row) =>
              row.id === localStorage.getItem("tenderlens.active-company"),
          ) || rows[0];
        setCompany(active || null);
        if (active)
          localStorage.setItem("tenderlens.active-company", active.id);
      })
      .catch((cause) => setMessage(String(cause)))
      .finally(() => setLoading(false));
  }, []);
  const save = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    const payload = {
      name: String(form.get("name")),
      website: String(form.get("website") || "") || null,
      description: String(form.get("description")) || null,
      services: split(form.get("services")),
      industries: split(form.get("industries")),
      skills: split(form.get("skills")),
      certifications: split(form.get("certifications")),
      preferred_locations: split(form.get("locations")),
      cpv_codes: split(form.get("cpv")),
      languages: split(form.get("languages")),
      exclusions: split(form.get("exclusions")),
      tender_types: split(form.get("types")),
      minimum_contract_value: form.get("minimum")
        ? Number(form.get("minimum"))
        : null,
      maximum_contract_value: form.get("maximum")
        ? Number(form.get("maximum"))
        : null,
      company_size: String(form.get("size") || "") || null,
    };
    try {
      const result = await api<Company>(
        company ? `/companies/${company.id}` : "/companies",
        { method: company ? "PUT" : "POST", body: JSON.stringify(payload) },
      );
      setCompany(result);
      localStorage.setItem("tenderlens.active-company", result.id);
      setCompanies(await api<Company[]>("/companies"));
      setMessage(
        "Profile saved. Your scheduled matches will use these preferences.",
      );
      if (onboarding) setStep(4);
    } catch (cause) {
      setMessage(String(cause));
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <header className="page-header compact">
        <div>
          <h1>
            {onboarding
              ? "Let’s find the work you do best."
              : "What a good opportunity looks like."}
          </h1>
          <p>Your capabilities and preferences shape the shortlist.</p>
        </div>
      </header>
      {message && (
        <p role="status" className="notice">
          {message}
        </p>
      )}
      {loading ? (
        <p role="status">Loading company profiles…</p>
      ) : (
        <>
          {!onboarding && (
            <label className="profile-select">
              Active company
              <select
                value={company?.id || ""}
                onChange={(event) => {
                  const active =
                    companies.find((row) => row.id === event.target.value) ||
                    null;
                  setCompany(active);
                  if (active)
                    localStorage.setItem(
                      "tenderlens.active-company",
                      active.id,
                    );
                }}
              >
                <option value="">Create another profile</option>
                {companies.map((row) => (
                  <option key={row.id} value={row.id}>
                    {row.name}
                  </option>
                ))}
              </select>
            </label>
          )}
          {step === 4 ? (
            <section className="onboarding-callout">
              <h2>Your profile is ready.</h2>
              <p>
                Choose how often you want to hear from us, then review your
                first matches.
              </p>
              <div className="action-row">
                <Link className="button" href="/notifications">
                  Set up your digest
                </Link>
                <Link className="text-link" href="/dashboard">
                  Open your opportunities
                </Link>
              </div>
            </section>
          ) : (
            <div className="profile-layout">
              <form
                key={company?.id || "new"}
                className="profile-form"
                onSubmit={save}
              >
                {onboarding && (
                  <nav aria-label="Onboarding steps" className="step-nav">
                    {[1, 2, 3].map((number) => (
                      <button
                        key={number}
                        type="button"
                        aria-current={step === number ? "step" : undefined}
                        onClick={() => setStep(number)}
                      >
                        {number === 1
                          ? "Company"
                          : number === 2
                            ? "Capabilities"
                            : "Preferences"}
                      </button>
                    ))}
                  </nav>
                )}
                <fieldset hidden={onboarding && step !== 1}>
                  <legend>Company basics</legend>
                  <label>
                    Company name
                    <input
                      name="name"
                      required
                      minLength={2}
                      maxLength={256}
                      defaultValue={company?.name}
                    />
                  </label>
                  <label>
                    Company website
                    <input
                      name="website"
                      type="url"
                      defaultValue={company?.website || ""}
                      placeholder="https://your-company.be"
                    />
                  </label>
                  <label>
                    What does your company deliver?
                    <textarea
                      name="description"
                      maxLength={10000}
                      defaultValue={company?.description || ""}
                      placeholder="Describe the work you deliver and the customers you serve."
                    />
                  </label>
                  <label>
                    Industries <small>Comma separated</small>
                    <input
                      name="industries"
                      defaultValue={company?.industries.join(", ")}
                    />
                  </label>
                  <label>
                    Company size
                    <input
                      name="size"
                      defaultValue={company?.company_size || ""}
                      placeholder="e.g. 10–49 employees"
                    />
                  </label>
                </fieldset>
                <fieldset hidden={onboarding && step !== 2}>
                  <legend>Your capabilities</legend>
                  {[
                    [
                      "services",
                      "Services offered",
                      company?.services,
                      "Software development, cybersecurity",
                    ],
                    [
                      "skills",
                      "Skills & specializations",
                      company?.skills,
                      "Python, cloud security",
                    ],
                    [
                      "certifications",
                      "Certifications you hold",
                      company?.certifications,
                      "ISO 27001",
                    ],
                    [
                      "cpv",
                      "CPV codes (optional)",
                      company?.cpv_codes,
                      "72000000",
                    ],
                  ].map(([name, label, value, placeholder]) => (
                    <label key={String(name)}>
                      {String(label)}
                      <small>Comma separated</small>
                      <input
                        name={String(name)}
                        defaultValue={(value as string[] | undefined)?.join(
                          ", ",
                        )}
                        placeholder={String(placeholder)}
                      />
                    </label>
                  ))}
                  <p className="source-note">
                    Only list certifications your company actually holds.
                    Unknown eligibility remains an open question.
                  </p>
                </fieldset>
                <fieldset hidden={onboarding && step !== 3}>
                  <legend>Delivery preferences</legend>
                  <label>
                    Preferred regions / country codes
                    <input
                      name="locations"
                      defaultValue={
                        company?.preferred_locations.join(", ") || "BEL"
                      }
                    />
                    <small>
                      Use BEL, FRA, NLD or EU. Detailed region matching is not
                      yet supported.
                    </small>
                  </label>
                  <div className="two-fields">
                    <label>
                      Minimum contract value
                      <input
                        name="minimum"
                        type="number"
                        min="0"
                        defaultValue={company?.minimum_contract_value || ""}
                      />
                    </label>
                    <label>
                      Maximum contract value
                      <input
                        name="maximum"
                        type="number"
                        min="0"
                        defaultValue={company?.maximum_contract_value || ""}
                      />
                    </label>
                  </div>
                  <label>
                    Supported languages
                    <input
                      name="languages"
                      defaultValue={
                        company?.languages.join(", ") || "Dutch, English"
                      }
                    />
                  </label>
                  <label>
                    Exclude opportunities mentioning
                    <input
                      name="exclusions"
                      defaultValue={company?.exclusions.join(", ")}
                    />
                    <small>
                      Comma separated; explicit exclusions remove candidates.
                    </small>
                  </label>
                  <label>
                    Procedure types (optional)
                    <input
                      name="types"
                      defaultValue={company?.tender_types.join(", ")}
                      placeholder="open, restricted"
                    />
                  </label>
                </fieldset>
                {onboarding && step < 3 ? (
                  <button
                    type="button"
                    className="button"
                    key="continue"
                    onClick={(event) => {
                      event.preventDefault();
                      setStep(step + 1);
                    }}
                  >
                    Continue
                  </button>
                ) : (
                  <button
                    key="save"
                    className="button"
                    type="submit"
                    disabled={busy}
                  >
                    {busy ? "Saving profile…" : "Save company profile"}
                  </button>
                )}
              </form>
              <aside className="profile-aside">
                <h2>Specific is useful.</h2>
                <p>
                  Describe your actual delivery capabilities. A focused profile
                  makes matching reasons easier to judge.
                </p>
                <p>
                  Missing contract values and unverified requirements stay
                  visible. A relevance score is never a certificate of
                  eligibility.
                </p>
                <Link className="text-link" href="/dashboard">
                  Review your opportunities
                </Link>
              </aside>
            </div>
          )}
        </>
      )}
    </>
  );
}
