import type { Metadata } from "next";

import { PatientContact } from "@/components/workspaces/patient-contact";

export const metadata: Metadata = {
  title: "Contact and feedback",
  description: "Send MediSync a message or share feedback.",
};

export default function ContactPage() {
  return <PatientContact />;
}
