import type { Metadata } from "next";

import { PatientProfile } from "@/components/workspaces/patient-profile";

export const metadata: Metadata = {
  title: "My profile",
  description: "Manage your MediSync account details.",
};

export default function ProfilePage() {
  return <PatientProfile />;
}
