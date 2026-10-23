import type { Metadata } from "next";

import { AdminFeedback } from "@/components/workspaces/admin-messages";

export const metadata: Metadata = {
  title: "Patient feedback",
  description: "Read patient feedback submitted to MediSync.",
};

export default function AdminFeedbackPage() {
  return <AdminFeedback />;
}
