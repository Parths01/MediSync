"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  Activity,
  ArrowUpRight,
  CalendarDays,
  CheckCircle2,
  Clock3,
  Stethoscope,
  UsersRound,
} from "lucide-react";

import {
  WorkspaceError,
  WorkspaceFrame,
  WorkspaceLoading,
  useProtectedUser,
} from "@/components/protected-workspace";
import { AdminDashboard, AppointmentStatus, getAdminDashboard } from "@/lib/api";

const statusOrder: AppointmentStatus[] = [
  "pending",
  "confirmed",
  "completed",
  "cancelled",
  "rejected",
];

const statusLabels: Record<AppointmentStatus, string> = {
  pending: "Pending",
  confirmed: "Confirmed",
  completed: "Completed",
  cancelled: "Cancelled",
  rejected: "Rejected",
};

function formatDate(value: string): string {
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

function StatusChart({ data }: { data: AdminDashboard }) {
  const circumference = 2 * Math.PI * 43;
  const total = statusOrder.reduce(
    (sum, status) => sum + data.appointment_status_counts[status],
    0,
  );
  let offset = 0;

  return (
    <section className="workspace-card admin-chart-card">
      <div className="workspace-card-heading">
        <div>
          <span className="admin-chart-eyebrow">Appointment overview</span>
          <h2>Booking status</h2>
          <p>All appointment records, by current status</p>
        </div>
        <span className="admin-chart-icon"><Activity aria-hidden="true" size={19} /></span>
      </div>
      {total === 0 ? (
        <div className="workspace-empty">Status breakdown will appear when appointments are added.</div>
      ) : (
        <div className="status-chart-layout">
          <div className="status-donut-wrap">
            <svg
              aria-label={`${total} appointments in total`}
              className="status-donut"
              role="img"
              viewBox="0 0 112 112"
            >
              <circle className="status-donut-track" cx="56" cy="56" r="43" />
              {statusOrder.map((status) => {
                const count = data.appointment_status_counts[status];
                const segment = (count / total) * circumference;
                const circle = (
                  <circle
                    className={`status-donut-segment status-donut-${status}`}
                    cx="56"
                    cy="56"
                    key={status}
                    r="43"
                    strokeDasharray={`${segment} ${circumference - segment}`}
                    strokeDashoffset={-offset}
                  />
                );
                offset += segment;
                return circle;
              })}
            </svg>
            <div className="status-donut-center">
              <strong>{total}</strong>
              <span>bookings</span>
            </div>
          </div>
          <ul className="status-chart-legend">
            {statusOrder.map((status) => (
              <li key={status}>
                <span className={`status-legend-dot status-legend-${status}`} />
                <span>{statusLabels[status]}</span>
                <strong>{data.appointment_status_counts[status]}</strong>
              </li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function MonthlySeries({
  label,
  values,
  color,
}: {
  label: string;
  values: AdminDashboard["monthly_appointments"];
  color: "appointments" | "patients";
}) {
  const maxValue = Math.max(1, ...values.map((item) => item.count));
  const formatMonth = (value: string) =>
    new Intl.DateTimeFormat(undefined, { month: "short" }).format(
      new Date(`${value}-01T00:00:00`),
    );
  const formatRange = () => {
    const first = values[0]?.month;
    const last = values.at(-1)?.month;
    if (!first || !last) return "No date range";
    const format = (value: string) =>
      new Intl.DateTimeFormat(undefined, { month: "short", year: "numeric" }).format(
        new Date(`${value}-01T00:00:00`),
      );
    return `${format(first)} – ${format(last)}`;
  };
  return (
    <div className="monthly-series">
      <div className="monthly-series-heading">
        <h3>{label}</h3>
        <span>{formatRange()}</span>
      </div>
      {values.every((item) => item.count === 0) ? (
        <div className="monthly-series-empty">No recorded activity yet</div>
      ) : (
        <>
          <div
            aria-label={`${label} by month`}
            className="monthly-chart"
            role="img"
          >
            {values.map((item) => {
              return (
                <div className="monthly-chart-column" key={item.month}>
                  <div className="monthly-chart-bars">
                    <span
                      className={`monthly-bar monthly-bar-${color}`}
                      style={{ height: `${Math.max(item.count ? 8 : 2, (item.count / maxValue) * 100)}%` }}
                      title={`${item.count} ${label.toLowerCase()}`}
                    />
                  </div>
                  <span className="monthly-chart-label">{formatMonth(item.month)}</span>
                </div>
              );
            })}
          </div>
        </>
      )}
    </div>
  );
}

function MonthlyActivityChart({ data }: { data: AdminDashboard }) {
  return (
    <section className="workspace-card admin-chart-card">
      <div className="workspace-card-heading">
        <div>
          <span className="admin-chart-eyebrow">Growth &amp; activity</span>
          <h2>Monthly trends</h2>
          <p>Six months of recorded activity for each metric</p>
        </div>
        <span className="admin-chart-icon admin-chart-icon-blue">
          <CalendarDays aria-hidden="true" size={19} />
        </span>
      </div>
      <div className="monthly-trends">
        <MonthlySeries color="appointments" label="Appointments" values={data.monthly_appointments} />
        <MonthlySeries color="patients" label="New patients" values={data.monthly_registrations} />
      </div>
    </section>
  );
}

export function AdminDashboardPage() {
  const { user, loading: checkingUser, error: userError } = useProtectedUser("admin");
  const [data, setData] = useState<AdminDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getAdminDashboard(controller.signal)
      .then(setData)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load the admin dashboard.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  if (checkingUser) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  const hour = new Date().getHours();
  const greeting = hour < 12 ? "Good morning" : hour < 18 ? "Good afternoon" : "Good evening";
  const today = new Intl.DateTimeFormat(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  }).format(new Date());

  return (
    <WorkspaceFrame description={`Signed in as ${user.name}.`} role="admin" title="Admin overview">
      {error && <WorkspaceError message={error} />}
      {loading && <WorkspaceLoading message="Loading dashboard metrics…" />}
      {data && (
        <>
          <section className="admin-dashboard-hero">
            <div className="admin-dashboard-hero-copy">
              <span className="admin-dashboard-live"><i /> Clinic overview</span>
              <h2>{greeting}, {user.name.split(" ")[0]}.</h2>
              <p>Here&apos;s what&apos;s happening across your practice today.</p>
            </div>
            <div className="admin-dashboard-date">
              <CalendarDays aria-hidden="true" size={17} />
              <span>{today}</span>
            </div>
            <div aria-hidden="true" className="admin-hero-orb admin-hero-orb-one" />
            <div aria-hidden="true" className="admin-hero-orb admin-hero-orb-two" />
          </section>

          <section aria-label="MediSync metrics" className="admin-stat-grid">
            <article className="admin-stat-card">
              <span className="admin-stat-icon admin-stat-icon-mint"><UsersRound aria-hidden="true" size={19} /></span>
              <span className="admin-stat-label">Total patients</span>
              <strong>{data.total_users}</strong>
              <span className="admin-stat-footnote"><i /> {data.new_users_30d} joined in the last 30 days</span>
            </article>
            <article className="admin-stat-card">
              <span className="admin-stat-icon admin-stat-icon-blue"><Stethoscope aria-hidden="true" size={19} /></span>
              <span className="admin-stat-label">Doctors</span>
              <strong>{data.total_doctors}</strong>
              <span className="admin-stat-footnote">Available in your directory</span>
            </article>
            <article className="admin-stat-card">
              <span className="admin-stat-icon admin-stat-icon-purple"><CalendarDays aria-hidden="true" size={19} /></span>
              <span className="admin-stat-label">Appointments</span>
              <strong>{data.total_appointments}</strong>
              <span className="admin-stat-footnote">Across all booking statuses</span>
            </article>
            <article className="admin-stat-card">
              <span className="admin-stat-icon admin-stat-icon-amber"><Clock3 aria-hidden="true" size={19} /></span>
              <span className="admin-stat-label">Needs attention</span>
              <strong>{data.pending_appointments}</strong>
              <span className="admin-stat-footnote">Pending appointment requests</span>
            </article>
          </section>

          <section aria-label="Practice charts" className="admin-charts-grid">
            <StatusChart data={data} />
            <MonthlyActivityChart data={data} />
          </section>

          <section className="workspace-card admin-recent-card">
            <div className="workspace-card-heading">
              <div>
                <span className="admin-chart-eyebrow">Latest updates</span>
                <h2>Recent appointments</h2>
                <p>A quick look at the latest booking activity</p>
              </div>
              <Link className="admin-view-all" href="/admin/appointments">
                View all <ArrowUpRight aria-hidden="true" size={16} />
              </Link>
            </div>
            {data.recent_appointments.length === 0 ? (
              <div className="workspace-empty">No appointments found.</div>
            ) : (
              <div className="table-wrap">
                <table className="workspace-table admin-recent-table">
                  <thead><tr><th>Patient</th><th>Doctor</th><th>Date</th><th>Status</th></tr></thead>
                  <tbody>
                    {data.recent_appointments.map((appointment) => (
                      <tr key={appointment.appointment_id}>
                        <td>
                          <span className="admin-patient-cell">
                            <span aria-hidden="true" className="admin-patient-avatar">
                              {appointment.patient_name?.charAt(0) ?? "P"}
                            </span>
                            <span>{appointment.patient_name}</span>
                          </span>
                        </td>
                        <td><span className="admin-doctor-name">Dr. {appointment.doctor_name}</span><small>{appointment.specialization}</small></td>
                        <td>{formatDate(appointment.appointment_date)}</td>
                        <td><span className={`status-pill status-${appointment.status}`}>{appointment.status}</span></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
            {data.pending_appointments > 0 && (
              <Link className="admin-pending-note" href="/admin/appointments">
                <CheckCircle2 aria-hidden="true" size={16} />
                {data.pending_appointments} request{data.pending_appointments === 1 ? "" : "s"} waiting for review
                <ArrowUpRight aria-hidden="true" size={15} />
              </Link>
            )}
          </section>
        </>
      )}
    </WorkspaceFrame>
  );
}
