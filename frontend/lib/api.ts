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

export interface AdminAIAnalytics {
  conversations: number;
  requests: number;
  successful_requests: number;
  failed_requests: number;
  average_latency_ms: number | null;
  input_tokens: number | null;
  output_tokens: number | null;
  helpful_feedback: number;
  not_helpful_feedback: number;
  token_usage_available: boolean;
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

export interface AIMessage { message_id: number; role: "user" | "assistant"; content: string; created_at: string; }
export interface AIConversation { conversation_id: number; title: string; updated_at: string; messages: AIMessage[]; }
export interface AICitation { title: string; url: string; checked_at: string; }
export interface AIChatMetadata { conversation_id: number; message_id: number; citations: AICitation[]; emergency: boolean; doctors: Pick<Doctor, "doctor_id" | "name" | "specialization" | "experience">[]; delivery_mode: "buffered"; }

export function getAIConversations(signal?: AbortSignal): Promise<AIConversation[]> {
  return apiRequest<AIConversation[]>("/ai/conversations", { signal });
}
export function getAIConversation(id: number, signal?: AbortSignal): Promise<AIConversation> {
  return apiRequest<AIConversation>(`/ai/conversations/${id}`, { signal });
}
export function deleteAIConversation(id: number): Promise<void> {
  return apiRequest<void>(`/ai/conversations/${id}`, { method: "DELETE" });
}
export function deleteAllAIConversations(): Promise<void> {
  return apiRequest<void>("/ai/conversations", { method: "DELETE" });
}
export function submitAIFeedback(messageId: number, rating: "helpful" | "not_helpful"): Promise<{ status: string }> {
  return apiRequest<{ status: string }>(`/ai/messages/${messageId}/feedback`, {
    method: "POST", body: JSON.stringify({ rating }),
  });
}
export async function streamAIChat(
  message: string,
  conversationId: number | null,
  onContent: (text: string) => void,
  signal?: AbortSignal,
): Promise<AIChatMetadata> {
  const headers = new Headers({ Accept: "text/event-stream", "Content-Type": "application/json" });
  headers.set("X-CSRF-Token", await getCsrfToken());
  const response = await fetch(`${apiBaseUrl}/api/v1/ai/chat/stream`, {
    method: "POST", headers, credentials: "include", signal,
    body: JSON.stringify({ message, conversation_id: conversationId }),
  });
  if (!response.ok || !response.body) {
    let detail = `MediSync request failed (API returned ${response.status}).`;
    try { const body: unknown = await response.json(); if (typeof body === "object" && body !== null && "detail" in body && typeof body.detail === "string") detail = body.detail; } catch { /* keep fallback */ }
    throw new Error(detail);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let metadata: AIChatMetadata | null = null;
  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const event of events) {
      const line = event.split("\n").find((part) => part.startsWith("data: "));
      if (!line) continue;
      const data: unknown = JSON.parse(line.slice(6));
      if (typeof data === "object" && data !== null && "type" in data && (data.type === "response" || data.type === "delta") && "text" in data && typeof data.text === "string") onContent(data.text);
      if (typeof data === "object" && data !== null && "type" in data && data.type === "error" && "detail" in data && typeof data.detail === "string") throw new Error(data.detail);
      if (typeof data === "object" && data !== null && "type" in data && data.type === "metadata") metadata = data as unknown as AIChatMetadata;
    }
    if (done) break;
  }
  if (!metadata) throw new Error("The assistant response ended unexpectedly.");
  return metadata;
}

interface AuthResult {
  user: User;
  csrf_token: string;
}

const apiBaseUrl = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000").replace(
  /\/+$/,
  "",
);
export const API_PAGE_SIZE = 50;

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

export function getMyAppointments(
  signal?: AbortSignal,
  limit = API_PAGE_SIZE,
  offset = 0,
): Promise<Appointment[]> {
  return apiRequest<Appointment[]>(`/patient/appointments?limit=${limit}&offset=${offset}`, { signal });
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

export function getMedicalHistory(
  signal?: AbortSignal,
  limit = API_PAGE_SIZE,
  offset = 0,
): Promise<MedicalHistory[]> {
  return apiRequest<MedicalHistory[]>(`/patient/history?limit=${limit}&offset=${offset}`, { signal });
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

export function getAdminAIAnalytics(signal?: AbortSignal): Promise<AdminAIAnalytics> {
  return apiRequest<AdminAIAnalytics>("/admin/ai-analytics", { signal });
}

export function getAdminAppointments(
  signal?: AbortSignal,
  limit = API_PAGE_SIZE,
  offset = 0,
): Promise<Appointment[]> {
  return apiRequest<Appointment[]>(`/admin/appointments?limit=${limit}&offset=${offset}`, { signal });
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

export function getAdminReports(
  signal?: AbortSignal,
  limit = API_PAGE_SIZE,
  offset = 0,
): Promise<ContactReport[]> {
  return apiRequest<ContactReport[]>(`/admin/reports?limit=${limit}&offset=${offset}`, { signal });
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

export function getAdminFeedback(
  signal?: AbortSignal,
  limit = API_PAGE_SIZE,
  offset = 0,
): Promise<Feedback[]> {
  return apiRequest<Feedback[]>(`/admin/feedback?limit=${limit}&offset=${offset}`, { signal });
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
