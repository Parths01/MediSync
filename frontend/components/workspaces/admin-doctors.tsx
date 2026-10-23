"use client";

import { useCallback, useEffect, useState, type FormEvent } from "react";
import Image from "next/image";

import { WorkspaceError, WorkspaceFrame, WorkspaceLoading, useProtectedUser } from "@/components/protected-workspace";
import {
  Doctor,
  createDoctor,
  deleteDoctor,
  getDoctorPhotoUrl,
  getDoctors,
  updateDoctor,
  uploadDoctorPhoto,
} from "@/lib/api";

type DoctorForm = Omit<Doctor, "doctor_id" | "photo" | "created_at">;

const emptyForm: DoctorForm = {
  name: "",
  specialization: "",
  experience: 0,
  contact_details: "",
};

export function AdminDoctors() {
  const { user, loading: checkingUser, error: userError } = useProtectedUser("admin");
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [form, setForm] = useState<DoctorForm>(emptyForm);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const refreshDoctors = useCallback(async (signal?: AbortSignal) => {
    const result = await getDoctors(signal);
    setDoctors(result);
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    refreshDoctors(controller.signal)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load doctors.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [refreshDoctors]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(null);
    try {
      const savedDoctor = editingId === null
        ? await createDoctor(form)
        : await updateDoctor(editingId, form);
      if (photoFile) {
        try {
          await uploadDoctorPhoto(savedDoctor.doctor_id, photoFile);
        } catch (reason) {
          setEditingId(savedDoctor.doctor_id);
          setForm({
            name: savedDoctor.name,
            specialization: savedDoctor.specialization,
            experience: savedDoctor.experience,
            contact_details: savedDoctor.contact_details,
          });
          const message = reason instanceof Error ? reason.message : "Could not upload the photo.";
          setError(`Doctor details were saved, but the photo was not: ${message}`);
          try {
            await refreshDoctors();
          } catch (refreshReason) {
            const refreshMessage = refreshReason instanceof Error
              ? refreshReason.message
              : "Could not refresh the directory.";
            setError((current) => `${current} ${refreshMessage}`);
          }
          return;
        }
      }
      setForm(emptyForm);
      setPhotoFile(null);
      setEditingId(null);
      setSuccess(editingId === null ? "Doctor added." : "Doctor updated.");
      try {
        await refreshDoctors();
      } catch (reason) {
        setSuccess(null);
        setError(`Doctor was saved, but the directory could not be refreshed: ${
          reason instanceof Error ? reason.message : "Unknown error"
        }`);
      }
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not save doctor details.");
    } finally {
      setSaving(false);
    }
  }

  async function handleDelete(doctor: Doctor) {
    if (!window.confirm(`Remove Dr. ${doctor.name} from the directory?`)) return;
    setError(null);
    setSuccess(null);
    try {
      await deleteDoctor(doctor.doctor_id);
      setDoctors((items) => items.filter((item) => item.doctor_id !== doctor.doctor_id));
      setSuccess("Doctor removed.");
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Could not remove this doctor.");
    }
  }

  if (checkingUser) return <WorkspaceLoading />;
  if (userError) return <WorkspaceError message={userError} />;
  if (!user) return <WorkspaceLoading message="Redirecting to sign in…" />;

  return (
    <WorkspaceFrame description="Maintain the public specialist directory." role="admin" title="Manage doctors">
      <section className="workspace-card form-card">
        <h2>{editingId === null ? "Add a doctor" : "Edit doctor"}</h2>
        {error && <WorkspaceError message={error} />}
        {success && <div className="form-alert form-alert-success" role="status">{success}</div>}
        <form className="stacked-form" onSubmit={handleSubmit}>
          <div className="form-grid">
            <label>
              Full name
              <input
                maxLength={255}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                required
                value={form.name}
              />
            </label>
            <label>
              Specialization
              <input
                maxLength={255}
                onChange={(event) => setForm({ ...form, specialization: event.target.value })}
                required
                value={form.specialization}
              />
            </label>
          </div>
          <label>
            Doctor photo <span className="field-optional">Optional; JPEG, PNG, or WebP, up to 5 MB</span>
            <input
              accept="image/jpeg,image/png,image/webp"
              onChange={(event) => setPhotoFile(event.target.files?.[0] ?? null)}
              type="file"
            />
          </label>
          <div className="form-grid">
            <label>
              Experience (years)
              <input
                max={100}
                min={0}
                onChange={(event) => setForm({ ...form, experience: Number(event.target.value) })}
                required
                type="number"
                value={form.experience}
              />
            </label>
            <label>
              Contact details
              <input
                maxLength={255}
                onChange={(event) => setForm({ ...form, contact_details: event.target.value })}
                required
                value={form.contact_details}
              />
            </label>
          </div>
          <div className="workspace-actions">
            <button className="button button-primary" disabled={saving} type="submit">
              {saving ? "Saving…" : editingId === null ? "Add doctor" : "Save changes"}
            </button>
            {editingId !== null && (
              <button
                className="button button-outline"
                onClick={() => {
                  setEditingId(null);
                  setForm(emptyForm);
                  setPhotoFile(null);
                }}
                type="button"
              >
                Cancel edit
              </button>
            )}
          </div>
        </form>
      </section>

      <section className="workspace-card">
        <div className="workspace-card-heading"><div><h2>Directory</h2><p>{doctors.length} listed</p></div></div>
        {loading && <p className="muted-copy">Loading doctors…</p>}
        {!loading && doctors.length === 0 && <div className="workspace-empty">No doctors have been added.</div>}
        <div className="table-wrap">
          <table className="workspace-table">
            <thead><tr><th>Photo</th><th>Name</th><th>Specialty</th><th>Experience</th><th>Contact</th><th>Actions</th></tr></thead>
            <tbody>
              {doctors.map((doctor) => {
                const photoUrl = getDoctorPhotoUrl(doctor.photo);
                return (
                  <tr key={doctor.doctor_id}>
                    <td>
                      {photoUrl && (
                        <Image
                          alt=""
                          className="admin-doctor-photo"
                          height={40}
                          src={photoUrl}
                          unoptimized
                          width={40}
                        />
                      )}
                    </td>
                    <td>Dr. {doctor.name}</td>
                    <td>{doctor.specialization}</td>
                    <td>{doctor.experience} years</td>
                    <td>{doctor.contact_details}</td>
                    <td>
                      <button
                        className="table-action"
                        onClick={() => {
                          setEditingId(doctor.doctor_id);
                          setPhotoFile(null);
                          setForm({
                            name: doctor.name,
                            specialization: doctor.specialization,
                            experience: doctor.experience,
                            contact_details: doctor.contact_details,
                          });
                        }}
                        type="button"
                      >
                        Edit
                      </button>
                      {" · "}
                      <button className="table-action" onClick={() => void handleDelete(doctor)} type="button">
                        Delete
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>
    </WorkspaceFrame>
  );
}
