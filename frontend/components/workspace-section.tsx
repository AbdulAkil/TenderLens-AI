"use client";
import Link from "next/link";
import { FormEvent, useEffect, useState } from "react";
import { AppShell } from "@/components/app-shell";
import { Plans } from "@/components/plans";
import {
  activeCompany,
  api,
  formatDate,
  formatMoney,
  type Account,
  type SavedTender,
  type Tender,
} from "@/lib/api";

type Preferences = {
  frequency: string;
  minimum_score: number;
  deadline_reminders: boolean;
  updates: boolean;
  timezone: string;
};
type History = {
  id: string;
  subject: string;
  category: string;
  status: string;
  created_at: string;
};
type Member = { user_id: string; email: string; role: string };
type Organization = { id: string; name: string };
type Admin = {
  counts: Record<string, number>;
  pilot_leads: Array<{ company_name: string; email: string; message: string }>;
  feedback_counts: Record<string, number>;
  jobs: {
    id: string;
    kind: string;
    status: string;
    attempts: number;
    last_error: string | null;
  }[];
  deliveries: { id: string; subject: string; status: string }[];
  organizations: { id: string; name: string; plan: string; status: string }[];
  ai_cost_eur: number;
  manual_review: boolean;
  email_provider: string;
};

export function WorkspaceSection({ section }: { section: string }) {
  return (
    <AppShell>
      <Content section={section} />
    </AppShell>
  );
}
function Content({ section }: { section: string }) {
  const [account, setAccount] = useState<Account | null>(null);
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [history, setHistory] = useState<History[]>([]);
  const [team, setTeam] = useState<Member[]>([]);
  const [orgs, setOrgs] = useState<Organization[]>([]);
  const [saved, setSaved] = useState<SavedTender[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [comparison, setComparison] = useState<Tender[]>([]);
  const [admin, setAdmin] = useState<Admin | null>(null);
  const [preview, setPreview] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const loadAdmin = () => api<Admin>("/admin/overview").then(setAdmin);
  useEffect(() => {
    const tasks: Promise<unknown>[] = [
      api<Account>("/auth/me").then(setAccount),
    ];
    if (section === "notifications")
      tasks.push(
        api<Preferences>("/notifications/preferences").then(setPrefs),
        api<History[]>("/notifications/history").then(setHistory),
      );
    if (section === "settings")
      tasks.push(
        api<Member[]>("/account/team").then(setTeam),
        api<Organization[]>("/account/organizations").then(setOrgs),
      );
    if (section === "compare")
      tasks.push(
        activeCompany().then((company) =>
          company
            ? api<SavedTender[]>(`/companies/${company.id}/saved`).then(
                setSaved,
              )
            : undefined,
        ),
      );
    if (section === "admin") tasks.push(loadAdmin());
    Promise.all(tasks)
      .catch((cause) => setMessage(String(cause)))
      .finally(() => setLoading(false));
  }, [section]);
  const action = async (
    task: () => Promise<unknown>,
    success = "Changes saved.",
  ) => {
    setBusy(true);
    setMessage("");
    try {
      await task();
      setMessage(success);
    } catch (cause) {
      setMessage(cause instanceof Error ? cause.message : String(cause));
    } finally {
      setBusy(false);
    }
  };
  const savePreferences = (event: FormEvent) => {
    event.preventDefault();
    if (prefs)
      action(() =>
        api("/notifications/preferences", {
          method: "PUT",
          body: JSON.stringify(prefs),
        }),
      );
  };
  const addMember = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    action(async () => {
      await api("/account/team", {
        method: "POST",
        body: JSON.stringify({
          email: form.get("email"),
          role: form.get("role"),
        }),
      });
      setTeam(await api<Member[]>("/account/team"));
    });
  };
  const deletion = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    action(async () => {
      await api("/auth/deletion-request", {
        method: "POST",
        body: JSON.stringify({ password: form.get("password") }),
      });
      location.assign("/auth/login");
    }, "Deletion requested.");
  };
  const titles: Record<string, string> = {
    notifications: "The right signal. At your pace.",
    billing: "Your subscription.",
    settings: "Your account and team.",
    compare: "Make the differences clear.",
    admin: "Operations desk.",
  };
  return (
    <>
      <header className="page-header compact">
        <h1>{titles[section]}</h1>
      </header>
      {message && (
        <p role="status" className="notice">
          {message}
        </p>
      )}
      {loading && <p role="status">Loading your workspace…</p>}
      {section === "notifications" && prefs && (
        <div className="settings-layout">
          <form className="profile-form" onSubmit={savePreferences}>
            <h2>Tender delivery</h2>
            <label>
              Digest frequency
              <select
                value={prefs.frequency}
                onChange={(e) =>
                  setPrefs({ ...prefs, frequency: e.target.value })
                }
              >
                <option value="off">Off</option>
                <option value="weekly">Weekly</option>
                <option value="daily">Daily (Professional / Business)</option>
              </select>
            </label>
            <label>
              Minimum relevance score
              <input
                type="number"
                min={0}
                max={100}
                value={prefs.minimum_score}
                onChange={(e) =>
                  setPrefs({ ...prefs, minimum_score: Number(e.target.value) })
                }
              />
              <small>
                Experimental scores; adjust after reviewing your actual matches.
              </small>
            </label>
            <label>
              Timezone
              <input
                value={prefs.timezone}
                onChange={(e) =>
                  setPrefs({ ...prefs, timezone: e.target.value })
                }
              />
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={prefs.deadline_reminders}
                onChange={(e) =>
                  setPrefs({ ...prefs, deadline_reminders: e.target.checked })
                }
              />
              <span>
                Remind me about saved deadlines (Professional / Business)
              </span>
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={prefs.updates}
                onChange={(e) =>
                  setPrefs({ ...prefs, updates: e.target.checked })
                }
              />
              <span>Notify me about supported notice changes</span>
            </label>
            <button className="button" disabled={busy}>
              {busy ? "Saving…" : "Save email preferences"}
            </button>
            <p className="source-note">
              Choose Off to stop procurement emails. Essential account messages
              are separate. Local delivery defaults to dry run.
            </p>
          </form>
          <section>
            <h2>Recent deliveries</h2>
            {!history.length && <p>No delivery records yet.</p>}
            <ul className="activity-list">
              {history.map((item) => (
                <li key={item.id}>
                  <strong>{item.subject}</strong>
                  <span>
                    {item.status} · {formatDate(item.created_at)}
                  </span>
                </li>
              ))}
            </ul>
          </section>
        </div>
      )}
      {section === "billing" && (
        <>
          <div className="workspace-status">
            <span>
              {account?.plan} · {account?.subscription_status}
            </span>
            {account?.trial_ends_at && (
              <span>Trial ends {formatDate(account.trial_ends_at)}</span>
            )}
            <button
              className="quiet-button"
              disabled={busy}
              onClick={() =>
                action(async () => {
                  const result = await api<{ url: string }>("/billing/portal", {
                    method: "POST",
                  });
                  location.assign(result.url);
                })
              }
            >
              Manage subscription
            </button>
            <button
              className="quiet-button"
              disabled={busy}
              onClick={() =>
                action(async () => {
                  const rows = await api<
                    {
                      id: string;
                      status: string;
                      amount_paid: number;
                      currency: string;
                      url: string;
                    }[]
                  >("/billing/invoices");
                  setPreview(
                    rows.length
                      ? rows
                          .map(
                            (row) =>
                              `${row.id} · ${row.status} · ${row.amount_paid / 100} ${row.currency.toUpperCase()}\n${row.url || "Invoice not finalized"}`,
                          )
                          .join("\n\n")
                      : "No invoices yet.",
                  );
                }, "Billing history loaded.")
              }
            >
              View invoice history
            </button>
          </div>
          <p>
            The billing portal manages test subscriptions, cancellation and
            payment details. Checkout success does not unlock a plan until a
            signed webhook updates your account.
          </p>
          <Plans billing />
          {preview && <pre className="text-preview">{preview}</pre>}
        </>
      )}
      {section === "settings" && (
        <div className="settings-layout">
          <section>
            <h2>Organization & access</h2>
            <p>
              {account?.email} · {account?.role}
            </p>
            <label>
              Active organization
              <select
                value={account?.organization_id || ""}
                onChange={(event) =>
                  action(async () => {
                    await api("/account/switch", {
                      method: "POST",
                      body: JSON.stringify({
                        organization_id: event.target.value,
                      }),
                    });
                    localStorage.removeItem("tenderlens.active-company");
                    location.reload();
                  })
                }
              >
                {orgs.map((org) => (
                  <option value={org.id} key={org.id}>
                    {org.name}
                  </option>
                ))}
              </select>
            </label>
            <h2 className="spaced-heading">Your team</h2>
            <ul className="activity-list">
              {team.map((member) => (
                <li key={member.user_id}>
                  <strong>{member.email}</strong>
                  <span>{member.role}</span>
                  {member.role !== "owner" && account?.role !== "member" && (
                    <button
                      className="quiet-button"
                      disabled={busy}
                      onClick={() =>
                        action(async () => {
                          await api(`/account/team/${member.user_id}`, {
                            method: "DELETE",
                          });
                          setTeam(
                            team.filter(
                              (item) => item.user_id !== member.user_id,
                            ),
                          );
                        })
                      }
                    >
                      Remove member
                    </button>
                  )}
                </li>
              ))}
            </ul>
            {account?.role !== "member" && (
              <form className="profile-form" onSubmit={addMember}>
                <h3>Add a verified member</h3>
                <p>
                  Business plan required. Ask the person to create and verify
                  their account first.
                </p>
                <label>
                  Member email
                  <input name="email" type="email" required />
                </label>
                <label>
                  Role
                  <select name="role">
                    <option value="member">Member</option>
                    <option value="admin">Administrator</option>
                  </select>
                </label>
                <button className="button" disabled={busy}>
                  Add team member
                </button>
              </form>
            )}
          </section>
          <section>
            <h2>Your information</h2>
            <p>
              Export your company profiles, saved opportunities, feedback and
              preferences. Privacy export remains available after a trial ends.
            </p>
            <button
              className="quiet-button"
              disabled={busy}
              onClick={() =>
                action(async () => {
                  const data = await api("/account/export");
                  const url = URL.createObjectURL(
                    new Blob([JSON.stringify(data, null, 2)], {
                      type: "application/json",
                    }),
                  );
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = "tenderlens-workspace.json";
                  a.click();
                  URL.revokeObjectURL(url);
                }, "Export downloaded.")
              }
            >
              Download workspace data
            </button>
            {account?.role === "owner" && (
              <form className="profile-form danger-zone" onSubmit={deletion}>
                <h2>Request organization deletion</h2>
                <p>
                  This revokes all organization sessions immediately. The
                  operator must settle billing and required retention before
                  final erasure.
                </p>
                <label>
                  Confirm your current password
                  <input
                    name="password"
                    type="password"
                    autoComplete="current-password"
                    required
                  />
                </label>
                <label className="checkbox-label">
                  <input type="checkbox" required />
                  <span>
                    I understand that everyone in this organization will lose
                    access.
                  </span>
                </label>
                <button className="quiet-button" disabled={busy}>
                  Request deletion & revoke access
                </button>
              </form>
            )}
            <p>
              <Link className="text-link" href="/auth/forgot">
                Reset your password
              </Link>
            </p>
          </section>
        </div>
      )}
      {section === "compare" && (
        <>
          <p>
            Select two to four saved opportunities. Comparison is available on
            Professional and Business.
          </p>
          {saved.length < 2 && (
            <div className="empty-state">
              <h2>Build a shortlist first.</h2>
              <p>
                Save at least two tenders to compare published facts side by
                side.
              </p>
              <Link href="/discover">Discover opportunities</Link>
            </div>
          )}
          <div className="comparison-picker">
            {saved.map((item) => (
              <label className="checkbox-label" key={item.id}>
                <input
                  type="checkbox"
                  checked={selected.includes(item.tender_id)}
                  disabled={
                    selected.length >= 4 && !selected.includes(item.tender_id)
                  }
                  onChange={(e) =>
                    setSelected(
                      e.target.checked
                        ? [...selected, item.tender_id]
                        : selected.filter((id) => id !== item.tender_id),
                    )
                  }
                />
                <span>{item.tender.title}</span>
              </label>
            ))}
          </div>
          {saved.length >= 2 && (
            <button
              className="button"
              disabled={busy || selected.length < 2}
              onClick={() =>
                action(async () => {
                  setComparison(
                    (
                      await api<{ items: Tender[] }>("/tenders/compare", {
                        method: "POST",
                        body: JSON.stringify({ tender_ids: selected }),
                      })
                    ).items,
                  );
                }, "Comparison loaded.")
              }
            >
              Compare selected tenders
            </button>
          )}
          {comparison.length > 0 && (
            <div className="table-scroll">
              <table>
                <caption>Published procurement facts</caption>
                <thead>
                  <tr>
                    <th>Detail</th>
                    {comparison.map((item) => (
                      <th key={item.id}>
                        <Link href={`/tenders/${item.id}`}>{item.title}</Link>
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {[
                    "buyer_name",
                    "country_code",
                    "estimated_value",
                    "submission_deadline",
                    "procedure_type",
                  ].map((field) => (
                    <tr key={field}>
                      <th>{field.replaceAll("_", " ")}</th>
                      {comparison.map((item) => (
                        <td key={item.id}>
                          {field === "estimated_value"
                            ? formatMoney(item.estimated_value, item.currency)
                            : field === "submission_deadline"
                              ? formatDate(item.submission_deadline)
                              : String(
                                  item[field as keyof Tender] ||
                                    "Not published",
                                )}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
      {section === "admin" && admin && (
        <>
          <div className="workspace-status">
            {Object.entries(admin.counts).map(([key, value]) => (
              <span key={key}>
                {key.replaceAll("_", " ")}: <strong>{value}</strong>
              </span>
            ))}
          </div>
          <p>
            Delivery: {admin.email_provider}. Digest review{" "}
            {admin.manual_review ? "required" : "automatic"}. Recorded AI cost:
            €{admin.ai_cost_eur.toFixed(2)}.
          </p>
          <h2>Digest review</h2>
          <ul className="activity-list">
            {admin.deliveries.map((item) => (
              <li key={item.id}>
                <strong>{item.subject}</strong>
                <span>{item.status}</span>
                <div className="action-row">
                  <button
                    className="quiet-button"
                    disabled={busy}
                    onClick={() =>
                      action(async () => {
                        const result = await api<{ text: string }>(
                          `/admin/deliveries/${item.id}`,
                        );
                        setPreview(result.text);
                      }, "Preview loaded.")
                    }
                  >
                    Review content
                  </button>
                  {item.status === "review" && (
                    <button
                      className="button"
                      disabled={busy}
                      onClick={() =>
                        action(async () => {
                          await api(`/admin/deliveries/${item.id}/approve`, {
                            method: "POST",
                          });
                          await loadAdmin();
                        }, "Digest approved.")
                      }
                    >
                      Approve digest
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
          {preview && <pre className="text-preview">{preview}</pre>}
          <h2 className="spaced-heading">Background jobs</h2>
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Job</th>
                  <th>Status</th>
                  <th>Attempts</th>
                  <th>Failure</th>
                  <th>Action</th>
                </tr>
              </thead>
              <tbody>
                {admin.jobs.map((job) => (
                  <tr key={job.id}>
                    <td>{job.kind}</td>
                    <td>{job.status}</td>
                    <td>{job.attempts}</td>
                    <td>{job.last_error || "—"}</td>
                    <td>
                      {job.status === "failed" && (
                        <button
                          className="quiet-button"
                          onClick={() =>
                            action(async () => {
                              await api(`/admin/jobs/${job.id}/retry`, {
                                method: "POST",
                              });
                              await loadAdmin();
                            }, "Job queued.")
                          }
                        >
                          Retry
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <h2 className="spaced-heading">Pilot interest</h2>
          <ul className="activity-list">
            {admin.pilot_leads.map((lead) => (
              <li key={lead.email}>
                <strong>{lead.company_name}</strong>
                <span>{lead.email}</span>
                <p>{lead.message}</p>
              </li>
            ))}
          </ul>
          <p>
            Feedback:{" "}
            {Object.entries(admin.feedback_counts)
              .map(([value, count]) => `${value}: ${count}`)
              .join("; ") || "No feedback recorded yet."}
          </p>
          <h2 className="spaced-heading">Organizations</h2>
          <ul className="activity-list">
            {admin.organizations.map((org) => (
              <li key={org.id}>
                <strong>{org.name}</strong>
                <span>
                  {org.plan} · {org.status}
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  );
}
