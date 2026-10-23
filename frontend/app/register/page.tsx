import type { Metadata } from "next";

import { AuthForm } from "@/components/auth-form";

export const metadata: Metadata = {
  title: "Create an account",
  description: "Create a MediSync patient account.",
};

export default function RegisterPage() {
  return <AuthForm mode="register" />;
}
