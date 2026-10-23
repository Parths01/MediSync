"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";

import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import { SymptomResult, getSymptomRecommendations } from "@/lib/api";

export function SymptomChecker() {
  const { user, loading, error: userError } = useProtectedUser("patient");
  const [result, setResult] = useState<SymptomResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [checking, setChecking] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setError(null);
    setResult(null);
    setChecking(true);
    try {
      setResult(await getSymptomRecommendations(String(form.get("symptoms") ?? "")));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not find recommendations.");
    } finally {
      setChecking(false);
    }
  }

  if (loading) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  return (
    <WorkspaceFrame
      description="Explore specialty suggestions from a small machine-learning demo."
      role="patient"
      title="Find a specialist"
    >
      <section className="workspace-card form-card">
        <div className="form-alert form-alert-info">
          Demo only: this model was trained on synthetic examples and has not been clinically
          validated. Suggestions are not medical advice or a diagnosis; do not use them to make
          care decisions. For urgent or emergency symptoms, contact local emergency services.
        </div>
        {error && <WorkspaceError message={error} />}
        <form className="stacked-form" onSubmit={handleSubmit}>
          <label>
            Describe what you are looking for
            <textarea maxLength={2000} minLength={1} name="symptoms" required rows={5} />
          </label>
          <button className="button button-primary form-submit" disabled={checking} type="submit">
            {checking ? "Checking…" : "Find matching specialties"}
          </button>
        </form>
      </section>

      {result && (
        <>
          <div className="form-alert form-alert-info" role="note">{result.disclaimer}</div>
          <section className="workspace-card">
            <h2>Demo model suggestions</h2>
            {result.recommendations.length === 0 ? (
              <div className="workspace-empty">No specialty keywords matched. You can browse all doctors instead.</div>
            ) : (
              <div className="workspace-list">
                {result.recommendations.map((recommendation, index) => (
                  <article className="workspace-list-item" key={recommendation.specialty}>
                    <div>
                      <h3>{index + 1}. {recommendation.specialty}</h3>
                      <p>Prototype ranking only · not a clinical assessment</p>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </section>
          <section className="workspace-card">
            <h2>Doctors in matching specialties</h2>
            {result.doctors.length === 0 ? (
              <div className="workspace-empty">
                No listed doctors matched. <Link href="/doctors">Browse the full directory</Link>.
              </div>
            ) : (
              <div className="workspace-list">
                {result.doctors.map((doctor) => (
                  <article className="workspace-list-item" key={doctor.doctor_id}>
                    <div>
                      <h3>Dr. {doctor.name}</h3>
                      <p>{doctor.specialization} · {doctor.experience} years experience</p>
                    </div>
                    <Link className="button button-outline" href={`/appointments/new?doctor_id=${doctor.doctor_id}`}>
                      Request a visit
                    </Link>
                  </article>
                ))}
              </div>
            )}
          </section>
        </>
      )}
    </WorkspaceFrame>
  );
}
