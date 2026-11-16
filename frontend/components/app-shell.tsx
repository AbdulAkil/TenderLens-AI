"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { api, type Account } from "@/lib/api";
import { navigation, type Locale } from "@/lib/messages";

const links = [
  ["/dashboard", "Your opportunities"],
  ["/discover", "Discover tenders"],
  ["/saved", "Saved opportunities"],
  ["/compare", "Compare tenders"],
  ["/company", "Company profiles"],
  ["/notifications", "Email preferences"],
  ["/billing", "Subscription"],
  ["/settings", "Account & team"],
];
export function AppShell({ children }: { children: ReactNode }) {
  const [account, setAccount] = useState<Account | null>(null);
  const [error, setError] = useState("");
  const [locale, setLocale] = useState<Locale>("en");
  const router = useRouter();
  const pathname = usePathname();
  useEffect(() => {
    const saved = localStorage.getItem("tenderlens.locale");
    if (saved && saved in navigation) setLocale(saved as Locale);
  }, []);
  useEffect(() => {
    api<Account>("/auth/me")
      .then(setAccount)
      .catch(() => router.replace("/auth/login"));
  }, [router]);
  const logout = async () => {
    try {
      await api("/auth/logout", { method: "POST" });
      localStorage.removeItem("tenderlens.active-company");
      router.push("/auth/login");
    } catch (cause) {
      setError(String(cause));
    }
  };
  if (!account)
    return (
      <main className="auth-loading" role="status">
        Opening your secure workspace…
      </main>
    );
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <aside className="side-nav">
        <Link className="wordmark" href="/">
          TENDERLENS<span>AI</span>
        </Link>
        <p className="side-label">{account.organization_name}</p>
        <nav aria-label="Workspace" lang={locale}>
          {links.map(([href, label], index) => (
            <Link
              aria-current={pathname === href ? "page" : undefined}
              key={href}
              href={href}
            >
              {navigation[locale][index] || label}
            </Link>
          ))}
          {account.is_admin && <Link href="/admin">Administration</Link>}
        </nav>
        <div className="side-foot">
          <label className="navigation-language">
            Navigation language
            <select
              value={locale}
              onChange={(event) => {
                const value = event.target.value as Locale;
                setLocale(value);
                localStorage.setItem("tenderlens.locale", value);
              }}
            >
              <option value="en">English</option>
              <option value="nl">Nederlands</option>
              <option value="fr">Français</option>
            </select>
          </label>
          <strong>
            {account.plan} · {account.subscription_status}
          </strong>
          <p>{account.email}</p>
          <button className="nav-logout" onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>
      <main id="main-content" className="workspace">
        {error && (
          <p role="alert" className="notice error">
            {error}
          </p>
        )}
        {children}
      </main>
    </div>
  );
}
