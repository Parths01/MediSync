import type { Metadata } from "next";

import { AppointmentBooking } from "@/components/workspaces/appointment-booking";

export const metadata: Metadata = {
  title: "Book an appointment",
  description: "Request an appointment with a MediSync doctor.",
};

export default async function AppointmentPage({
  searchParams,
}: {
  searchParams: Promise<{ doctor_id?: string }>;
}) {
  const params = await searchParams;
  const parsedId = Number(params.doctor_id);
  const initialDoctorId = Number.isInteger(parsedId) && parsedId > 0 ? parsedId : null;
  return <AppointmentBooking initialDoctorId={initialDoctorId} />;
}
