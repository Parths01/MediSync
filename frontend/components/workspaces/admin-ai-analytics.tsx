"use client";

import { useEffect, useState } from "react";
import { BrainCircuit, Clock3, MessageCircle, ThumbsDown, ThumbsUp } from "lucide-react";
import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import { getAdminAIAnalytics, type AdminAIAnalytics } from "@/lib/api";

export function AdminAIAnalyticsPage() {
  const { user, loading: checkingUser, error: userError } = useProtectedUser("admin");
  const [data, setData] = useState<AdminAIAnalytics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getAdminAIAnalytics(controller.signal).then(setData).catch((reason: unknown) => {
      if (reason instanceof DOMException && reason.name === "AbortError") return;
      setError(reason instanceof Error ? reason.message : "Could not load AI analytics.");
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, []);

  if (checkingUser) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  return <WorkspaceFrame description="Aggregate assistant usage only. Patient prompts and identities are not shown here." role="admin" title="AI assistant analytics">
    {loading && <WorkspaceLoading message="Loading assistant metrics…" />}
    {error && <WorkspaceError message={error} />}
    {data && <>
      <section className="admin-stat-grid" aria-label="AI assistant metrics">
        <article className="admin-stat-card"><span className="admin-stat-icon admin-stat-icon-mint"><MessageCircle size={19} /></span><span className="admin-stat-label">Conversations</span><strong>{data.conversations}</strong><span className="admin-stat-footnote">Stored patient conversations</span></article>
        <article className="admin-stat-card"><span className="admin-stat-icon admin-stat-icon-blue"><BrainCircuit size={19} /></span><span className="admin-stat-label">Requests</span><strong>{data.requests}</strong><span className="admin-stat-footnote">{data.successful_requests} completed · {data.failed_requests} failed</span></article>
        <article className="admin-stat-card"><span className="admin-stat-icon admin-stat-icon-purple"><Clock3 size={19} /></span><span className="admin-stat-label">Average latency</span><strong>{data.average_latency_ms === null ? "—" : `${Math.round(data.average_latency_ms)} ms`}</strong><span className="admin-stat-footnote">Local rules response</span></article>
        <article className="admin-stat-card"><span className="admin-stat-icon admin-stat-icon-amber"><ThumbsUp size={19} /></span><span className="admin-stat-label">Helpful ratings</span><strong>{data.helpful_feedback}</strong><span className="admin-stat-footnote"><ThumbsDown aria-hidden="true" size={13} /> {data.not_helpful_feedback} not helpful</span></article>
      </section>
      <section className="workspace-card ai-analytics-note"><h2>Data and token reporting</h2><p>Usage metrics are aggregate. Message content and patient identifiers are not displayed.</p><p>{data.token_usage_available ? `Recorded tokens: ${data.input_tokens ?? 0} input · ${data.output_tokens ?? 0} output.` : "Token totals are unavailable because the local rules assistant does not use an LLM."}</p></section>
    </>}
  </WorkspaceFrame>;
}
