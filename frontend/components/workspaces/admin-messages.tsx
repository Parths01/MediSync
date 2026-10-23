"use client";

import { useEffect, useState } from "react";

import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import {
  ContactReport,
  Feedback,
  getAdminFeedback,
  getAdminReports,
  updateReportStatus,
} from "@/lib/api";

function formatDate(value: string | null): string {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(
    new Date(value),
  );
}

export function AdminReports() {
  const { user, loading: checkingUser, error: userError } = useProtectedUser("admin");
  const [reports, setReports] = useState<ContactReport[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getAdminReports(controller.signal)
      .then(setReports)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load inquiries.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, []);

  async function toggleStatus(report: ContactReport) {
    setError(null);
    try {
      const updated = await updateReportStatus(
        report.contact_id,
        report.status === "open" ? "closed" : "open",
      );
      setReports((items) =>
        items.map((item) => (item.contact_id === report.contact_id ? updated : item)),
      );
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update inquiry.");
    }
  }

  if (checkingUser) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  return (
    <WorkspaceFrame description="Review patient inquiries and manage their open or closed state." role="admin" title="Patient inquiries">
      {error && <WorkspaceError message={error} />}
      <section className="workspace-card">
        {loading && <p className="muted-copy">Loading inquiries…</p>}
        {!loading && !error && reports.length === 0 && <div className="workspace-empty">No inquiries found.</div>}
        {reports.length > 0 && (
          <div className="table-wrap">
            <table className="workspace-table">
              <thead><tr><th>Patient</th><th>Message</th><th>Received</th><th>Status</th><th>Action</th></tr></thead>
              <tbody>
                {reports.map((report) => (
                  <tr key={report.contact_id}>
                    <td>{report.user_name}</td>
                    <td>{report.message}</td>
                    <td>{formatDate(report.created_at)}</td>
                    <td><span className={`status-pill status-${report.status}`}>{report.status}</span></td>
                    <td>
                      <button className="table-action" onClick={() => void toggleStatus(report)} type="button">
                        {report.status === "open" ? "Close" : "Reopen"}
                      </button>
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

export function AdminFeedback() {
  const { user, loading: checkingUser, error: userError } = useProtectedUser("admin");
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getAdminFeedback(controller.signal)
      .then(setFeedback)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load feedback.");
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
    <WorkspaceFrame description="Read feedback submitted by patients." role="admin" title="Patient feedback">
      {error && <WorkspaceError message={error} />}
      <section className="workspace-card">
        {loading && <p className="muted-copy">Loading feedback…</p>}
        {!loading && !error && feedback.length === 0 && <div className="workspace-empty">No feedback received yet.</div>}
        <div className="workspace-list">
          {feedback.map((item) => (
            <article className="workspace-list-item" key={item.feedback_id}>
              <div><h3>{item.user_name}</h3><p>{formatDate(item.created_at)}</p><p>{item.message}</p></div>
            </article>
          ))}
        </div>
      </section>
    </WorkspaceFrame>
  );
}
