import type { Metadata } from "next";

import { PatientDashboard } from "@/components/workspaces/patient-dashboard";

export const metadata: Metadata = {
  title: "Patient dashboard",
  description: "Review your upcoming MediSync appointments.",
};

export default function DashboardPage() {
  return <PatientDashboard />;
}
