"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { ArrowUpRight, HeartPulse, Menu, X } from "lucide-react";
import { getCurrentUser, logout, type User } from "@/lib/api";

export function SiteHeader() {
  const router = useRouter();
  const [menuOpen, setMenuOpen] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [authError, setAuthError] = useState<string | null>(null);
  const pathname = usePathname();

  useEffect(() => {
    const controller = new AbortController();
    setCheckingSession(true);
    setAuthError(null);

    getCurrentUser(controller.signal)
      .then(setUser)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setUser(null);
      })
      .finally(() => {
        if (!controller.signal.aborted) setCheckingSession(false);
      });

    setMenuOpen(false);
    return () => controller.abort();
  }, [pathname]);

  async function handleSignOut() {
    setAuthError(null);
    try {
      await logout();
      setUser(null);
      setMenuOpen(false);
      router.replace("/");
      router.refresh();
    } catch (reason) {
      setAuthError(reason instanceof Error ? reason.message : "Could not sign out.");
    }
  }

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
          {!checkingSession && !user && (
            <>
              <Link href="/login" onClick={() => setMenuOpen(false)}>Sign in</Link>
              <Link className="nav-cta" href="/register" onClick={() => setMenuOpen(false)}>
                Create account <ArrowUpRight size={16} />
              </Link>
            </>
          )}
          {!checkingSession && user && user.role === "patient" && (
            <>
              <Link href="/ai-assistant" onClick={() => setMenuOpen(false)}>AI assistant</Link>
              <Link className="nav-cta" href="/dashboard" onClick={() => setMenuOpen(false)}>
                My dashboard <ArrowUpRight size={16} />
              </Link>
              <button className="nav-signout" onClick={() => void handleSignOut()} type="button">
                Sign out
              </button>
            </>
          )}
          {!checkingSession && user && user.role === "admin" && (
            <>
              <Link className="nav-cta" href="/admin" onClick={() => setMenuOpen(false)}>
                Admin dashboard <ArrowUpRight size={16} />
              </Link>
              <button className="nav-signout" onClick={() => void handleSignOut()} type="button">
                Sign out
              </button>
            </>
          )}
        </nav>
        {authError && <span className="nav-auth-error" role="alert">{authError}</span>}
      </div>
    </header>
  );
}
