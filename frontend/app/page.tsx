import Link from "next/link";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  CalendarDays,
  Check,
  Clock3,
  HeartPulse,
  ShieldCheck,
  Sparkles,
  Stethoscope,
} from "lucide-react";

import { DoctorDirectory } from "@/components/doctor-directory";

const steps = [
  {
    number: "01",
    icon: <SearchIcon />,
    title: "Find your fit",
    description: "Explore specialists by name or area of care and find the experience you need.",
  },
  {
    number: "02",
    icon: <CalendarDays size={20} />,
    title: "Make your connection",
    description: "Choose a specialist and request a visit at a time that works for you.",
  },
  {
    number: "03",
    icon: <HeartPulse size={20} />,
    title: "Feel more in sync",
    description: "Keep your next step clear and focus on what matters: your wellbeing.",
  },
];

function SearchIcon() {
  return <Stethoscope size={20} />;
}

export default function HomePage() {
  return (
    <>
      <section className="hero-section">
        <div className="hero-orb hero-orb-one" />
        <div className="hero-orb hero-orb-two" />
        <div className="hero-content page-width">
          <div className="hero-copy">
            <div className="hero-eyebrow"><span className="eyebrow-dot" /> HEALTHCARE, IN SYNC WITH YOU</div>
            <h1>Good care starts with a <span>simple step.</span></h1>
            <p className="hero-description">
              Find the right doctor, make a personal connection, and bring a little more ease to your healthcare journey.
            </p>
            <div className="hero-actions">
              <Link className="button button-primary" href="/doctors">
                Find your doctor <ArrowRight size={17} />
              </Link>
              <a className="button button-quiet" href="#how-it-works">
                How it works <ArrowDown size={16} />
              </a>
            </div>
            <div className="hero-reassurance">
              <div className="reassurance-icons"><span><ShieldCheck size={15} /></span><span><HeartPulse size={15} /></span></div>
              <span>Thoughtful care starts with a conversation</span>
            </div>
          </div>
          <div className="hero-art" aria-label="Illustration of a doctor in a clinic">
            <div className="art-sun" />
            <div className="art-window"><div /><div /><div /><div /></div>
            <div className="art-plant"><i /><i /><i /><b /></div>
            <div className="art-person">
              <div className="person-hair" />
              <div className="person-head"><span /></div>
              <div className="person-neck" />
              <div className="person-coat"><span className="coat-lapel" /><span className="coat-pocket"><HeartPulse size={19} /></span></div>
            </div>
            <div className="art-stethoscope"><span /><i /></div>
            <div className="art-card art-card-top"><span className="art-card-icon"><Check size={16} /></span><span><strong>Care, connected</strong><small>One step at a time</small></span></div>
            <div className="art-card art-card-bottom"><span className="art-stars">★★★★★</span><strong>Made to feel a little easier</strong><small>For the moments that matter</small></div>
            <div className="art-label"><Sparkles size={14} /> A calmer way to care</div>
          </div>
        </div>
        <div className="hero-bottom page-width">
          <span>YOUR NEXT STEP, MADE SIMPLE</span>
          <a href="#how-it-works">Discover the MediSync difference <ArrowDown size={15} /></a>
        </div>
      </section>

      <section className="trust-strip" aria-label="MediSync values">
        <div className="trust-inner page-width">
          <div><ShieldCheck size={19} /><span><strong>Carefully connected</strong><small>Find the right specialist</small></span></div>
          <div><Clock3 size={19} /><span><strong>Your time matters</strong><small>Simple, clear next steps</small></span></div>
          <div><HeartPulse size={19} /><span><strong>People come first</strong><small>A more human experience</small></span></div>
        </div>
      </section>

      <section className="section-space process-section" id="how-it-works">
        <div className="page-width">
          <div className="section-heading">
            <span className="section-kicker">YOUR CARE, YOUR WAY</span>
            <h2>A clearer path to feeling <em>taken care of.</em></h2>
            <p>Healthcare should feel personal, not complicated. We make the first steps easier to navigate.</p>
          </div>
          <div className="steps-grid">
            {steps.map((step) => (
              <article className="step-card" key={step.number}>
                <div className="step-top"><span className="step-icon">{step.icon}</span><span className="step-number">{step.number}</span></div>
                <h3>{step.title}</h3>
                <p>{step.description}</p>
                <div className="step-line" />
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="doctors-section section-space">
        <div className="page-width">
          <div className="section-heading section-heading-row">
            <div>
              <span className="section-kicker">MEET YOUR CARE TEAM</span>
              <h2>Expertise with a <em>human touch.</em></h2>
              <p>Get to know the specialists ready to help you take your next step.</p>
            </div>
            <Link className="inline-link" href="/doctors">Meet all doctors <ArrowUpRight size={17} /></Link>
          </div>
          <DoctorDirectory compact limit={3} />
        </div>
      </section>

      <section className="care-note-section">
        <div className="care-note page-width">
          <div className="care-note-mark"><HeartPulse size={24} /></div>
          <div>
            <span className="section-kicker">A LITTLE MORE REASSURANCE</span>
            <h2>Every good health journey begins with a conversation.</h2>
            <p>Browse our directory and request an appointment with a specialist on your care team.</p>
          </div>
          <Link className="button button-light" href="/doctors">Browse specialists <ArrowRight size={17} /></Link>
          <div className="care-note-deco" aria-hidden="true"><HeartPulse size={152} strokeWidth={0.7} /></div>
        </div>
      </section>

      <section className="closing-section">
        <div className="page-width closing-inner">
          <span className="section-kicker">A HEALTHIER TOMORROW STARTS HERE</span>
          <h2>Make a little room for <em>your health.</em></h2>
          <p>Take one simple step toward care that feels more connected.</p>
          <Link className="button button-primary" href="/doctors">Explore our doctors <ArrowRight size={17} /></Link>
          <span className="closing-decoration closing-decoration-left"><HeartPulse size={29} /></span>
          <span className="closing-decoration closing-decoration-right"><Sparkles size={25} /></span>
        </div>
      </section>
    </>
  );
}
