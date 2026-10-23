"use client";

import { FormEvent, useState } from "react";

import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import { User, updateProfile } from "@/lib/api";

export function PatientProfile() {
  const { user, loading, error: userError } = useProtectedUser("patient");
  const [updatedUser, setUpdatedUser] = useState<User | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);
    const formElement = event.currentTarget;
    const form = new FormData(formElement);
    const currentPassword = String(form.get("current_password") ?? "");
    const newPassword = String(form.get("new_password") ?? "");
    try {
      const result = await updateProfile({
        name: String(form.get("name") ?? ""),
        dob: String(form.get("dob") ?? ""),
        gender: getGender(form.get("gender")),
        contact: String(form.get("contact") ?? ""),
        blood_group: String(form.get("blood_group") ?? "") || null,
        ...(currentPassword || newPassword
          ? { current_password: currentPassword, new_password: newPassword }
          : {}),
      });
      setUpdatedUser(result);
      setSuccess("Profile updated.");
      const currentPasswordInput = formElement.elements.namedItem("current_password");
      const newPasswordInput = formElement.elements.namedItem("new_password");
      if (currentPasswordInput instanceof HTMLInputElement) currentPasswordInput.value = "";
      if (newPasswordInput instanceof HTMLInputElement) newPasswordInput.value = "";
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not update your profile.");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  const profile = updatedUser ?? user;

  return (
    <WorkspaceFrame description="Update the personal details associated with your account." role="patient" title="My profile">
      <section className="workspace-card form-card">
        {error && <WorkspaceError message={error} />}
        {success && <div className="form-alert form-alert-success" role="status">{success}</div>}
        <form className="stacked-form" onSubmit={handleSubmit}>
          <label>
            Full name
            <input defaultValue={profile.name} key={`name-${profile.name}`} maxLength={255} name="name" required />
          </label>
          <label>
            Email
            <input disabled value={profile.email} />
            <span className="field-help">Email address changes are not currently supported.</span>
          </label>
          <div className="form-grid">
            <label>
              Date of birth
              <input defaultValue={profile.dob} key={`dob-${profile.dob}`} max={new Date().toISOString().slice(0, 10)} name="dob" required type="date" />
            </label>
            <label>
              Gender
              <select defaultValue={profile.gender} key={`gender-${profile.gender}`} name="gender" required>
                <option>Female</option><option>Male</option><option>Other</option>
              </select>
            </label>
          </div>
          <div className="form-grid">
            <label>
              Contact number
              <input defaultValue={profile.contact} key={`contact-${profile.contact}`} maxLength={15} name="contact" required />
            </label>
            <label>
              Blood group
              <select defaultValue={profile.blood_group ?? ""} key={`blood-${profile.blood_group}`} name="blood_group">
                <option value="">Prefer not to say</option>
                {["A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"].map((group) => (
                  <option key={group}>{group}</option>
                ))}
              </select>
            </label>
          </div>
          <h2 className="form-subheading">Change password (optional)</h2>
          <div className="form-grid">
            <label>
              Current password
              <input autoComplete="current-password" maxLength={128} name="current_password" type="password" />
            </label>
            <label>
              New password
              <input autoComplete="new-password" maxLength={128} minLength={8} name="new_password" type="password" />
            </label>
          </div>
          <button className="button button-primary form-submit" disabled={saving} type="submit">
            {saving ? "Saving…" : "Save profile"}
          </button>
        </form>
      </section>
    </WorkspaceFrame>
  );
}

function getGender(value: FormDataEntryValue | null): "Male" | "Female" | "Other" {
  return value === "Male" || value === "Female" || value === "Other" ? value : "Other";
}
