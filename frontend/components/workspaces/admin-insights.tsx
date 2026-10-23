"use client";

import { useEffect, useState } from "react";

import {
  WorkspaceError,
  WorkspaceFrame,
  WorkspaceLoading,
  useProtectedUser,
} from "@/components/protected-workspace";
import { AdminInsights, getAdminInsights } from "@/lib/api";

function formatDate(value: string | null): string {
  if (!value) return "Date unavailable";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

export function AdminInsightsPage() {
  const { user, loading: checkingUser, error: userError } = useProtectedUser("admin");
  const [data, setData] = useState<AdminInsights | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getAdminInsights(controller.signal)
      .then(setData)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load the admin insights.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  if (checkingUser) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  return (
    <WorkspaceFrame
      description="Review routine appointment reminders and recent feedback themes."
      role="admin"
      title="Heuristic insights"
    >
      {error && <WorkspaceError message={error} />}
      {loading && <WorkspaceLoading message="Reviewing recent activity…" />}
      {data && (
        <>
          <p className="insights-disclaimer" role="note">{data.disclaimer}</p>
          <section className="stat-grid" aria-label="Appointment follow-up indicator counts">
            {(["High", "Medium", "Low"] as const).map((label) => (
              <div className="stat-tile" key={label}>
                <span>{label} follow-up indicator</span>
                <strong>
                  {data.follow_up_indicators.filter((item) => item.indicator_label === label).length}
                </strong>
              </div>
            ))}
          </section>
          <section className="stat-grid" aria-label="Feedback sentiment counts">
            <div className="stat-tile">
              <span>Feedback entries (total)</span><strong>{data.feedback_total}</strong>
            </div>
            <div className="stat-tile">
              <span>Positive in latest {data.feedback_analyzed}</span>
              <strong>{data.sentiment_counts.positive}</strong>
            </div>
            <div className="stat-tile">
              <span>Neutral in latest {data.feedback_analyzed}</span>
              <strong>{data.sentiment_counts.neutral}</strong>
            </div>
            <div className="stat-tile">
              <span>Negative in latest {data.feedback_analyzed}</span>
              <strong>{data.sentiment_counts.negative}</strong>
            </div>
          </section>

          <section className="workspace-card">
            <div className="workspace-card-heading">
              <div>
                <h2>Upcoming appointment follow-up</h2>
                <p>Up to 50 upcoming pending or confirmed appointments</p>
              </div>
            </div>
            {data.follow_up_indicators.length === 0 ? (
              <div className="workspace-empty">No upcoming appointments to review.</div>
            ) : (
              <div className="table-wrap">
                <table className="workspace-table">
                  <thead>
                    <tr>
                      <th>Patient</th><th>Doctor / Specialty</th><th>Date</th>
                      <th>Indicator</th><th>Factors</th><th>Reminder suggestion</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.follow_up_indicators.map(({ appointment, ...indicator }) => (
                      <tr key={appointment.appointment_id}>
                        <td>{appointment.patient_name}</td>
                        <td>Dr. {appointment.doctor_name}<br /><span className="insight-specialty">{appointment.specialization}</span></td>
                        <td>{formatDate(appointment.appointment_date)}</td>
                        <td>
                          <span className={`insight-label insight-label-${indicator.indicator_label.toLowerCase()}`}>
                            {indicator.indicator_label}
                          </span>
                          <span className="insight-score">
                            {Math.round(indicator.indicator_score * 100)}/100 heuristic points
                          </span>
                        </td>
                        <td>
                          <ul className="insight-factors">
                            {indicator.factors.map((factor) => <li key={factor}>{factor}</li>)}
                          </ul>
                        </td>
                        <td><strong className="insight-suggestion">{indicator.suggestion}</strong></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className="workspace-card">
            <div className="workspace-card-heading">
              <div>
                <h2>Negative feedback to review</h2>
                <p>Keyword classification from the latest {data.feedback_analyzed} entries; review the original message for context.</p>
              </div>
            </div>
            {data.negative_feedback.length === 0 ? (
              <div className="workspace-empty">No negative feedback was classified in the analyzed entries.</div>
            ) : (
              <div className="workspace-list">
                {data.negative_feedback.map((item) => (
                  <article className="workspace-list-item" key={item.feedback_id}>
                    <div>
                      <h3>{item.user_name}</h3>
                      <p>{formatDate(item.created_at)}</p>
                      <p>{item.message}</p>
                    </div>
                    <span className="insight-label insight-label-high">Review</span>
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
