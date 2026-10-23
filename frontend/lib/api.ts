export interface Doctor {
  doctor_id: number;
  name: string;
  specialization: string;
  experience: number;
  contact_details: string;
  photo: string | null;
  created_at: string | null;
}

export interface User {
  user_id: number;
  name: string;
  dob: string;
  gender: "Male" | "Female" | "Other";
  contact: string;
  email: string;
  blood_group: string | null;
  role: "patient" | "admin";
  registration_date: string | null;
}

export type AppointmentStatus =
  | "pending"
  | "confirmed"
  | "completed"
  | "rejected"
  | "cancelled";

export interface Appointment {
  appointment_id: number;
  user_id: number;
  doctor_id: number;
  appointment_date: string;
  description: string | null;
  status: AppointmentStatus;
  assigned_by: "user" | "admin";
  created_at: string | null;
  doctor_name: string;
  specialization: string;
  doctor_contact: string;
  patient_name: string | null;
}

export interface MedicalHistory {
  history_id: number;
  diagnosis: string;
  treatment: string | null;
  notes: string | null;
  recorded_at: string;
  created_at: string | null;
}

export interface ContactReport {
  contact_id: number;
  message: string;
  status: "open" | "closed";
  created_at: string | null;
  user_name: string;
}

export interface Feedback {
  feedback_id: number;
  message: string;
  created_at: string | null;
  user_name: string;
}

export interface AdminDashboard {
  total_users: number;
  total_doctors: number;
  total_appointments: number;
  new_users_30d: number;
  pending_appointments: number;
  appointment_status_counts: Record<AppointmentStatus, number>;
  monthly_appointments: MonthlyCount[];
  monthly_registrations: MonthlyCount[];
  recent_appointments: Appointment[];
}

export interface MonthlyCount {
  month: string;
  count: number;
}

export interface AppointmentIndicator {
  appointment: Appointment;
  indicator_score: number;
  indicator_label: string;
  factors: string[];
  suggestion: string;
}

export interface FeedbackInsight {
  feedback_id: number;
  message: string;
  created_at: string | null;
  user_name: string;
  sentiment: string;
}

export interface AdminInsights {
  follow_up_indicators: AppointmentIndicator[];
  feedback_total: number;
  feedback_analyzed: number;
  sentiment_counts: Record<"positive" | "neutral" | "negative", number>;
  negative_feedback: FeedbackInsight[];
  disclaimer: string;
}

export interface SymptomRecommendation {
  specialty: string;
  score: number;
}

export interface SymptomResult {
  recommendations: SymptomRecommendation[];
  doctors: Doctor[];
  disclaimer: string;
}

interface AuthResult {
  user: User;
  csrf_token: string;
}

const apiBaseUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);

