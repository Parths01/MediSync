import type { Metadata } from "next";

import { AdminReports } from "@/components/workspaces/admin-messages";

export const metadata: Metadata = {
  title: "Patient inquiries",
  description: "Review messages sent to MediSync.",
};

export default function AdminReportsPage() {
  return <AdminReports />;
}
