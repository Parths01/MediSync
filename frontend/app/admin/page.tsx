import type { Metadata } from "next";

import { AdminDashboardPage } from "@/components/workspaces/admin-dashboard";

export const metadata: Metadata = {
  title: "Admin dashboard",
  description: "MediSync administrator overview.",
};

export default function AdminPage() {
  return <AdminDashboardPage />;
}
