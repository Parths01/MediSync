"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowUpRight, HeartPulse, Menu, X } from "lucide-react";

export function SiteHeader() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="site-header">
      <div className="nav-wrap">
        <Link className="brand" href="/" aria-label="MediSync home" onClick={() => setMenuOpen(false)}>
          <span className="brand-icon"><HeartPulse size={21} strokeWidth={2.5} /></span>
          <span>medi<span className="brand-accent">sync</span></span>
        </Link>
        <button
          aria-expanded={menuOpen}
          aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          className="mobile-menu-toggle"
          onClick={() => setMenuOpen(!menuOpen)}
          type="button"
        >
          {menuOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
        <nav className={menuOpen ? "site-nav is-open" : "site-nav"} aria-label="Main navigation">
          <Link href="/doctors" onClick={() => setMenuOpen(false)}>Find a doctor</Link>
          <Link href="/#how-it-works" onClick={() => setMenuOpen(false)}>How it works</Link>
          <Link href="/login" onClick={() => setMenuOpen(false)}>Sign in</Link>
          <Link className="nav-cta" href="/doctors" onClick={() => setMenuOpen(false)}>
            Explore care <ArrowUpRight size={16} />
          </Link>
        </nav>
      </div>
    </header>
  );
}