export function getDoctorPhotoUrl(photo: string | null): string | null {
  if (!photo) return null;
  if (/^https?:\/\//i.test(photo)) return photo;
  const filename = photo.split("/").pop();
  if (!filename || !/^doctor_[a-f0-9]{8,32}\.(jpg|png|webp)$/i.test(filename)) return null;
  return `${apiBaseUrl}/api/v1/doctors/photos/${encodeURIComponent(filename)}`;
}

function readCsrfCookie(): string | null {
  if (typeof document === "undefined") return null;
  const cookie = document.cookie
    .split("; ")
    .find((part) => part.startsWith("medisync_csrf="));
  return cookie ? decodeURIComponent(cookie.slice("medisync_csrf=".length)) : null;
}

async function getCsrfToken(): Promise<string> {
  const existingToken = readCsrfCookie();
  if (existingToken) return existingToken;

  const response = await fetch(`${apiBaseUrl}/api/v1/auth/csrf`, {
    headers: { Accept: "application/json" },
    credentials: "include",
  });
  if (!response.ok) {
    throw new Error(`Could not initialize secure session (API returned ${response.status}).`);
  }
  const result: unknown = await response.json();
  if (
    typeof result !== "object" ||
    result === null ||
    !("csrf_token" in result) ||
    typeof result.csrf_token !== "string"
  ) {
    throw new Error("The CSRF token response from the API was invalid.");
  }
  return result.csrf_token;
}

async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body !== undefined && !(init.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!["GET", "HEAD", "OPTIONS"].includes(method)) {
    headers.set("X-CSRF-Token", await getCsrfToken());
  }

  let response: Response;
  try {
    response = await fetch(`${apiBaseUrl}/api/v1${path}`, {
      ...init,
      method,
      headers,
      credentials: "include",
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new Error("Could not reach the MediSync API. Check that the backend is running.", {
      cause: error,
    });
  }

  if (response.status === 204) return undefined as T;

  let payload: unknown;
  try {
    payload = await response.json();
  } catch (error) {
    throw new Error("The MediSync API returned an invalid response.", { cause: error });
  }
  if (!response.ok) {
    const detail =
      typeof payload === "object" && payload !== null && "detail" in payload
        ? payload.detail
        : undefined;
    throw new Error(
      typeof detail === "string"
        ? detail
        : `MediSync request failed (API returned ${response.status}).`,
    );
  }
  return payload as T;
}

export function getDoctors(signal?: AbortSignal): Promise<Doctor[]> {
  return apiRequest<Doctor[]>("/doctors", { signal });
}

export function register(payload: {
  name: string;
  dob: string;
  gender: User["gender"];
  contact: string;
  email: string;
  password: string;
  blood_group: string | null;
}): Promise<AuthResult> {
  return apiRequest<AuthResult>("/auth/register", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function login(email: string, password: string): Promise<AuthResult> {
  return apiRequest<AuthResult>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function logout(): Promise<void> {
  return apiRequest<void>("/auth/logout", { method: "POST" });
}

export function getCurrentUser(signal?: AbortSignal): Promise<User> {
  return apiRequest<User>("/auth/me", { signal });
}

export function getMyAppointments(signal?: AbortSignal): Promise<Appointment[]> {
  return apiRequest<Appointment[]>("/patient/appointments", { signal });
}

export function bookAppointment(payload: {
  doctor_id: number;
  appointment_date: string;
  description: string;
}): Promise<Appointment> {
  return apiRequest<Appointment>("/patient/appointments", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function cancelAppointment(appointmentId: number): Promise<Appointment> {
  return apiRequest<Appointment>(`/patient/appointments/${appointmentId}/cancel`, {
    method: "POST",
  });
}

export function updateProfile(payload: {
  name: string;
  dob: string;
  gender: User["gender"];
  contact: string;
  blood_group: string | null;
  current_password?: string;
  new_password?: string;
}): Promise<User> {
  return apiRequest<User>("/patient/profile", {
    method: "PATCH",
    body: JSON.stringify(payload),
  });
}

export function getMedicalHistory(signal?: AbortSignal): Promise<MedicalHistory[]> {
  return apiRequest<MedicalHistory[]>("/patient/history", { signal });
}

export function addMedicalHistory(payload: {
  diagnosis: string;
  treatment: string;
  notes: string;
  recorded_at: string;
}): Promise<MedicalHistory> {
  return apiRequest<MedicalHistory>("/patient/history", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function sendContactMessage(message: string): Promise<{ status: string }> {
  return apiRequest<{ status: string }>("/patient/contact", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function submitFeedback(message: string): Promise<{ status: string }> {
  return apiRequest<{ status: string }>("/patient/feedback", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export function getSymptomRecommendations(symptoms: string): Promise<SymptomResult> {
  return apiRequest<SymptomResult>("/patient/symptom-check", {
    method: "POST",
    body: JSON.stringify({ symptoms }),
  });
}

export function getAdminDashboard(signal?: AbortSignal): Promise<AdminDashboard> {
  return apiRequest<AdminDashboard>("/admin/dashboard", { signal });
}

export function getAdminInsights(signal?: AbortSignal): Promise<AdminInsights> {
  return apiRequest<AdminInsights>("/admin/insights", { signal });
}

export function getAdminAppointments(signal?: AbortSignal): Promise<Appointment[]> {
  return apiRequest<Appointment[]>("/admin/appointments", { signal });
}

export function updateAppointmentStatus(
  appointmentId: number,
  status: AppointmentStatus,
): Promise<Appointment> {
  return apiRequest<Appointment>(`/admin/appointments/${appointmentId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function getAdminReports(signal?: AbortSignal): Promise<ContactReport[]> {
  return apiRequest<ContactReport[]>("/admin/reports", { signal });
}

export function updateReportStatus(
  contactId: number,
  status: ContactReport["status"],
): Promise<ContactReport> {
  return apiRequest<ContactReport>(`/admin/reports/${contactId}`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function getAdminFeedback(signal?: AbortSignal): Promise<Feedback[]> {
  return apiRequest<Feedback[]>("/admin/feedback", { signal });
}

export function createDoctor(payload: Omit<Doctor, "doctor_id" | "photo" | "created_at">): Promise<Doctor> {
  return apiRequest<Doctor>("/doctors", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateDoctor(
  doctorId: number,
  payload: Omit<Doctor, "doctor_id" | "photo" | "created_at">,
): Promise<Doctor> {
  return apiRequest<Doctor>(`/doctors/${doctorId}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export function uploadDoctorPhoto(doctorId: number, image: File): Promise<Doctor> {
  const formData = new FormData();
  formData.set("image", image);
  return apiRequest<Doctor>(`/doctors/${doctorId}/photo`, {
    method: "POST",
    body: formData,
  });
}

export function deleteDoctor(doctorId: number): Promise<void> {
  return apiRequest<void>(`/doctors/${doctorId}`, { method: "DELETE" });
}
