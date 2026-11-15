"use client";
import { useEffect, useState } from "react";
import {
  activeCompany,
  api,
  officialUrl,
  type DocumentSource,
} from "@/lib/api";
type Requirement = {
  id: string;
  field_name: string;
  value: unknown;
  source_document_id: string | null;
};
export function TenderEvidence({
  id,
  documents,
}: {
  id: string;
  documents: DocumentSource[];
}) {
  const [requirements, setRequirements] = useState<Requirement[]>([]);
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    api<Requirement[]>(`/tenders/${id}/requirements`)
      .then(setRequirements)
      .catch(() => undefined);
  }, [id]);
  return (
    <>
      <section className="workspace-status">
        <label>
          How useful is this opportunity?
          <select
            defaultValue=""
            disabled={busy}
            onChange={async (event) => {
              const value = event.target.value;
              if (!value) return;
              setBusy(true);
              try {
                const company = await activeCompany();
                if (!company) throw Error("Create a company profile first.");
                const result = await api<{ message: string }>(
                  `/companies/${company.id}/feedback/${id}`,
                  { method: "PUT", body: JSON.stringify({ value }) },
                );
                setMessage(result.message);
              } catch (cause) {
                setMessage(String(cause));
              } finally {
                setBusy(false);
              }
            }}
          >
            <option value="" disabled>
              Record your feedback
            </option>
            <option value="relevant">Relevant</option>
            <option value="irrelevant">Irrelevant</option>
            <option value="interested">Interested</option>
            <option value="not_eligible">Not eligible</option>
            <option value="applied">Already applied</option>
            <option value="not_interested">Not interested</option>
          </select>
        </label>
        {message && <p role="status">{message}</p>}
      </section>
      {requirements.length > 0 && (
        <section className="fact-list">
          <h2>Extracted requirements & sources</h2>
          <ul>
            {requirements.map((item) => {
              const document = documents.find(
                (doc) => doc.id === item.source_document_id,
              );
              return (
                <li key={item.id}>
                  <strong>{item.field_name.replaceAll("_", " ")}: </strong>
                  {Array.isArray(item.value)
                    ? item.value.join("; ")
                    : String(item.value)}{" "}
                  {document && (
                    <a
                      className="text-link"
                      href={officialUrl(document.source_url)}
                      target="_blank"
                      rel="noopener noreferrer"
                    >
                      Read source evidence
                    </a>
                  )}
                </li>
              );
            })}
          </ul>
          <p className="source-note">
            Verify mandatory status, applicability and the complete submission
            instructions.
          </p>
        </section>
      )}
    </>
  );
}
