import Link from "next/link";
import example from "@/lib/example-notice.json";
import { notFound } from "next/navigation";
import { PublicShell } from "@/components/public-shell";
import { Plans } from "@/components/plans";
import { ContactForm } from "@/components/contact-form";
import { WorkspaceSection } from "@/components/workspace-section";

const pages: Record<
  string,
  { title: string; intro: string; sections: Array<[string, string]> }
> = {
  features: {
    title: "The notice is only the beginning.",
    intro:
      "Turn public procurement records into a shortlist your team can act on.",
    sections: [
      [
        "Discovery with provenance",
        "Search official TED records by text, buyer, country, classification and value. Open the original notice whenever you need to verify a detail.",
      ],
      [
        "Matching you can inspect",
        "Company services, capabilities and delivery preferences contribute to a transparent score. Missing eligibility information stays visible; it never becomes a guarantee.",
      ],
      [
        "An evidence-led brief",
        "Inspect a source summary, extracted requirements and potential blockers. Optional AI stays behind provider configuration and validated evidence.",
      ],
      [
        "A shortlist that keeps moving",
        "Save opportunities, compare notices, record relevance feedback and configure a scheduled digest. Pilot digests can be reviewed by an administrator before delivery.",
      ],
    ],
  },
  "how-it-works": {
    title: "A shortlist shaped around your business.",
    intro:
      "Set up your profile once. Keep it current as your capabilities change.",
    sections: [
      [
        "Describe your company",
        "Enter the services you deliver, preferred regions, languages, contract size and certifications. No CPV expertise required.",
      ],
      [
        "Choose your delivery preferences",
        "Weekly is the default. Professional and Business support daily delivery and saved-opportunity deadline reminders. Change preferences at any time.",
      ],
      [
        "Inspect the reasons",
        "Open a matched tender to see the buyer, official deadline, value where available, matching reasons and source evidence. Unknown information remains unknown.",
      ],
      [
        "Make your bid decision",
        "Review mandatory conditions in the official notice. Save promising contracts and dismiss irrelevant ones. TenderLens supports your judgment; it does not decide eligibility.",
      ],
    ],
  },
  faq: {
    title: "A few useful answers.",
    intro: "What to know before you begin.",
    sections: [
      [
        "Does this cover every Belgian tender?",
        "No. Automated ingestion currently uses TED. Belgian opportunities below European publication thresholds may require additional official channels. Belgian e-Procurement integration is not claimed.",
      ],
      [
        "Do I need an AI subscription?",
        "No. Discovery, deterministic matching, saved opportunities and scheduled digests operate without an LLM. Optional AI features require separate operator configuration.",
      ],
      [
        "Is a high score proof of eligibility?",
        "No. It is a relevance signal using available information. Check mandatory certifications, financial requirements and the official submission instructions.",
      ],
      [
        "Can I cancel or change plans?",
        "The Stripe test billing portal supports subscription management when configured. Production billing and invoicing require founder activation and accounting review.",
      ],
      [
        "Will emails arrive immediately?",
        "Local mode records emails without sending. In a configured pilot, verified sandbox recipients can receive approved digests through the transactional provider.",
      ],
      [
        "Which languages are supported?",
        "Profiles accept English, Dutch and French terms. Deterministic matching includes a small multilingual vocabulary; semantic equivalence is not guaranteed. The full interface currently uses English.",
      ],
    ],
  },
  privacy: {
    title: "Privacy notice — draft for legal review.",
    intro:
      "This pilot notice requires the operator’s legal identity, contact details and reviewed processing arrangements before commercial activation.",
    sections: [
      [
        "Information we process",
        "Account email, password hash, organization membership, company profiles, saved tenders, feedback, notification preferences and delivery logs. Public procurement records retain official provenance.",
      ],
      [
        "Purposes and legal bases",
        "Service delivery and account security support the contract; operational security may rely on legitimate interests after assessment. Pilot inquiries include consent to a response. Final legal bases must be reviewed by counsel.",
      ],
      [
        "Providers and transfers",
        "Configured hosting, Stripe test billing, optional Resend and optional OpenAI may process data. Select regions, execute required DPAs, assess transfers and publish the final subprocessor register before activation.",
      ],
      [
        "Retention and your rights",
        "Expired sessions and tokens are cleaned by the worker. Completed delivery logs are retained for 90 days. Export your workspace in account settings. An owner can request organization deletion; the operator must resolve billing and legal retention before erasure. Backup retention must be configured.",
      ],
      [
        "Contact and complaints",
        "Use the contact page for privacy requests during the pilot. The operator must publish a direct privacy contact. Individuals may complain to the Belgian Data Protection Authority. This draft is not a compliance certification.",
      ],
    ],
  },
  terms: {
    title: "Terms of service — draft for legal review.",
    intro:
      "Controlled B2B pilot terms. The contracting entity, registered address, enterprise/VAT numbers and applicable commercial terms must be completed before paid activation.",
    sections: [
      [
        "The service",
        "TenderLens provides procurement discovery and decision support from published information. Source coverage, extraction and matching can be incomplete. The official procurement notice controls.",
      ],
      [
        "Your responsibilities",
        "Provide accurate profile information, safeguard credentials and review deadlines and eligibility independently. Do not submit confidential tender materials without authorization.",
      ],
      [
        "Trials and subscriptions",
        "Proposed monthly prices are configurable hypotheses. The local trial lasts 14 days. Current checkout is test-mode only; no live payment is authorized. VAT, renewal, cancellation and refund terms require review before paid launch.",
      ],
      [
        "Service boundaries",
        "No award, eligibility, tender coverage or uninterrupted availability is guaranteed. Procurement authorities and TED do not endorse this service. Liability, governing law, dispute handling and support commitments require counsel’s approval.",
      ],
      [
        "Suspension and deletion",
        "Access may end when a trial or subscription expires. Privacy export remains available. Organization owners can request deletion; legally required records and external billing must be handled separately.",
      ],
    ],
  },
  cookies: {
    title: "Cookies and local storage.",
    intro:
      "The current application uses storage necessary to operate your account. No advertising or third-party analytics are included.",
    sections: [
      [
        "Session cookie",
        "The HttpOnly TenderLens session cookie identifies an expiring server-side session. It uses SameSite=Lax and Secure in production. Signing out revokes the server session.",
      ],
      [
        "Browser preferences",
        "Local storage remembers the selected company profile and interface language. The backend checks ownership independently; local storage never grants access.",
      ],
      [
        "Optional tracking",
        "No optional tracking cookies are implemented. Review consent requirements before adding analytics, advertising or third-party embeds. Final legal classification requires review.",
      ],
    ],
  },
};

