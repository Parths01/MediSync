"use client";

import { ListPagination } from "@/components/list-pagination";
import { API_PAGE_SIZE } from "@/lib/api";

import Link from "next/link";
import { useEffect, useState } from "react";

import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import { Appointment, getMyAppointments, cancelAppointment } from "@/lib/api";

function displayDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function PatientDashboard() {
  const { user, loading: checkingUser, error: userError } = useProtectedUser("patient");
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [loadingAppointments, setLoadingAppointments] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [hasMoreAppointments, setHasMoreAppointments] = useState(false);
  const [loadingMoreAppointments, setLoadingMoreAppointments] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    getMyAppointments(controller.signal)
      .then((records) => {
        setAppointments(records);
        setHasMoreAppointments(records.length === API_PAGE_SIZE);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load appointments.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoadingAppointments(false);
      });
    return () => controller.abort();
  }, []);

  async function handleCancel(appointmentId: number) {
    setActionError(null);
    try {
      const updated = await cancelAppointment(appointmentId);
      setAppointments((items) =>
        items.map((item) => (item.appointment_id === appointmentId ? updated : item)),
      );
    } catch (reason) {
      setActionError(reason instanceof Error ? reason.message : "Could not cancel this appointment.");
    }
  }

  if (checkingUser) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  const upcoming = appointments.filter(
    (appointment) =>
      new Date(appointment.appointment_date) >= new Date() &&
      ["pending", "confirmed"].includes(appointment.status),
  );

  return (
    <WorkspaceFrame
      description={`Welcome, ${user.name}. Review your upcoming visits and manage your care details.`}
      role="patient"
      title="Your care dashboard"
    >
      <div className="workspace-actions">
        <Link className="button button-primary" href="/doctors">Find a doctor</Link>
        <Link className="button button-outline" href="/history">View health history</Link>
      </div>
      <section className="workspace-card">
        <div className="workspace-card-heading">
          <div>
            <h2>Upcoming appointments</h2>
            <p>{upcoming.length} upcoming {upcoming.length === 1 ? "visit" : "visits"}</p>
          </div>
        </div>
        {error && <WorkspaceError message={error} />}
        {actionError && <WorkspaceError message={actionError} />}
        {loadingAppointments && <p className="muted-copy">Loading appointments…</p>}
        {!loadingAppointments && !error && upcoming.length === 0 && (
          <div className="workspace-empty">
            <p>You have no upcoming appointments.</p>
            <Link href="/doctors">Browse doctors</Link>
          </div>
        )}
        <div className="workspace-list">
          {hasMoreAppointments && (
            <ListPagination
              count={appointments.length}
              hasMore={hasMoreAppointments}
              loading={loadingMoreAppointments}
              onLoadMore={() => {
                setLoadingMoreAppointments(true);
                getMyAppointments(undefined, API_PAGE_SIZE, appointments.length)
                  .then((records) => {
                    setAppointments((current) => [...current, ...records]);
                    setHasMoreAppointments(records.length === API_PAGE_SIZE);
                  })
                  .catch((reason: unknown) => {
                    setError(reason instanceof Error ? reason.message : "Could not load more appointments.");
                  })
                  .finally(() => setLoadingMoreAppointments(false));
              }}
            />
          )}
          {upcoming.map((appointment) => (
            <article className="workspace-list-item" key={appointment.appointment_id}>
              <div>
                <h3>Dr. {appointment.doctor_name}</h3>
                <p>{appointment.specialization}</p>
                <p>{displayDate(appointment.appointment_date)}</p>
                {appointment.description && <p className="muted-copy">{appointment.description}</p>}
              </div>
              <div className="workspace-item-actions">
                <span className={`status-pill status-${appointment.status}`}>{appointment.status}</span>
                {["pending", "confirmed"].includes(appointment.status) && (
                  <button
                    className="text-button"
                    onClick={() => void handleCancel(appointment.appointment_id)}
                    type="button"
                  >
                    {appointment.status === "confirmed" ? "Cancel appointment" : "Cancel request"}
                  </button>
                )}
              </div>
            </article>
          ))}
        </div>
      </section>
    </WorkspaceFrame>
  );
}
