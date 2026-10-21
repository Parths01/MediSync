<?php
/**
 * user/symptom_checker.php
 *
 * "Find the Right Doctor" — AI symptom → specialty → doctor recommender.
 * Pure-PHP heuristic; no external service needed.
 */
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
require_once '../includes/ml_helpers.php';
authenticateUser();

$symptoms         = '';
$recommendations  = [];
$doctors          = [];
$searched         = false;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    verify_csrf_token();
    $symptoms = trim($_POST['symptoms'] ?? '');

    if ($symptoms !== '') {
        $searched = true;
        $recommendations = ml_recommend_specialties($symptoms);

        if (!empty($recommendations)) {
            // Fetch all doctors whose specialization matches any recommended specialty.
            // We order by whether their specialty is the top recommendation first.
            $topSpecialties = array_column($recommendations, 'specialty');
            $placeholders   = implode(',', array_fill(0, count($topSpecialties), '?'));
            $stmt = $pdo->prepare(
                "SELECT * FROM doctors
                 WHERE specialization IN ($placeholders)
                 ORDER BY FIELD(specialization, $placeholders), name"
            );
            // bind twice: once for WHERE IN, once for FIELD() ordering
            $stmt->execute(array_merge($topSpecialties, $topSpecialties));
            $doctors = $stmt->fetchAll();
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Find the Right Doctor – MediSync</title>
    <meta name="description" content="Describe your symptoms and MediSync will suggest the right specialist and let you book instantly.">
    <link href="../assets/css/style.css" rel="stylesheet">
    <style>
        /* ── Page-level extras ────────────────────────────────────────── */
        .sc-hero {
            background: linear-gradient(135deg, var(--navy) 0%, var(--navy-soft) 100%);
            border-radius: var(--radius);
            padding: 36px 32px 32px;
            margin-bottom: 28px;
            color: #fff;
        }
        .sc-hero h1 { color: #fff; margin-bottom: 6px; font-size: clamp(1.6rem, 3.5vw, 2.4rem); }
        .sc-hero p  { color: #9fb8d0; margin: 0; }

        /* search card */
        .symptom-form-card {
            background: #fff;
            border: 1px solid var(--line);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 28px 28px 24px;
            margin-bottom: 28px;
        }
        .symptom-form-card label { font-size: 1rem; }
        .symptom-input-row { display: flex; gap: 12px; align-items: flex-end; }
        .symptom-input-row textarea {
            flex: 1;
            min-height: 80px;
            resize: vertical;
        }
        .symptom-input-row .btn { align-self: flex-end; white-space: nowrap; min-width: 140px; }
        .symptom-tip { color: var(--muted); font-size: .82rem; margin-top: 8px; }

        /* results */
        .results-section { animation: rise-in .5s ease both; }

        /* specialty match chips */
        .spec-chips { display: flex; flex-wrap: wrap; gap: 10px; margin-bottom: 24px; }
        .spec-chip {
            display: flex; align-items: center; gap: 8px;
            background: linear-gradient(135deg, #e8faf5, #c6f1e5);
            border: 1px solid #a6dfd0;
            border-radius: 999px;
            padding: 7px 16px;
            font-size: .85rem; font-weight: 600; color: var(--teal-dark);
        }
        .spec-chip .chip-rank {
            background: var(--teal-dark);
            color: #fff;
            border-radius: 50%;
            width: 20px; height: 20px;
            display: inline-flex; align-items: center; justify-content: center;
            font-size: .7rem; font-weight: 700; flex-shrink: 0;
        }
        .spec-chip .chip-kws { color: var(--muted); font-size: .75rem; font-weight: 400; }

        /* doctor cards */
        .sc-doctors-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 18px;
        }
        .sc-doctor-card {
            background: #fff;
            border: 1px solid var(--line);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 20px;
            display: flex;
            gap: 16px;
            align-items: flex-start;
            transition: transform .2s, box-shadow .2s;
        }
        .sc-doctor-card:hover { transform: translateY(-3px); box-shadow: 0 20px 40px rgba(13,27,42,.12); }
        .sc-doc-photo {
            width: 70px; height: 70px; flex-shrink: 0;
            border-radius: 50%; object-fit: cover;
            background: var(--slate);
            display: flex; align-items: center; justify-content: center;
            font-size: 1.8rem; color: var(--muted);
        }
        .sc-doc-photo img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }
        .sc-doc-info { flex: 1; }
        .sc-doc-name { font-weight: 700; font-size: 1.05rem; color: var(--navy); margin-bottom: 2px; }
        .sc-doc-spec {
            font-size: .8rem; font-weight: 700;
            color: var(--teal-dark); text-transform: uppercase; letter-spacing: .06em;
            margin-bottom: 6px;
        }
        .sc-doc-exp { color: var(--muted); font-size: .82rem; margin-bottom: 12px; }
        .sc-doc-actions { display: flex; gap: 8px; flex-wrap: wrap; }

        .no-match-card {
            background: #fff;
            border: 1px solid var(--line);
            border-radius: var(--radius);
            padding: 40px 28px;
            text-align: center;
            color: var(--muted);
        }
        .no-match-card .icon { font-size: 2.5rem; display: block; margin-bottom: 12px; }

        /* section headings */
        .result-heading {
            font-size: 1rem; text-transform: uppercase; letter-spacing: .08em;
            color: var(--muted); font-weight: 700; margin: 0 0 14px;
        }

        @media (max-width: 640px) {
            .symptom-input-row { flex-direction: column; }
            .symptom-input-row .btn { width: 100%; }
        }
    </style>
</head>
<body>
<div class="dashboard-container">
    <!-- Sidebar -->
    <div class="user-sidebar">
        <h2>Welcome, <?= htmlspecialchars($_SESSION['name']) ?></h2>
        <nav>
            <a href="dashboard.php" class="nav-link">Dashboard</a>
            <a href="history.php" class="nav-link">My History</a>
            <a href="doctors.php" class="nav-link">Book Appointment</a>
            <a href="symptom_checker.php" class="nav-link active">Find the Right Doctor</a>
            <a href="contact.php" class="nav-link">Contact Us</a>
            <a href="profile.php" class="nav-link">My Profile</a>
            <a href="../auth/logout.php" class="nav-link">Logout</a>
        </nav>
    </div>

    <!-- Main Content -->
    <div class="user-main">

        <div class="sc-hero">
            <h1>🩺 Find the Right Doctor</h1>
            <p>Describe your symptoms in plain language and we'll suggest the right specialist, then show you available doctors to book instantly.</p>
        </div>

        <!-- Symptom Input Form -->
        <div class="symptom-form-card">
            <form method="POST" action="symptom_checker.php" id="symptom-form">
                <?= csrf_field() ?>
                <div class="form-group">
                    <label for="symptoms">What symptoms are you experiencing?</label>
                    <div class="symptom-input-row">
                        <textarea
                            id="symptoms"
                            name="symptoms"
                            placeholder="e.g. I have a severe headache, dizziness and blurred vision for the past two days..."
                            required
                        ><?= htmlspecialchars($symptoms, ENT_QUOTES, 'UTF-8') ?></textarea>
                        <button type="submit" class="btn" id="find-btn">
                            <span id="btn-text">🔍 Find Doctor</span>
                        </button>
                    </div>
                    <p class="symptom-tip">
                        💡 Tip: Be specific — mention location of pain, duration, and severity for better matches.
                    </p>
                </div>
            </form>
        </div>

        <!-- Results -->
        <?php if ($searched): ?>
        <div class="results-section">

            <?php if (empty($recommendations)): ?>
                <div class="no-match-card">
                    <span class="icon">🔎</span>
                    <h3>No specialty matched</h3>
                    <p>We couldn't identify a specialty from those symptoms. Try describing your symptoms differently, or <a href="doctors.php">browse all doctors</a>.</p>
                </div>

            <?php else: ?>

                <!-- Specialty chips -->
                <p class="result-heading">Recommended Specialties</p>
                <div class="spec-chips">
                    <?php foreach ($recommendations as $i => $rec): ?>
                    <div class="spec-chip">
                        <span class="chip-rank"><?= $i + 1 ?></span>
                        <?= htmlspecialchars($rec['specialty'], ENT_QUOTES, 'UTF-8') ?>
                        <span class="chip-kws">· <?= htmlspecialchars(implode(', ', array_slice($rec['matched'], 0, 3)), ENT_QUOTES, 'UTF-8') ?></span>
                    </div>
                    <?php endforeach; ?>
                </div>

                <!-- Doctor cards -->
                <p class="result-heading" style="margin-top:8px;">
                    <?= count($doctors) ?> Matching Doctor<?= count($doctors) !== 1 ? 's' : '' ?> Available
                </p>

                <?php if (empty($doctors)): ?>
                    <div class="no-match-card">
                        <span class="icon">👨‍⚕️</span>
                        <h3>No doctors available for these specialties yet</h3>
                        <p>Check back later or <a href="doctors.php">view all doctors</a>.</p>
                    </div>
                <?php else: ?>
                    <div class="sc-doctors-grid">
                        <?php foreach ($doctors as $doc): ?>
                        <div class="sc-doctor-card">
                            <div class="sc-doc-photo">
                                <?php if (!empty($doc['photo'])): ?>
                                    <img src="<?= htmlspecialchars($doc['photo'], ENT_QUOTES, 'UTF-8') ?>"
                                         alt="Dr. <?= htmlspecialchars($doc['name'], ENT_QUOTES, 'UTF-8') ?>">
                                <?php else: ?>
                                    👨‍⚕️
                                <?php endif; ?>
                            </div>
                            <div class="sc-doc-info">
                                <div class="sc-doc-name">Dr. <?= htmlspecialchars($doc['name'], ENT_QUOTES, 'UTF-8') ?></div>
                                <div class="sc-doc-spec"><?= htmlspecialchars($doc['specialization'], ENT_QUOTES, 'UTF-8') ?></div>
                                <div class="sc-doc-exp">
                                    <?= htmlspecialchars((string)$doc['experience'], ENT_QUOTES, 'UTF-8') ?>+ yrs experience
                                    &nbsp;·&nbsp; 📞 <?= htmlspecialchars($doc['contact_details'], ENT_QUOTES, 'UTF-8') ?>
                                </div>
                                <div class="sc-doc-actions">
                                    <a href="book_appointment.php?doctor_id=<?= urlencode((string)$doc['doctor_id']) ?>"
                                       class="btn" id="book-doc-<?= (int)$doc['doctor_id'] ?>">
                                        Book Appointment
                                    </a>
                                </div>
                            </div>
                        </div>
                        <?php endforeach; ?>
                    </div>
                <?php endif; ?>

            <?php endif; ?>

        </div><!-- /results-section -->
        <?php endif; ?>

    </div><!-- /user-main -->
</div>

<script>
document.getElementById('symptom-form').addEventListener('submit', function () {
    const btn  = document.getElementById('find-btn');
    const text = document.getElementById('btn-text');
    btn.disabled = true;
    text.textContent = '⏳ Analysing…';
});
</script>
</body>
</html>
