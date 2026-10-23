import type { Metadata } from "next";

import { PatientHistory } from "@/components/workspaces/patient-history";

export const metadata: Metadata = {
  title: "Health history",
  description: "Review and maintain your private health history.",
};

export default function HistoryPage() {
  return <PatientHistory />;
}
