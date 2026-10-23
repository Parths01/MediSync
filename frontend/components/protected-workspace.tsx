"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import {
  Activity,
  CalendarDays,
  LayoutDashboard,
  Lightbulb,
  LogOut,
  Mail,
  MessageSquareText,
  Search,
  Stethoscope,
  UserRound,
} from "lucide-react";
import { getCurrentUser, logout, type User } from "@/lib/api";

export function useProtectedUser(requiredRole?: User["role"]) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    getCurrentUser(controller.signal)
      .then((currentUser) => {
        if (requiredRole && currentUser.role !== requiredRole) {
          router.replace(currentUser.role === "admin" ? "/admin" : "/dashboard");
          return;
        }
        setUser(currentUser);
      })
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Unable to verify your account.");
        if (reason instanceof Error && reason.message === "Authentication required") {
          const requestedPath =
            typeof window === "undefined" ? pathname : pathname + window.location.search;
          router.replace(`/login?next=${encodeURIComponent(requestedPath)}`);
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [pathname, requiredRole, router]);

  return { user, loading, error };
}

export function WorkspaceFrame({
  title,
  description,
  children,
  role,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  role: User["role"];
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [logoutError, setLogoutError] = useState<string | null>(null);
  const userLinks =
    role === "admin"
      ? [
          { label: "Overview", href: "/admin", icon: LayoutDashboard },
          { label: "Doctors", href: "/admin/doctors", icon: Stethoscope },
          { label: "Appointments", href: "/admin/appointments", icon: CalendarDays },
          { label: "Heuristic insights", href: "/admin/insights", icon: Lightbulb },
          { label: "Inquiries", href: "/admin/reports", icon: Mail },
          { label: "Feedback", href: "/admin/feedback", icon: MessageSquareText },
        ]
      : [
          { label: "Overview", href: "/dashboard", icon: LayoutDashboard },
          { label: "Find a doctor", href: "/doctors", icon: Search },
          { label: "Symptom checker", href: "/symptoms", icon: Activity },
          { label: "My history", href: "/history", icon: CalendarDays },
          { label: "My profile", href: "/profile", icon: UserRound },
          { label: "Contact", href: "/contact", icon: Mail },
        ];

  return (
    <section className="workspace-section">
      <div className="workspace-heading page-width">
        <div>
          <span className="section-kicker">{role === "admin" ? "ADMINISTRATION" : "YOUR CARE"}</span>
          <h1>{title}</h1>
          {description && <p>{description}</p>}
        </div>
      </div>
      <div className="workspace-layout page-width">
        <nav className="workspace-nav" aria-label={`${role} navigation`}>
          <div className="workspace-nav-heading">
            <span className="workspace-nav-heading-icon">
              {role === "admin" ? <Stethoscope aria-hidden="true" /> : <Activity aria-hidden="true" />}
            </span>
            <div>
              <strong>{role === "admin" ? "Admin console" : "Patient portal"}</strong>
              <span>{role === "admin" ? "MediSync management" : "Your care, in one place"}</span>
            </div>
          </div>
          <span className="workspace-nav-label">{role === "admin" ? "Manage" : "My account"}</span>
          {userLinks.map(({ label, href, icon: Icon }) => (
            <Link aria-current={pathname === href ? "page" : undefined} href={href} key={href}>
              <Icon aria-hidden="true" size={19} strokeWidth={1.8} />
              <span>{label}</span>
            </Link>
          ))}
          <button
            className="workspace-logout"
            onClick={async () => {
              setLogoutError(null);
              try {
                await logout();
                router.replace("/login");
              } catch (reason) {
                setLogoutError(reason instanceof Error ? reason.message : "Could not sign out.");
              }
            }}
            type="button"
          >
            <LogOut aria-hidden="true" size={18} />
            Sign out
          </button>
        </nav>
        <div className="workspace-content">
          {logoutError && <WorkspaceError message={logoutError} />}
          {children}
        </div>
      </div>
    </section>
  );
}

export function WorkspaceLoading({ message = "Loading your workspace…" }: { message?: string }) {
  return <div aria-live="polite" className="workspace-state">{message}</div>;
}

export function WorkspaceError({ message }: { message: string }) {
  return <div className="form-alert form-alert-error" role="alert">{message}</div>;
}
