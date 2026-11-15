"use client";
import { FormEvent, useState } from "react";
import { api } from "@/lib/api";
export function ContactForm() {
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    try {
      const result = await api<{ message: string }>("/pilot-interest", {
        method: "POST",
        body: JSON.stringify({
          email: form.get("email"),
          company_name: form.get("company"),
          message: form.get("message"),
          consent_to_contact: form.get("consent") === "on",
        }),
      });
      setMessage(result.message);
    } catch (cause) {
      setMessage(String(cause));
    } finally {
      setBusy(false);
    }
  };
  return (
    <form className="profile-form contact-form" onSubmit={submit}>
      <label>
        Business email
        <input name="email" type="email" required maxLength={320} />
      </label>
      <label>
        Company name
        <input name="company" minLength={2} maxLength={256} required />
      </label>
      <label>
        What kind of opportunities are you looking for?
        <textarea name="message" minLength={5} maxLength={2000} required />
      </label>
      <label className="checkbox-label">
        <input type="checkbox" name="consent" required />
        <span>
          You may contact me about this request. I have read the privacy notice.
        </span>
      </label>
      <button className="button" disabled={busy}>
        {busy ? "Recording request…" : "Request a pilot conversation"}
      </button>
      {message && (
        <p role="status" className="notice">
          {message}
        </p>
      )}
    </form>
  );
}
