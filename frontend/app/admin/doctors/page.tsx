import type { Metadata } from "next";

import { AdminDoctors } from "@/components/workspaces/admin-doctors";

export const metadata: Metadata = {
  title: "Manage doctors",
  description: "Maintain the MediSync doctor directory.",
};

export default function AdminDoctorsPage() {
  return <AdminDoctors />;
}
