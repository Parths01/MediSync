import type { Metadata } from "next";
import Link from "next/link";
import { ArrowRight, HeartPulse, Search } from "lucide-react";

import { DoctorDirectory } from "@/components/doctor-directory";

export const metadata: Metadata = {
  title: "Find a doctor",
  description: "Explore MediSync's doctor directory by name or specialty.",
};

export default function DoctorsPage() {
  return (
    <>
      <section className="directory-hero">
        <div className="page-width">
          <div className="breadcrumb"><Link href="/">Home</Link><span>/</span><span>Find a doctor</span></div>
          <div className="directory-hero-content">
            <div>
              <span className="section-kicker">YOUR CARE TEAM</span>
              <h1>Find a doctor who <em>gets you.</em></h1>
              <p>Explore our specialists and request an appointment that works for you.</p>
            </div>
            <div className="directory-hero-stamp"><HeartPulse size={29} /><span>Care starts<br />with connection</span></div>
          </div>
          <div className="directory-prompt"><Search size={17} /><span>Search by doctor name or specialty, then request a visit with your chosen specialist.</span><ArrowRight size={16} /></div>
        </div>
      </section>
      <section className="directory-page section-space">
        <div className="page-width">
          <div className="directory-page-heading">
            <div><h2>Our specialists</h2><p>Find the right expertise for your next step.</p></div>
          </div>
          <DoctorDirectory />
          <aside className="directory-disclaimer">
            <HeartPulse size={18} />
            <p><strong>Need urgent medical care?</strong> This directory is not an emergency service. Contact your local emergency number for immediate assistance.</p>
          </aside>
        </div>
      </section>
    </>
  );
}
