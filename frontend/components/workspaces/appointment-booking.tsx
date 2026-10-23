"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import { Doctor, bookAppointment, getDoctors } from "@/lib/api";

function localDateTimeMinimum(): string {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 16);
}

export function AppointmentBooking({ initialDoctorId }: { initialDoctorId: number | null }) {
  const router = useRouter();
  const { user, loading: checkingUser, error: userError } = useProtectedUser("patient");
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [doctorId, setDoctorId] = useState(initialDoctorId?.toString() ?? "");
  const [loadingDoctors, setLoadingDoctors] = useState(true);
  const [dateTime, setDateTime] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getDoctors(controller.signal)
      .then(setDoctors)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load doctors.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingDoctors(false);
      });
    return () => controller.abort();
  }, []);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await bookAppointment({
        doctor_id: Number(doctorId),
        appointment_date: new Date(dateTime).toISOString(),
        description,
      });
      router.replace("/dashboard");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not book this appointment.");
    } finally {
      setSaving(false);
    }
  }

  if (checkingUser) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  return (
    <WorkspaceFrame
      description="Choose a specialist and request a future appointment time."
      role="patient"
      title="Book an appointment"
    >
      <section className="workspace-card form-card">
        {error && <WorkspaceError message={error} />}
        {loadingDoctors ? (
          <p className="muted-copy">Loading doctors…</p>
        ) : doctors.length === 0 ? (
          <div className="workspace-empty">There are no doctors available to book right now.</div>
        ) : (
          <form className="stacked-form" onSubmit={handleSubmit}>
            <label>
              Doctor
              <select
                onChange={(event) => setDoctorId(event.target.value)}
                required
                value={doctorId}
              >
                <option value="">Select a doctor</option>
                {doctors.map((doctor) => (
                  <option key={doctor.doctor_id} value={doctor.doctor_id}>
                    Dr. {doctor.name} — {doctor.specialization}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Date and time
              <input
                min={localDateTimeMinimum()}
                onChange={(event) => setDateTime(event.target.value)}
                required
                type="datetime-local"
                value={dateTime}
              />
            </label>
            <label>
              Reason for visit
              <textarea
                maxLength={10000}
                onChange={(event) => setDescription(event.target.value)}
                required
                rows={5}
                value={description}
              />
              <span className="field-help">Share only the information needed to request your visit.</span>
            </label>
            <button className="button button-primary form-submit" disabled={saving} type="submit">
              {saving ? "Sending request…" : "Request appointment"}
            </button>
          </form>
        )}
      </section>
    </WorkspaceFrame>
  );
}
