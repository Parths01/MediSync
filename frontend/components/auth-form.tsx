"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { login, register } from "@/lib/api";

function getGender(value: FormDataEntryValue | null): "Male" | "Female" | "Other" {
  return value === "Male" || value === "Female" || value === "Other" ? value : "Other";
}

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const isRegister = mode === "register";

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setLoading(true);

    const form = new FormData(event.currentTarget);
    const email = String(form.get("email") ?? "");
    const password = String(form.get("password") ?? "");

    try {
      const result = isRegister
        ? await register({
            name: String(form.get("name") ?? ""),
            dob: String(form.get("dob") ?? ""),
            gender: getGender(form.get("gender")),
            contact: String(form.get("contact") ?? ""),
            email,
            password,
            blood_group: String(form.get("blood_group") ?? "") || null,
          })
        : await login(email, password);

      const requestedPath =
        typeof window === "undefined"
          ? null
          : new URLSearchParams(window.location.search).get("next");
      const safeRequestedPath =
        requestedPath?.startsWith("/") && !requestedPath.startsWith("//")
          ? requestedPath
          : null;
      router.replace(
        safeRequestedPath ?? (result.user.role === "admin" ? "/admin" : "/dashboard"),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not sign in. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <section className="auth-section">
      <div className="auth-card">
        <span className="section-kicker">{isRegister ? "GET STARTED" : "WELCOME BACK"}</span>
        <h1>{isRegister ? "Create your account" : "Sign in to MediSync"}</h1>
        <p className="muted-copy">
          {isRegister
            ? "Create a patient account to manage your appointments and health history."
            : "Use your account to manage appointments and care details."}
        </p>

        {error && <div className="form-alert form-alert-error" role="alert">{error}</div>}

        <form className="stacked-form" onSubmit={handleSubmit}>
          {isRegister && (
            <>
              <label>
                Full name
                <input autoComplete="name" maxLength={255} name="name" required />
              </label>
              <div className="form-grid">
                <label>
                  Date of birth
                  <input autoComplete="bday" max={new Date().toISOString().slice(0, 10)} name="dob" required type="date" />
                </label>
                <label>
                  Gender
                  <select autoComplete="sex" defaultValue="Other" name="gender" required>
                    <option>Female</option>
                    <option>Male</option>
                    <option>Other</option>
                  </select>
                </label>
              </div>
              <div className="form-grid">
                <label>
                  Contact number
                  <input autoComplete="tel" maxLength={15} name="contact" required />
                </label>
                <label>
                  Blood group <span className="field-optional">(optional)</span>
                  <select defaultValue="" name="blood_group">
                    <option value="">Prefer not to say</option>
                    {["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((group) => (
                      <option key={group}>{group}</option>
                    ))}
                  </select>
                </label>
              </div>
            </>
          )}
          <label>
            Email
            <input autoComplete="email" maxLength={255} name="email" required type="email" />
          </label>
          <label>
            Password
            <input
              autoComplete={isRegister ? "new-password" : "current-password"}
              maxLength={128}
              minLength={8}
              name="password"
              required
              type="password"
            />
          </label>
          <button className="button button-primary form-submit" disabled={loading} type="submit">
            {loading ? "Please wait…" : isRegister ? "Create account" : "Sign in"}
          </button>
        </form>

        <p className="auth-switch">
          {isRegister ? "Already have an account?" : "New to MediSync?"}{" "}
          <Link href={isRegister ? "/login" : "/register"}>
            {isRegister ? "Sign in" : "Create an account"}
          </Link>
        </p>
      </div>
    </section>
  );
}
