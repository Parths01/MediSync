"use client";

import { useEffect, useState } from "react";

import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import {
  Appointment,
  AppointmentStatus,
  getAdminAppointments,
  updateAppointmentStatus,
} from "@/lib/api";

const statuses: AppointmentStatus[] = ["pending", "confirmed", "completed", "rejected", "cancelled"];

function isAppointmentStatus(value: string): value is AppointmentStatus {
  return statuses.includes(value as AppointmentStatus);
}

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

export function AdminAppointments() {
  const { user, loading: checkingUser, error: userError } = useProtectedUser("admin");
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [savingId, setSavingId] = useState<number | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getAdminAppointments(controller.signal)
      .then(setAppointments)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load appointments.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  async function saveStatus(appointmentId: number, nextStatus: AppointmentStatus) {
    setSavingId(appointmentId);
    setError(null);
    try {
      const updated = await updateAppointmentStatus(appointmentId, nextStatus);
      setAppointments((items) =>
        items.map((item) => (item.appointment_id === appointmentId ? updated : item)),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update appointment status.");
    } finally {
      setSavingId(null);
    }
  }

  if (checkingUser) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  return (
    <WorkspaceFrame description="Review patient appointment requests and update their status." role="admin" title="Appointments">
      {error && <WorkspaceError message={error} />}
      <section className="workspace-card">
        {loading && <p className="muted-copy">Loading appointments…</p>}
        {!loading && appointments.length === 0 && <div className="workspace-empty">No appointments found.</div>}
        {appointments.length > 0 && (
          <div className="table-wrap">
            <table className="workspace-table">
              <thead><tr><th>Patient</th><th>Doctor</th><th>Date</th><th>Reason</th><th>Status</th></tr></thead>
              <tbody>
                {appointments.map((appointment) => (
                  <tr key={appointment.appointment_id}>
                    <td>{appointment.patient_name}</td>
                    <td>Dr. {appointment.doctor_name}<br /><span className="muted-copy">{appointment.specialization}</span></td>
                    <td>{formatDate(appointment.appointment_date)}</td>
                    <td>{appointment.description}</td>
                    <td>
                      <select
                        aria-label={`Status for appointment ${appointment.appointment_id}`}
                        disabled={savingId === appointment.appointment_id}
                        onChange={(event) => {
                          if (isAppointmentStatus(event.target.value)) {
                            void saveStatus(appointment.appointment_id, event.target.value);
                          }
                        }}
                        value={appointment.status}
                      >
                        {statuses.map((status) => <option key={status} value={status}>{status}</option>)}
                      </select>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </WorkspaceFrame>
  );
}
