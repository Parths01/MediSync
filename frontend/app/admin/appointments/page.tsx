import type { Metadata } from "next";

import { AdminAppointments } from "@/components/workspaces/admin-appointments";

export const metadata: Metadata = {
  title: "Manage appointments",
  description: "Review and update patient appointment requests.",
};

export default function AdminAppointmentsPage() {
  return <AdminAppointments />;
}
