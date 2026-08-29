import Link from "next/link";
import type { ReactNode } from "react";

const links = [
  ["/", "Overview"],
  ["/discover", "Discover"],
  ["/company", "Company profile"],
  ["/saved", "Saved"],
];

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="app-shell">
      <aside className="side-nav">
        <Link className="wordmark" href="/">TENDERLENS<span>AI</span></Link>
        <p className="side-label">Procurement workspace</p>
        <nav aria-label="Primary navigation">
          {links.map(([href, label]) => <Link key={href} href={href}>{label}</Link>)}
        </nav>
        <div className="side-foot"><span className="live-dot" /> Source-first intelligence<br />Belgium · European Union</div>
      </aside>
      <main className="workspace">{children}</main>
    </div>
  );
}
