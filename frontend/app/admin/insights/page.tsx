import type { Metadata } from "next";

import { AdminInsightsPage } from "@/components/workspaces/admin-insights";

export const metadata: Metadata = {
  title: "Heuristic insights",
  description: "Review appointment follow-up indicators and patient feedback themes.",
};

export default function AdminInsightsRoute() {
  return <AdminInsightsPage />;
}
