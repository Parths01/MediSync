import Link from "next/link";
import { HeartPulse } from "lucide-react";

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="footer-main">
        <div className="footer-about">
          <Link className="brand footer-brand" href="/">
            <span className="brand-icon"><HeartPulse size={20} strokeWidth={2.5} /></span>
            <span>medi<span className="brand-accent">sync</span></span>
          </Link>
          <p>Thoughtful healthcare, connected around you.</p>
        </div>
        <div className="footer-links">
          <span className="footer-label">Explore</span>
          <Link href="/doctors">Our doctors</Link>
          <Link href="/#how-it-works">How it works</Link>
        </div>
        <div className="footer-links">
          <span className="footer-label">A note on care</span>
          <span>Contact the clinic directly about care options and availability.</span>
          <span>For emergencies, contact local emergency services.</span>
        </div>
      </div>
      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} MediSync</span>
        <span>Care information on this site is not a substitute for medical advice.</span>
      </div>
    </footer>
  );
}
