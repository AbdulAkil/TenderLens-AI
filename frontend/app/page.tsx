import Link from "next/link";
import { PublicShell } from "@/components/public-shell";
export default function Home() {
  return (
    <PublicShell>
      <section className="marketing-hero">
        <div className="hero-copy">
          <h1>
            Your next contract.
            <br />
            <em>Already on your radar.</em>
          </h1>
          <p>
            Stop searching for tenders. Get public procurement opportunities
            matched to what your company actually does.
          </p>
          <div className="action-row">
            <Link className="button" href="/auth/signup">
              Find your opportunities
            </Link>
            <Link className="text-link" href="/example-report">
              See an example report
            </Link>
          </div>
          <small>
            Built for Belgian SMEs · 14-day trial · No payment card at signup
          </small>
        </div>
        <aside className="hero-report">
          <div className="report-heading">
            <span>THE OPPORTUNITY BRIEF</span>
            <span>Evidence, before opinion</span>
          </div>
          <h2>
            A clearer route from
            <br />
            notice to decision.
          </h2>
          <dl>
            <div>
              <dt>Company fit</dt>
              <dd>Your services, regions, and capabilities</dd>
            </div>
            <div>
              <dt>Requirements</dt>
              <dd>Source evidence with gaps made visible</dd>
            </div>
            <div>
              <dt>Next action</dt>
              <dd>Review, shortlist, or move on</dd>
            </div>
          </dl>
          <p>This is a product walkthrough, not a live tender.</p>
          <Link href="/how-it-works">Explore the workflow</Link>
        </aside>
      </section>
      <section className="value-strip">
        <p>Construction & renovation</p>
        <p>IT & cybersecurity</p>
        <p>Engineering & maintenance</p>
        <p>Professional services</p>
      </section>
      <section className="marketing-section split-editorial">
        <h2>
          Spend your time
          <br />
          on the right bids.
        </h2>
        <div>
          <p>
            Public notices are a starting point. Knowing which ones deserve your
            attention is the work.
          </p>
          <p>
            TenderLens compares official procurement records with your company
            profile, explains the overlap, and keeps possible blockers visible.
            A scheduled digest brings the shortlist to your inbox.
          </p>
          <Link className="text-link" href="/features">
            What you can do with TenderLens
          </Link>
        </div>
      </section>
      <section className="marketing-section process-list">
        <h2>
          From company profile
          <br />
          to a focused shortlist.
        </h2>
        <article>
          <h3>Tell us what you deliver</h3>
          <p>
            Add services, preferred regions, contract sizes, and the
            certifications you hold.
          </p>
        </article>
        <article>
          <h3>Review the evidence</h3>
          <p>
            Explore relevant notices, matching reasons, deadlines, and
            requirements that need a closer look.
          </p>
        </article>
        <article>
          <h3>Keep opportunities moving</h3>
          <p>
            Save the promising ones. Configure a digest. Return to the official
            source when you are ready to prepare a bid.
          </p>
        </article>
      </section>
      <section className="marketing-cta">
        <h2>
          Less searching.
          <br />
          More informed decisions.
        </h2>
        <Link className="button" href="/auth/signup">
          Build your first shortlist
        </Link>
        <p>
          TED covers published European notices. Belgian below-threshold
          coverage is limited; verify other official channels.
        </p>
      </section>
    </PublicShell>
  );
}
