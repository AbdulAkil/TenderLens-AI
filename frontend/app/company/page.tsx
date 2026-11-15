"use client";
import { AppShell } from "@/components/app-shell";
import { CompanyEditor } from "@/components/company-editor";
export default function CompanyPage() {
  return (
    <AppShell>
      <CompanyEditor />
    </AppShell>
  );
}
