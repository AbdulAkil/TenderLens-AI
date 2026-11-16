import type { Metadata } from "next";
import "./globals.css";
import "./commercial.css";

export const metadata: Metadata = {
  title: "TenderLens AI — Procurement intelligence",
  description:
    "Evidence-led procurement intelligence for European opportunities.",
  metadataBase: new URL(
    process.env.NEXT_PUBLIC_SITE_URL || "http://localhost:3000",
  ),
  openGraph: {
    title: "TenderLens AI",
    description:
      "Evidence-led procurement intelligence for European opportunities.",
    images: [
      { url: "/og.png", width: 1798, height: 940, alt: "TenderLens AI" },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "TenderLens AI",
    images: ["/og.png"],
  },
};

export default function RootLayout({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
