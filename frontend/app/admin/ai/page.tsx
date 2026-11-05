import type { Metadata } from "next";
import { AdminAIAnalyticsPage } from "@/components/workspaces/admin-ai-analytics";

export const metadata: Metadata = { title: "AI analytics", description: "Privacy-safe MediSync assistant usage metrics." };

export default function AdminAIPage() { return <AdminAIAnalyticsPage />; }
