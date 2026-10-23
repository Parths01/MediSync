import type { Metadata } from "next";

import { SymptomChecker } from "@/components/workspaces/symptom-checker";

export const metadata: Metadata = {
  title: "Find a specialist",
  description: "Match your words to a MediSync doctor specialty.",
};

export default function SymptomsPage() {
  return <SymptomChecker />;
}
