"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { MessageSquarePlus, Send, Trash2, Sparkles, ExternalLink, ThumbsDown, ThumbsUp } from "lucide-react";
import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import { deleteAIConversation, deleteAllAIConversations, getAIConversation, getAIConversations, streamAIChat, submitAIFeedback, type AIChatMetadata, type AIConversation, type AICitation, type Doctor } from "@/lib/api";

type Message = { id?: number; role: "user" | "assistant"; content: string };
const suggestions = ["Help me prepare for a doctor's visit", "Explain what a specialist does", "I have a persistent headache", "How can I find a doctor?"];

export function AIAssistant() {
  const { user, loading, error: userError } = useProtectedUser("patient");
  const [history, setHistory] = useState<AIConversation[]>([]);
  const [conversationId, setConversationId] = useState<number | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [citations, setCitations] = useState<AICitation[]>([]);
  const [doctors, setDoctors] = useState<AIChatMetadata["doctors"]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [feedbackSent, setFeedbackSent] = useState<Set<number>>(new Set());
  const [error, setError] = useState<string | null>(null);

  const refreshHistory = useCallback(async () => {
    try { setHistory(await getAIConversations()); } catch { /* chat remains usable */ }
  }, []);
  useEffect(() => { if (user) void refreshHistory(); }, [user, refreshHistory]);

  async function openConversation(id: number) {
    setError(null);
    try {
      const conversation = await getAIConversation(id);
      setConversationId(id);
      setMessages(conversation.messages.map(({ message_id, role, content }) => ({ id: message_id, role, content })));
      setCitations([]); setDoctors([]);
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not load this conversation."); }
  }

  async function sendMessage(raw: string) {
    const text = raw.trim();
    if (!text || busy) return;
    setInput(""); setError(null); setCitations([]); setDoctors([]); setBusy(true);
    setMessages((current) => [...current, { role: "user", content: text }, { role: "assistant", content: "" }]);
    try {
      const result = await streamAIChat(text, conversationId, (delta) => {
        setMessages((current) => current.map((message, index) => index === current.length - 1 ? { ...message, content: message.content + delta } : message));
      });
      setMessages((current) => current.map((message, index) => index === current.length - 1 ? { ...message, id: result.message_id } : message));
      setConversationId(result.conversation_id); setCitations(result.citations); setDoctors(result.doctors);
      await refreshHistory();
    } catch (reason) {
      setMessages((current) => current.slice(0, -1));
      setError(reason instanceof Error ? reason.message : "Could not reach the assistant.");
    } finally { setBusy(false); }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); await sendMessage(input);
  }
  async function removeConversation(id: number) {
    try { await deleteAIConversation(id); setHistory((current) => current.filter((item) => item.conversation_id !== id)); if (id === conversationId) startNew(); }
    catch (reason) { setError(reason instanceof Error ? reason.message : "Could not delete conversation."); }
  }
  async function removeAllConversations() {
    if (!window.confirm("Delete all of your AI conversations and their feedback? This cannot be undone.")) return;
    try {
      await deleteAllAIConversations();
      setHistory([]);
      startNew();
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not delete conversations."); }
  }
  function startNew() { setConversationId(null); setMessages([]); setCitations([]); setDoctors([]); setError(null); }

  if (loading) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  return <WorkspaceFrame description="General health information and help finding care." role="patient" title="AI health assistant">
    <div className="ai-layout">
      <aside className="workspace-card ai-sidebar" aria-label="Chat history">
        <button className="button button-primary ai-new" onClick={startNew} type="button"><MessageSquarePlus size={17} /> New chat</button>
        <h2>Recent chats</h2>
        {history.length > 0 && <button className="button button-secondary" onClick={() => void removeAllConversations()} type="button">Delete all chats</button>}
        {history.length === 0 ? <p className="ai-history-empty">Your conversations will appear here.</p> : history.map((item) => <div className={`ai-history-row${conversationId === item.conversation_id ? " active" : ""}`} key={item.conversation_id}>
          <button onClick={() => void openConversation(item.conversation_id)} type="button">{item.title}</button>
          <button aria-label="Delete conversation" onClick={() => void removeConversation(item.conversation_id)} type="button"><Trash2 size={15} /></button>
        </div>)}
      </aside>
      <section className="workspace-card ai-chat" aria-label="Assistant conversation">
        <div className="ai-safety"><Sparkles size={17} /> General information only. This assistant cannot diagnose or prescribe. For emergencies, contact local emergency services.</div>
        <div className="ai-transcript" aria-live="polite">
          {messages.length === 0 ? <div className="ai-welcome"><span className="ai-mark"><Sparkles /></span><h2>How can I help today?</h2><p>Ask a general health question or get help finding a doctor.</p><div className="ai-suggestions">{suggestions.map((suggestion) => <button key={suggestion} onClick={() => void sendMessage(suggestion)} type="button">{suggestion}</button>)}</div></div> : messages.map((message, index) => <article className={`ai-message ${message.role}`} key={`${message.id ?? index}-${message.role}`}><span>{message.role === "user" ? "You" : "MediSync assistant"}</span><p>{message.content || (busy ? "Preparing a response…" : "")}</p>{message.role === "assistant" && message.id && <div className="ai-feedback" aria-label="Rate this answer"><span>Was this helpful?</span><button disabled={feedbackSent.has(message.id)} onClick={async () => { try { await submitAIFeedback(message.id!, "helpful"); setFeedbackSent((current) => new Set(current).add(message.id!)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save feedback."); } }} title="Helpful" type="button"><ThumbsUp size={15} /></button><button disabled={feedbackSent.has(message.id)} onClick={async () => { try { await submitAIFeedback(message.id!, "not_helpful"); setFeedbackSent((current) => new Set(current).add(message.id!)); } catch (reason) { setError(reason instanceof Error ? reason.message : "Could not save feedback."); } }} title="Not helpful" type="button"><ThumbsDown size={15} /></button>{feedbackSent.has(message.id) && <span>Thanks</span>}</div>}</article>)}
        </div>
        {error && <WorkspaceError message={error} />}
        {citations.length > 0 && <div className="ai-citations"><strong>Health references</strong>{citations.map((citation) => <a href={citation.url} key={citation.url} rel="noreferrer" target="_blank">{citation.title} <ExternalLink size={13} /><small>{citation.checked_at}</small></a>)}</div>}
        {doctors.length > 0 && <div className="ai-doctors"><strong>Doctors in the directory</strong>{doctors.map((doctor: Pick<Doctor, "doctor_id" | "name" | "specialization" | "experience">) => <article key={doctor.doctor_id}><div><b>Dr. {doctor.name}</b><small>{doctor.specialization} · {doctor.experience} years</small></div><Link href={`/appointments/new?doctor_id=${doctor.doctor_id}`}>Request a visit</Link></article>)}</div>}
        <form className="ai-composer" onSubmit={handleSubmit}><label className="sr-only" htmlFor="ai-message">Your message</label><textarea id="ai-message" maxLength={4000} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void sendMessage(input); } }} placeholder="Ask a health question…" value={input} /><button aria-label="Send message" className="button button-primary" disabled={busy || !input.trim()} type="submit"><Send size={17} /></button></form>
        <p className="ai-privacy">Responses are buffered by the local assistant. Conversations expire automatically under MediSync’s configured retention policy. You can delete chats at any time. Avoid sharing details you do not need to discuss.</p>
      </section>
    </div>
  </WorkspaceFrame>;
}
