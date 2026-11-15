import Link from "next/link";
import type { ReactNode } from "react";
export function PublicShell({ children }: { children: ReactNode }) {
  return (
    <>
      <a className="skip-link" href="#public-content">
        Skip to content
      </a>
      <header className="public-nav">
        <Link className="wordmark" href="/">
          TENDERLENS<span>AI</span>
        </Link>
        <nav aria-label="Main navigation">
          <Link href="/features">Product</Link>
          <Link href="/how-it-works">How it works</Link>
          <Link href="/pricing">Pricing</Link>
          <Link href="/auth/login">Sign in</Link>
          <Link className="button" href="/auth/signup">
            Start your trial
          </Link>
        </nav>
      </header>
      <main id="public-content">{children}</main>
      <footer className="public-footer">
        <div>
          <Link className="wordmark" href="/">
            TENDERLENS<span>AI</span>
          </Link>
          <p>Public opportunities. Clearer decisions.</p>
          <p>Belgium first. Official TED data.</p>
        </div>
        <nav aria-label="Resources">
          <Link href="/example-report">Example report</Link>
          <Link href="/faq">Questions & answers</Link>
          <Link href="/contact">Contact & pilot requests</Link>
          <Link href="/privacy">Privacy</Link>
          <Link href="/terms">Terms</Link>
          <Link href="/cookies">Cookie information</Link>
        </nav>
        <p>
          Controlled pilot · No affiliation with TED or Belgian public
          authorities.
        </p>
      </footer>
    </>
  );
}
