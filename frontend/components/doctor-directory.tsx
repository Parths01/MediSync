"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { ArrowUpRight, BriefcaseMedical, Phone, Search, SlidersHorizontal, UserRound } from "lucide-react";

import { getDoctorPhotoUrl, getDoctors, type Doctor } from "@/lib/api";

interface DoctorDirectoryProps {
  limit?: number;
  compact?: boolean;
}

function initials(name: string): string {
  return name
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function DoctorCard({ doctor, compact = false }: { doctor: Doctor; compact?: boolean }) {
  const phone = doctor.contact_details.replace(/[^\d+]/g, "");
  const photoUrl = getDoctorPhotoUrl(doctor.photo);

  return (
    <article className={`doctor-card${compact ? " doctor-card-compact" : ""}`}>
      <div className="doctor-card-top">
        <div className="doctor-avatar" aria-hidden={!photoUrl}>
          {photoUrl ? (
            <Image
              alt={`Portrait of Dr. ${doctor.name}`}
              className="doctor-avatar-photo"
              height={74}
              src={photoUrl}
              unoptimized
              width={74}
            />
          ) : initials(doctor.name)}
        </div>
        <span className="availability"><span />MediSync listing</span>
      </div>
      <div className="doctor-card-body">
        <span className="doctor-specialty">{doctor.specialization}</span>
        <h3>Dr. {doctor.name}</h3>
        <div className="doctor-meta">
          <span><BriefcaseMedical size={15} /> {doctor.experience} years experience</span>
          <span><UserRound size={15} /> Specialist care</span>
        </div>
        <div className="doctor-card-footer">
          <Link
            className="doctor-call"
            href={`/appointments/new?doctor_id=${doctor.doctor_id}`}
            aria-label={`Book an appointment with Dr. ${doctor.name}`}
          >
            Book a visit <ArrowUpRight size={15} />
          </Link>
          {phone && (
            <a className="doctor-contact-label doctor-phone" href={`tel:${phone}`} aria-label={`Call Dr. ${doctor.name}`}>
              <Phone size={15} /> Call clinic
            </a>
          )}
        </div>
      </div>
    </article>
  );
}

function DoctorCardSkeleton() {
  return (
    <div className="doctor-card doctor-skeleton" aria-hidden="true">
      <div className="skeleton-avatar" />
      <div className="skeleton-line skeleton-short" />
      <div className="skeleton-line skeleton-long" />
      <div className="skeleton-line skeleton-medium" />
    </div>
  );
}

export function DoctorDirectory({ limit, compact = false }: DoctorDirectoryProps) {
  const [doctors, setDoctors] = useState<Doctor[]>([]);
  const [query, setQuery] = useState("");
  const [specialty, setSpecialty] = useState("All specialties");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    getDoctors(controller.signal)
      .then(setDoctors)
      .catch((reason: unknown) => {
        if (reason instanceof DOMException && reason.name === "AbortError") return;
        setError(reason instanceof Error ? reason.message : "Could not load doctors.");
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });

    return () => controller.abort();
  }, [refreshKey]);

  const specialties = useMemo(
    () => ["All specialties", ...Array.from(new Set(doctors.map((doctor) => doctor.specialization))).sort()],
    [doctors],
  );

  const filteredDoctors = useMemo(() => {
    const normalizedQuery = query.trim().toLowerCase();
    return doctors.filter((doctor) => {
      const matchesSpecialty = specialty === "All specialties" || doctor.specialization === specialty;
      const matchesQuery =
        normalizedQuery.length === 0 ||
        doctor.name.toLowerCase().includes(normalizedQuery) ||
        doctor.specialization.toLowerCase().includes(normalizedQuery);
      return matchesSpecialty && matchesQuery;
    });
  }, [doctors, query, specialty]);

  const visibleDoctors = limit ? filteredDoctors.slice(0, limit) : filteredDoctors;

  return (
    <div className="directory">
      {!compact && (
        <div className="directory-toolbar">
          <label className="directory-search">
            <Search size={18} />
            <span className="sr-only">Search doctors or specialties</span>
            <input
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search a doctor or specialty"
              type="search"
              value={query}
            />
          </label>
          <label className="directory-filter">
            <SlidersHorizontal size={17} />
            <span className="sr-only">Filter by specialty</span>
            <select onChange={(event) => setSpecialty(event.target.value)} value={specialty}>
              {specialties.map((option) => <option key={option}>{option}</option>)}
            </select>
          </label>
          {!loading && !error && (
            <span className="results-count">{filteredDoctors.length} {filteredDoctors.length === 1 ? "doctor" : "doctors"}</span>
          )}
        </div>
      )}

      {loading && (
        <div className="doctor-grid">
          {Array.from({ length: limit ?? 6 }, (_, index) => <DoctorCardSkeleton key={index} />)}
        </div>
      )}

      {!loading && error && (
        <div className="directory-message directory-error" role="alert">
          <div className="message-icon"><BriefcaseMedical size={22} /></div>
          <div>
            <h3>We couldn’t load the care team</h3>
            <p>{error}</p>
            <button
              className="text-button"
              onClick={() => {
                setLoading(true);
                setError(null);
                setRefreshKey((key) => key + 1);
              }}
              type="button"
            >
              Try again <ArrowUpRight size={15} />
            </button>
          </div>
        </div>
      )}

      {!loading && !error && visibleDoctors.length > 0 && (
        <div className="doctor-grid">
          {visibleDoctors.map((doctor) => (
            <DoctorCard compact={compact} doctor={doctor} key={doctor.doctor_id} />
          ))}
        </div>
      )}

      {!loading && !error && visibleDoctors.length === 0 && (
        <div className="directory-message">
          <div className="message-icon"><Search size={22} /></div>
          <div>
            <h3>{doctors.length === 0 ? "Our directory is growing" : "No doctors match that search"}</h3>
            <p>{doctors.length === 0 ? "There are no doctors listed yet. Please check back soon." : "Try another name or choose a different specialty."}</p>
          </div>
        </div>
      )}
    </div>
  );
}
