import type { Metadata } from "next";
import { AIAssistant } from "@/components/workspaces/ai-assistant";

export const metadata: Metadata = { title: "AI health assistant", description: "General health information and help finding a doctor." };

export default function AIAssistantPage() { return <AIAssistant />; }
