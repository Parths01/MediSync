<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>MediSync — Care that fits your life</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <style>
        .landing-hero { background: #fff; overflow:hidden; }
        .hero-grid { display:grid; grid-template-columns:1.05fr .95fr; align-items:center; gap:60px; min-height:560px; }
        .hero-grid h1 { font-size:clamp(3rem,6vw,5.7rem); letter-spacing:-.055em; margin:14px 0 22px; }
        .hero-grid h1 em { color:var(--teal); font-style:normal; }
        .hero-copy { max-width:570px; font-size:1.15rem; color:var(--muted); }
        .hero-actions { display:flex; gap:12px; margin-top:30px; flex-wrap:wrap; }
        .hero-art { position:relative; min-height:450px; background:#dff6ef; border-radius:42% 42% 18px 42%; overflow:hidden; }
        .hero-art img { width:100%; height:100%; object-fit:cover; mix-blend-mode:multiply; opacity:.88; }
        .floating-card { position:absolute; bottom:24px; left:24px; background:#fff; border-radius:14px; padding:14px 18px; box-shadow:var(--shadow); }
        .trust { padding:26px 0; border-bottom:1px solid var(--line); }
        .trust-row { display:flex; justify-content:space-between; gap:20px; flex-wrap:wrap; color:var(--muted); font-weight:600; }
        .trust-row strong { color:var(--navy); }
        .section-heading { max-width:590px; margin-bottom:35px; }
        .section-heading h2 { font-size:clamp(2rem,4vw,3.2rem); margin:10px 0; }
        .search-card { margin-top:-42px; position:relative; z-index:1; display:grid; grid-template-columns:1fr 1fr auto; gap:12px; align-items:end; }
        .doctor-tile img { width:72px; height:72px; object-fit:cover; border-radius:50%; float:left; margin-right:16px; }
        .testimonial { background:var(--navy); color:#fff; border-radius:24px; padding:48px; }
        .testimonial h2, .testimonial p { color:#fff; }
        .cta-band { background:var(--teal); color:#fff; text-align:center; border-radius:24px; padding:55px 25px; }
        .cta-band h2 { color:#fff; font-size:2.7rem; }
        footer { background:var(--navy); color:#c9d7e1; padding:42px 0; }
        footer a { color:#fff; margin-left:18px; }
        @media(max-width:700px){ .hero-grid{grid-template-columns:1fr; gap:25px; min-height:0; padding:55px 0}.hero-art{min-height:280px}.search-card{grid-template-columns:1fr;margin-top:0}.testimonial{padding:28px}.cta-band h2{font-size:2rem} }
    </style>
</head>
<body>
    <nav class="site-nav">
        <div class="container">
            <a class="brand" href="index.php"><span class="brand-mark">✚</span> MediSync</a>
            <div class="nav-actions"><a href="#how-it-works">How it works</a><a href="auth/login.php">Sign in</a><a class="btn" href="auth/register.php">Get started</a></div>
        </div>
    </nav>
    <main>
        <section class="landing-hero"><div class="container hero-grid">
            <div><span class="eyebrow">Healthcare, in sync with you</span><h1>Good care starts with a <em>simple</em> step.</h1><p class="hero-copy">Find the right doctor, choose a time that works, and keep your care moving forward — all from one calm, connected space.</p><div class="hero-actions"><a class="btn" href="auth/register.php">Book an appointment <span>→</span></a><a class="btn btn-outline" href="auth/login.php">I already have an account</a></div></div>
            <div class="hero-art"><img src="https://images.unsplash.com/photo-1559839734-2b71ea197ec2?auto=format&fit=crop&w=900&q=85" alt="Doctor smiling in a clinic"><div class="floating-card"><strong>● Available today</strong><br><span class="muted">Trusted specialists, ready to help</span></div></div>
        </div></section>
        <section class="trust"><div class="container trust-row"><span><strong>4.9/5</strong> patient rating</span><span><strong>10k+</strong> appointments coordinated</span><span><strong>50+</strong> verified specialists</span><span>Private and secure by design</span></div></section>
        <section class="section"><div class="container"><div class="surface search-card"><div class="form-group"><label for="specialty">I’m looking for</label><select id="specialty"><option>Any specialty</option><option>General medicine</option><option>Cardiology</option><option>Dermatology</option></select></div><div class="form-group"><label for="location">Near</label><input id="location" type="text" placeholder="City or postcode"></div><a class="btn" href="auth/register.php">Find a doctor</a></div></div></section>
        <section class="section" id="how-it-works"><div class="container"><div class="section-heading"><span class="eyebrow">A better way to care</span><h2>From “I should book that” to “I’m taken care of.”</h2></div><div class="card-grid"><article class="surface"><span class="eyebrow">01</span><h3>Find your fit</h3><p class="muted">Browse verified doctors by specialty and experience, all in one place.</p></article><article class="surface"><span class="eyebrow">02</span><h3>Pick a time</h3><p class="muted">See availability and request an appointment in just a few clicks.</p></article><article class="surface"><span class="eyebrow">03</span><h3>Stay in sync</h3><p class="muted">Keep your upcoming visits and doctor details organized from your dashboard.</p></article></div></div></section>
        <section class="section"><div class="container"><div class="section-heading"><span class="eyebrow">Meet your care team</span><h2>Expertise with a human touch.</h2></div><div class="card-grid"><article class="surface doctor-tile"><img src="uploads/doctors/doctor_67a7c4c352372.jpg" alt=""><h3>Dr. Sarah Mitchell</h3><p class="muted">General Medicine · 12 years</p></article><article class="surface doctor-tile"><img src="uploads/doctors/doctor_67a7c5c2d5f41.jpg" alt=""><h3>Dr. James Wilson</h3><p class="muted">Cardiology · 15 years</p></article><article class="surface doctor-tile"><img src="uploads/doctors/doctor_67a7c59b2e847.jpg" alt=""><h3>Dr. Priya Sharma</h3><p class="muted">Dermatology · 9 years</p></article></div></div></section>
        <section class="section"><div class="container"><div class="section-heading"><span class="eyebrow">Designed around you</span><h2>Less admin. More feeling well.</h2></div><div class="card-grid"><article class="surface"><h3>Clear, not cluttered</h3><p class="muted">Your appointments, doctor details, and next steps are easy to find.</p></article><article class="surface"><h3>Care you can trust</h3><p class="muted">Every specialist is reviewed and presented with the information you need.</p></article><article class="surface"><h3>Always in your corner</h3><p class="muted">A thoughtful experience from your first search through your follow-up.</p></article></div></div></section>
        <section class="section"><div class="container"><div class="testimonial"><span class="eyebrow">A little love from our patients</span><h2>“MediSync made booking care feel refreshingly human.”</h2><p>“I found a specialist, booked a time around work, and had all the details I needed before the visit. No phone tag, no paperwork pile-up.”</p><strong>— Maya R., MediSync patient</strong></div></div></section>
        <section class="section"><div class="container"><div class="cta-band"><h2>Make time for your health.</h2><p>Start with a more thoughtful way to manage your care.</p><a class="btn btn-secondary" href="auth/register.php">Create your free account →</a></div></div></section>
    </main>
    <footer><div class="container"><strong>✚ MediSync</strong><span style="float:right">© 2024 MediSync · <a href="#">Privacy</a><a href="#">Terms</a></span></div></footer>
</body>
</html>