export default async function SectionPage({
  params,
}: {
  params: Promise<{ section: string }>;
}) {
  const { section } = await params;
  if (
    ["notifications", "billing", "settings", "compare", "admin"].includes(
      section,
    )
  )
    return <WorkspaceSection section={section} />;
  if (section === "pricing")
    return (
      <PublicShell>
        <section className="marketing-section">
          <h1>A plan for your tender pipeline.</h1>
          <p className="lead">
            Start with a trial. Choose the depth and frequency your team needs.
          </p>
          <Plans />
        </section>
      </PublicShell>
    );
  if (section === "contact")
    return (
      <PublicShell>
        <section className="marketing-section split-editorial">
          <div>
            <h1>Let’s find your first useful match.</h1>
            <p>
              Tell us about your company and the contracts you want to pursue.
              Pilot inquiries are stored for the founder to review.
            </p>
          </div>
          <ContactForm />
        </section>
      </PublicShell>
    );
  if (section === "example-report")
    return (
      <PublicShell>
        <article className="reading-page">
          <h1>What a useful tender brief looks like.</h1>
          <p className="notice">
            Example format, using the repository’s reviewed historical TED
            record. This is not an active opportunity or a personalized
            eligibility assessment.
          </p>
          <h2>{example.title}</h2>
          <dl className="report-facts">
            <div>
              <dt>Contracting authority</dt>
              <dd>
                {example.buyer} · {example.country}
              </dd>
            </div>
            <div>
              <dt>Published scope</dt>
              <dd>
                Framework for information-model coordination, inventory
                measurement and modeling services. Reader translation of the
                Finnish title; verify the official notice.
              </dd>
            </div>
            <div>
              <dt>Publication</dt>
              <dd>{example.publication_date}</dd>
            </div>
            <div>
              <dt>Submission deadline</dt>
              <dd>
                {example.submission_deadline} — historical, already passed
              </dd>
            </div>
            <div>
              <dt>Published estimated value</dt>
              <dd>
                €10,000,000 EUR at procedure level. This is not a promised
                project budget or revenue.
              </dd>
            </div>
            <div>
              <dt>Procedure / CPV</dt>
              <dd>
                {example.procedure} / {example.cpv_codes.join(", ")}
              </dd>
            </div>
            <div>
              <dt>Eligibility</dt>
              <dd>
                Not assessed in this example. Certifications, turnover and
                submission conditions require document review.
              </dd>
            </div>
          </dl>
          <p>
            The record below is linked to its official source. No contract
            value, deadline or eligibility requirement is invented for this
            example.
          </p>
          <a
            className="text-link"
            href="https://ted.europa.eu/en/notice/-/detail/556965-2026"
            target="_blank"
            rel="noopener noreferrer"
          >
            Open the official notice
          </a>
          <dl className="report-facts">
            <div>
              <dt>What the brief contains</dt>
              <dd>
                Buyer, published scope, geography, deadline and value where
                officially available.
              </dd>
            </div>
            <div>
              <dt>Why it might fit</dt>
              <dd>
                A component score and matching terms from your own profile. No
                personalized score is shown in this example.
              </dd>
            </div>
            <div>
              <dt>Requirements to verify</dt>
              <dd>
                Each extracted condition links to processed source evidence.
                Unprocessed documents are reported.
              </dd>
            </div>
            <div>
              <dt>Bid decision support</dt>
              <dd>
                Review mandatory requirements, resources and submission
                instructions before preparing a bid.
              </dd>
            </div>
          </dl>
          <Link className="button" href="/auth/signup">
            Create your own company profile
          </Link>
        </article>
      </PublicShell>
    );
  const page = pages[section];
  if (!page) notFound();
  return (
    <PublicShell>
      <article className="reading-page">
        <h1>{page.title}</h1>
        <p className="lead">{page.intro}</p>
        {page.sections.map(([title, body]) => (
          <section key={title}>
            <h2>{title}</h2>
            <p>{body}</p>
          </section>
        ))}
        <Link className="text-link" href="/contact">
          Talk to the founder
        </Link>
      </article>
    </PublicShell>
  );
}
