"use client";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";
import { PublicShell } from "@/components/public-shell";
import { api } from "@/lib/api";
const titles: Record<string, string> = {
  login: "Welcome back.",
  signup: "A clearer view of your next opportunity.",
  forgot: "Reset your password.",
  reset: "Choose a new password.",
  verify: "Verify your email.",
  resend: "Request a verification email.",
};
export default function AuthPage() {
  const { mode } = useParams<{ mode: string }>();
  const router = useRouter();
  const [token, setToken] = useState("");
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    const value = new URLSearchParams(location.hash.slice(1)).get("token");
    if (value) {
      setToken(value);
      history.replaceState(null, "", location.pathname);
    }
  }, []);
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const endpoints: Record<string, string> = {
      login: "login",
      signup: "signup",
      forgot: "forgot-password",
      reset: "reset-password",
      verify: "verify",
      resend: "resend-verification",
    };
    const payload =
      mode === "verify"
        ? { token }
        : mode === "reset"
          ? { token, password: form.get("password") }
          : mode === "forgot" || mode === "resend"
            ? { email: form.get("email") }
            : {
                email: form.get("email"),
                password: form.get("password"),
                organization_name: form.get("organization_name"),
                accept_terms: form.get("terms") === "on",
              };
    try {
      const result = await api<{ message: string }>(
        `/auth/${endpoints[mode]}`,
        { method: "POST", body: JSON.stringify(payload) },
      );
      setMessage(result.message);
      if (mode === "login") {
        localStorage.removeItem("tenderlens.active-company");
        router.push("/dashboard");
      }
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "Unable to complete your request. Try again.",
      );
    } finally {
      setBusy(false);
    }
  };
  if (!titles[mode])
    return (
      <PublicShell>
        <section className="auth-card">
          <h1>Page unavailable</h1>
          <Link href="/auth/login">Sign in</Link>
        </section>
      </PublicShell>
    );
  return (
    <PublicShell>
      <section className="auth-layout">
        <div className="auth-intro">
          <h1>{titles[mode]}</h1>
          <p>
            Official procurement opportunities. Matching reasons you can
            inspect. A shortlist built around your business.
          </p>
          <Link className="text-link" href="/pricing">
            Explore the plans
          </Link>
        </div>
        <form className="auth-card" onSubmit={submit}>
          <h2>
            {mode === "signup"
              ? "Start your 14-day trial"
              : mode === "login"
                ? "Sign in to TenderLens"
                : "Secure account access"}
          </h2>
          {!["verify", "reset"].includes(mode) && (
            <label>
              Email address
              <input
                name="email"
                type="email"
                autoComplete="email"
                required
                maxLength={320}
              />
            </label>
          )}
          {mode === "signup" && (
            <label>
              Company name
              <input
                name="organization_name"
                autoComplete="organization"
                minLength={2}
                maxLength={256}
                required
              />
            </label>
          )}
          {["login", "signup", "reset"].includes(mode) && (
            <label>
              Password
              <input
                name="password"
                aria-label="Password"
                type="password"
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
                minLength={12}
                maxLength={128}
                required
              />
              <small>Use at least 12 characters.</small>
            </label>
          )}
          {["verify", "reset"].includes(mode) && !token && (
            <label>
              Verification token
              <input
                value={token}
                onChange={(event) => setToken(event.target.value)}
                required
                minLength={32}
              />
              <small>Open the link from your account email.</small>
            </label>
          )}
          {mode === "signup" && (
            <label className="checkbox-label">
              <input type="checkbox" name="terms" required />
              <span>
                I agree to the <Link href="/terms">terms</Link> and have read
                the <Link href="/privacy">privacy notice</Link>. Legal documents
                are pilot drafts.
              </span>
            </label>
          )}
          {error && (
            <p className="notice error" role="alert">
              {error}
            </p>
          )}
          {message && (
            <p className="notice" role="status">
              {message}
            </p>
          )}
          <button className="button" disabled={busy}>
            {busy
              ? "Please wait…"
              : mode === "login"
                ? "Sign in"
                : mode === "signup"
                  ? "Create your account"
                  : mode === "verify"
                    ? "Verify email"
                    : mode === "reset"
                      ? "Update password"
                      : "Send email"}
          </button>
          <div className="auth-links">
            <Link href="/auth/login">Sign in</Link>
            <Link href="/auth/signup">Create an account</Link>
            <Link href="/auth/forgot">Forgot password?</Link>
            <Link href="/auth/resend">Resend verification</Link>
          </div>
        </form>
      </section>
    </PublicShell>
  );
}
