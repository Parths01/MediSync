"use client";

import { FormEvent, useEffect, useState } from "react";

import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import { MedicalHistory, addMedicalHistory, getMedicalHistory } from "@/lib/api";

export function PatientHistory() {
  const { user, loading: checkingUser, error: userError } = useProtectedUser("patient");
  const [entries, setEntries] = useState<MedicalHistory[]>([]);
  const [loadingEntries, setLoadingEntries] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getMedicalHistory(controller.signal)
      .then(setEntries)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load health history.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingEntries(false);
      });
    return () => controller.abort();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    try {
      const entry = await addMedicalHistory({
        diagnosis: String(form.get("diagnosis") ?? ""),
        treatment: String(form.get("treatment") ?? ""),
        notes: String(form.get("notes") ?? ""),
        recorded_at: String(form.get("recorded_at") ?? ""),
      });
      setEntries((current) => [entry, ...current]);
      setSuccess("Health history entry saved.");
      formElement.reset();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save this entry.");
    } finally {
      setSaving(false);
    }
  }

  if (checkingUser) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  return (
    <WorkspaceFrame
      description="Your health history is private to your account."
      role="patient"
      title="My health history"
    >
      <section className="workspace-card form-card">
        <h2>Add a history entry</h2>
        <p className="muted-copy">Record information you want to keep for your own reference.</p>
        {error && <WorkspaceError message={error} />}
        {success && <div className="form-alert form-alert-success" role="status">{success}</div>}
        <form className="stacked-form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label>
              Diagnosis or topic
              <input maxLength={255} name="diagnosis" required />
            </label>
            <label>
              Record date
              <input max={new Date().toISOString().slice(0, 10)} name="recorded_at" required type="date" />
            </label>
          </div>
          <label>
            Treatment
            <textarea maxLength={10000} name="treatment" rows={3} />
          </label>
          <label>
            Notes
            <textarea maxLength={10000} name="notes" rows={3} />
          </label>
          <button className="button button-primary form-submit" disabled={saving} type="submit">
            {saving ? "Saving…" : "Save entry"}
          </button>
        </form>
      </section>

      <section className="workspace-card">
        <div className="workspace-card-heading">
          <div><h2>Saved entries</h2><p>Only you can view these records.</p></div>
        </div>
        {loadingEntries && <p className="muted-copy">Loading history…</p>}
        {!loadingEntries && !error && entries.length === 0 && (
          <div className="workspace-empty">No health history entries yet.</div>
        )}
        <div className="workspace-list">
          {entries.map((entry) => (
            <article className="workspace-list-item" key={entry.history_id}>
              <div>
                <h3>{entry.diagnosis}</h3>
                <p>Recorded {new Intl.DateTimeFormat(undefined, { dateStyle: "medium" }).format(new Date(`${entry.recorded_at}T00:00:00`))}</p>
                {entry.treatment && <p><strong>Treatment:</strong> {entry.treatment}</p>}
                {entry.notes && <p><strong>Notes:</strong> {entry.notes}</p>}
              </div>
            </article>
          ))}
        </div>
      </section>
    </WorkspaceFrame>
  );
}
