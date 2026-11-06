"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";

import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import {
  AppointmentAvailabilityDay,
  Doctor,
  bookAppointment,
  getAppointmentAvailability,
  getDoctors,
} from "@/lib/api";

function formatClinicDate(date: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    weekday: "long",
    day: "numeric",
    month: "long",
    timeZone: "Asia/Kolkata",
  }).format(new Date(`${date}T00:00:00+05:30`));
}

function formatClinicTime(time: string): string {
  const [hours, minutes] = time.split(":").map(Number);
  const hour = hours % 12 || 12;
  return `${hour}:${minutes.toString().padStart(2, "0")} ${hours < 12 ? "AM" : "PM"} IST`;
}

export function AppointmentBooking({ initialDoctorId }: { initialDoctorId: number | null }) {
  const router = useRouter();
  const { user, loading: checkingUser, error: userError } = useProtectedUser("patient");
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [doctorId, setDoctorId] = useState(initialDoctorId?.toString() ?? "");
  const [loadingDoctors, setLoadingDoctors] = useState(true);
  const [availability, setAvailability] = useState<AppointmentAvailabilityDay[]>([]);
  const [loadingAvailability, setLoadingAvailability] = useState(false);
  const [selectedDate, setSelectedDate] = useState("");
  const [selectedTime, setSelectedTime] = useState("");
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

  useEffect(() => {
    if (checkingUser) return;

    if (!user) {
      setAvailability([]);
      setSelectedDate("");
      setSelectedTime("");
      setLoadingAvailability(false);
      return;
    }

    if (!doctorId) {
      setAvailability([]);
      setSelectedDate("");
      setSelectedTime("");
      setLoadingAvailability(false);
      return;
    }

    const controller = new AbortController();
    setAvailability([]);
    setSelectedDate("");
    setSelectedTime("");
    setLoadingAvailability(true);
    setError(null);

    getAppointmentAvailability(Number(doctorId), controller.signal)
      .then((days) => {
        setAvailability(days);
        setSelectedDate(days[0]?.date ?? "");
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load available times.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingAvailability(false);
      });

    return () => controller.abort();
  }, [checkingUser, doctorId, user]);

  const selectedDay = availability.find((day) => day.date === selectedDate);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await bookAppointment({
        doctor_id: Number(doctorId),
        appointment_date: new Date(`${selectedDate}T${selectedTime}:00+05:30`).toISOString(),
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
              Available date (India time)
              <select
                disabled={!doctorId || loadingAvailability || availability.length === 0}
                onChange={(event) => {
                  setSelectedDate(event.target.value);
                  setSelectedTime("");
                }}
                required
                value={selectedDate}
              >
                <option value="">
                  {loadingAvailability ? "Loading available dates…" : "Select a date"}
                </option>
                {availability.map((day) => (
                  <option key={day.date} value={day.date}>
                    {formatClinicDate(day.date)}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Available time (30-minute slots)
              <select
                disabled={!selectedDay || loadingAvailability}
                onChange={(event) => setSelectedTime(event.target.value)}
                required
                value={selectedTime}
              >
                <option value="">Select a time</option>
                {selectedDay?.slots.map((time) => (
                  <option key={time} value={time}>
                    {formatClinicTime(time)}
                  </option>
                ))}
              </select>
              <span className="field-help">
                Monday–Saturday, 9:00 AM–4:30 PM IST, for the next 30 days.
              </span>
            </label>
            {doctorId && !loadingAvailability && availability.length === 0 && !error && (
              <p className="field-help">No appointment slots are available in the next 30 days.</p>
            )}
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
            <button
              className="button button-primary form-submit"
              disabled={saving || loadingAvailability || !selectedDate || !selectedTime}
              type="submit"
            >
              {saving ? "Sending request…" : "Request appointment"}
            </button>
          </form>
        )}
      </section>
    </WorkspaceFrame>
  );
}
