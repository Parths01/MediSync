"use client";

import { FormEvent, useState } from "react";

import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import { sendContactMessage, submitFeedback } from "@/lib/api";

export function PatientContact() {
  const { user, loading, error: userError } = useProtectedUser("patient");
  const [contactError, setContactError] = useState<string | null>(null);
  const [contactSuccess, setContactSuccess] = useState<string | null>(null);
  const [feedbackError, setFeedbackError] = useState<string | null>(null);
  const [feedbackSuccess, setFeedbackSuccess] = useState<string | null>(null);
  const [sendingContact, setSendingContact] = useState(false);
  const [sendingFeedback, setSendingFeedback] = useState(false);

  async function handleContact(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const message = String(new FormData(formElement).get("contact_message") ?? "");
    setContactError(null);
    setContactSuccess(null);
    setSendingContact(true);
    try {
      await sendContactMessage(message);
      formElement.reset();
      setContactSuccess("Your inquiry was sent.");
    } catch (reason) {
      setContactError(reason instanceof Error ? reason.message : "Could not send your inquiry.");
    } finally {
      setSendingContact(false);
    }
  }

  async function handleFeedback(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formElement = event.currentTarget;
    const message = String(new FormData(formElement).get("feedback_message") ?? "");
    setFeedbackError(null);
    setFeedbackSuccess(null);
    setSendingFeedback(true);
    try {
      await submitFeedback(message);
      formElement.reset();
      setFeedbackSuccess("Thank you for sharing your feedback.");
    } catch (reason) {
      setFeedbackError(reason instanceof Error ? reason.message : "Could not submit feedback.");
    } finally {
      setSendingFeedback(false);
    }
  }

  if (loading) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  return (
    <WorkspaceFrame
      description="Contact the MediSync team or share feedback about your experience."
      role="patient"
      title="Contact and feedback"
    >
      <section className="workspace-card form-card">
        <h2>Send an inquiry</h2>
        <p className="muted-copy">For emergencies, contact your local emergency services.</p>
        {contactError && <WorkspaceError message={contactError} />}
        {contactSuccess && <div className="form-alert form-alert-success" role="status">{contactSuccess}</div>}
        <form className="stacked-form" onSubmit={handleContact}>
          <label>
            Your message
            <textarea maxLength={10000} minLength={10} name="contact_message" required rows={5} />
          </label>
          <button className="button button-primary form-submit" disabled={sendingContact} type="submit">
            {sendingContact ? "Sending…" : "Send inquiry"}
          </button>
        </form>
      </section>

      <section className="workspace-card form-card">
        <h2>Share feedback</h2>
        {feedbackError && <WorkspaceError message={feedbackError} />}
        {feedbackSuccess && <div className="form-alert form-alert-success" role="status">{feedbackSuccess}</div>}
        <form className="stacked-form" onSubmit={handleFeedback}>
          <label>
            Feedback
            <textarea maxLength={10000} name="feedback_message" required rows={5} />
          </label>
          <button className="button button-primary form-submit" disabled={sendingFeedback} type="submit">
            {sendingFeedback ? "Sending…" : "Submit feedback"}
          </button>
        </form>
      </section>
    </WorkspaceFrame>
  );
}
