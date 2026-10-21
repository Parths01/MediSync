<?php
/**
 * admin/ml_insights.php
 *
 * AI Insights dashboard for admins:
 *   - Upcoming appointment no-show risk table
 *   - Feedback sentiment breakdown
 */
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
require_once '../includes/ml_helpers.php';
authenticateUser(['admin']);

// ── 1. NO-SHOW RISK ─────────────────────────────────────────────────────────

// Fetch upcoming appointments with patient miss-rate data
$upcoming = [];
try {
    $stmt = $pdo->query(
        "SELECT
             a.appointment_id,
             a.appointment_date,
             a.created_at,
             a.status,
             a.description,
             u.user_id,
             u.name  AS patient_name,
             d.name  AS doctor_name,
             d.specialization,
             -- total appointments for this patient (excluding current)
             (SELECT COUNT(*) FROM appointments a2
              WHERE a2.user_id = u.user_id
                AND a2.appointment_id != a.appointment_id) AS past_total,
             -- appointments patient did NOT complete (missed/cancelled/rejected)
             (SELECT COUNT(*) FROM appointments a3
              WHERE a3.user_id = u.user_id
                AND a3.appointment_id != a.appointment_id
                AND a3.status IN ('cancelled','rejected')
                AND a3.appointment_date < NOW()) AS past_missed
         FROM appointments a
         JOIN users u  ON a.user_id    = u.user_id
         JOIN doctors d ON a.doctor_id = d.doctor_id
         WHERE a.appointment_date >= NOW()
           AND a.status IN ('pending','confirmed')
         ORDER BY a.appointment_date ASC
         LIMIT 50"
    );
    $upcoming = $stmt->fetchAll();
} catch (PDOException $e) {
    error_log('ML insights – upcoming fetch failed: ' . $e->getMessage());
}

// Score each appointment
$scored = [];
foreach ($upcoming as $appt) {
    $result    = ml_noshow_score($appt);
    $scored[]  = array_merge($appt, $result);
}

// Sort: High first, then Medium, then Low
$labelOrder = ['High' => 0, 'Medium' => 1, 'Low' => 2];
usort($scored, fn($a, $b) => $labelOrder[$a['label']] <=> $labelOrder[$b['label']]);

// Counts for summary chips
$highCount   = count(array_filter($scored, fn($r) => $r['label'] === 'High'));
$medCount    = count(array_filter($scored, fn($r) => $r['label'] === 'Medium'));
$lowCount    = count(array_filter($scored, fn($r) => $r['label'] === 'Low'));


// ── 2. FEEDBACK SENTIMENT ────────────────────────────────────────────────────

$feedback_all    = [];
$sentiment_tally = ['positive' => 0, 'neutral' => 0, 'negative' => 0];
$negative_list   = [];

try {
    $stmt = $pdo->query(
        "SELECT f.feedback_id, f.message, f.created_at, u.name AS user_name
         FROM feedback f
         JOIN users u ON f.user_id = u.user_id
         ORDER BY f.created_at DESC"
    );
    $feedback_all = $stmt->fetchAll();
} catch (PDOException $e) {
    error_log('ML insights – feedback fetch failed: ' . $e->getMessage());
}

foreach ($feedback_all as &$fb) {
    $result         = ml_classify_sentiment($fb['message']);
    $fb['sentiment'] = $result['sentiment'];
    $sentiment_tally[$result['sentiment']]++;
    if ($result['sentiment'] === 'negative') {
        $negative_list[] = $fb;
    }
}
unset($fb);

$total_feedback = count($feedback_all);
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Insights – MediSync Admin</title>
    <meta name="description" content="Admin AI Insights: no-show risk predictions and feedback sentiment analysis for MediSync.">
    <link href="../assets/css/style.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        /* ── Hero banner ──────────────────────────────────────────────── */
        .ai-hero {
            background: linear-gradient(135deg, #0d1b2a 0%, #1b3145 55%, #0ea98b22 100%);
            border-radius: var(--radius);
            padding: 32px 28px;
            margin-bottom: 28px;
            border: 1px solid rgba(14,169,139,.2);
        }
        .ai-hero h1 { color: #fff; font-size: clamp(1.5rem,3.5vw,2.2rem); margin-bottom: 6px; }
        .ai-hero p  { color: #9fb8d0; margin: 0; }

        /* section headings */
        .section-title {
            display: flex; align-items: center; gap: 10px;
            font-family: Fraunces, serif;
            font-size: 1.35rem; color: var(--navy);
            margin: 0 0 16px;
        }
        .section-title .icon { font-size: 1.5rem; }

        /* ── No-show summary chips ────────────────────────────────────── */
        .risk-summary { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
        .risk-chip {
            display: flex; align-items: center; gap: 10px;
            padding: 12px 18px; border-radius: var(--radius);
            font-weight: 700; font-size: .9rem;
            border: 1px solid transparent;
        }
        .risk-chip .chip-count { font-size: 1.6rem; font-weight: 800; }
        .risk-chip.high   { background: #fff0f0; border-color: #fcc; color: #a52c2c; }
        .risk-chip.medium { background: #fff8e6; border-color: #f5d87e; color: #7a5400; }
        .risk-chip.low    { background: #e8faf5; border-color: #a6dfd0; color: #087e69; }

        /* ── No-show table ────────────────────────────────────────────── */
        .insights-table-wrap {
            background: #fff;
            border: 1px solid var(--line);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            overflow: auto;
            margin-bottom: 36px;
        }
        .insights-table-wrap table { min-width: 700px; }

        .risk-badge {
            display: inline-flex; align-items: center; gap: 5px;
            padding: 4px 10px; border-radius: 999px;
            font-size: .75rem; font-weight: 700;
        }
        .risk-badge.high   { background: #fff0f0; color: #a52c2c; }
        .risk-badge.medium { background: #fff8e6; color: #7a5400; }
        .risk-badge.low    { background: #e8faf5; color: #087e69; }

        .factors-list { margin: 0; padding: 0; list-style: none; }
        .factors-list li { font-size: .78rem; color: var(--muted); }
        .factors-list li::before { content: '· '; }

        td.action-cell { font-size: .8rem; color: var(--muted); max-width: 200px; }

        /* ── Sentiment section ────────────────────────────────────────── */
        .sentiment-section { margin-top: 12px; }

        .sentiment-charts-row {
            display: grid;
            grid-template-columns: 260px 1fr;
            gap: 20px;
            margin-bottom: 24px;
        }
        .sentiment-chart-card {
            background: #fff;
            border: 1px solid var(--line);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 20px;
            display: flex; flex-direction: column; align-items: center;
        }
        .sentiment-bars-card {
            background: #fff;
            border: 1px solid var(--line);
            border-radius: var(--radius);
            box-shadow: var(--shadow);
            padding: 24px 28px;
        }
        .sent-bar-row { display: flex; align-items: center; gap: 12px; margin-bottom: 14px; }
        .sent-bar-label { width: 80px; font-weight: 600; font-size: .9rem; }
        .sent-bar-track { flex: 1; background: var(--slate); border-radius: 999px; height: 16px; overflow: hidden; }
        .sent-bar-fill  { height: 100%; border-radius: 999px; transition: width 1s ease; }
        .sent-bar-fill.positive { background: var(--teal); }
        .sent-bar-fill.neutral  { background: #a0aec0; }
        .sent-bar-fill.negative { background: var(--coral); }
        .sent-bar-pct   { font-size: .85rem; font-weight: 700; width: 38px; text-align: right; }

        /* negative messages list */
        .neg-list { display: flex; flex-direction: column; gap: 12px; }
        .neg-card {
            background: #fff8f8;
            border: 1px solid #fcc;
            border-left: 4px solid var(--coral);
            border-radius: 10px;
            padding: 14px 16px;
        }
        .neg-card-meta { font-size: .78rem; color: var(--muted); margin-bottom: 6px; }
        .neg-card-msg  { font-size: .92rem; color: var(--ink); }

        .disclaimer {
            background: #fffbe6;
            border: 1px solid #f5d87e;
            border-radius: 10px;
            padding: 12px 16px;
            font-size: .82rem;
            color: #7a5400;
            margin-bottom: 28px;
        }

        @media (max-width: 900px) {
            .sentiment-charts-row { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
<div class="admin-dashboard">
    <!-- Sidebar -->
    <div class="admin-sidebar">
        <h2>MediSync Admin</h2>
        <nav>
            <a href="dashboard.php" class="nav-link">Dashboard</a>
            <a href="doctors.php" class="nav-link">Manage Doctors</a>
            <a href="feedback.php" class="nav-link">Patient Feedback</a>
            <a href="reports.php" class="nav-link">System Reports</a>
            <a href="ml_insights.php" class="nav-link active">AI Insights</a>
            <a href="logout.php" class="nav-link">Logout</a>
        </nav>
    </div>

    <!-- Main Content -->
    <div class="admin-main">

        <div class="ai-hero">
            <h1>🤖 AI Insights</h1>
            <p>Heuristic models running live on your real database — no-show risk scoring and feedback sentiment analysis.</p>
        </div>

        <div class="disclaimer">
            ⚠️ <strong>Note:</strong> These are rule-based heuristics, not trained ML models. They use lead time, appointment timing, patient history, and keyword matching. Accuracy improves automatically as your database grows.
        </div>

        <!-- ══════════════════════════════════════════════════════════ -->
        <!-- SECTION 1: NO-SHOW RISK                                   -->
        <!-- ══════════════════════════════════════════════════════════ -->
        <div class="section-title">
            <span class="icon">📅</span> Upcoming Appointment No-Show Risk
        </div>

        <!-- Summary chips -->
        <div class="risk-summary">
            <div class="risk-chip high">
                <span class="chip-count"><?= $highCount ?></span>
                High Risk
            </div>
            <div class="risk-chip medium">
                <span class="chip-count"><?= $medCount ?></span>
                Medium Risk
            </div>
            <div class="risk-chip low">
                <span class="chip-count"><?= $lowCount ?></span>
                Low Risk
            </div>
        </div>

        <div class="insights-table-wrap">
            <?php if (empty($scored)): ?>
                <div style="padding:40px;text-align:center;color:var(--muted);">
                    <p style="font-size:2rem;margin:0;">📭</p>
                    <p>No upcoming appointments to score right now.</p>
                </div>
            <?php else: ?>
            <table>
                <thead>
                    <tr>
                        <th>Patient</th>
                        <th>Doctor / Specialty</th>
                        <th>Date &amp; Time</th>
                        <th>Risk</th>
                        <th>Risk Factors</th>
                        <th>Suggested Action</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($scored as $row): ?>
                    <?php $rl = strtolower($row['label']); ?>
                    <tr>
                        <td><strong><?= htmlspecialchars($row['patient_name'], ENT_QUOTES, 'UTF-8') ?></strong></td>
                        <td>
                            Dr. <?= htmlspecialchars($row['doctor_name'], ENT_QUOTES, 'UTF-8') ?><br>
                            <small style="color:var(--teal-dark);font-weight:600;">
                                <?= htmlspecialchars($row['specialization'], ENT_QUOTES, 'UTF-8') ?>
                            </small>
                        </td>
                        <td style="white-space:nowrap;">
                            <?= date('M j, Y', strtotime($row['appointment_date'])) ?><br>
                            <small style="color:var(--muted);"><?= date('g:i A', strtotime($row['appointment_date'])) ?></small>
                        </td>
                        <td>
                            <span class="risk-badge <?= $rl ?>">
                                <?php
                                $icon = match ($row['label']) {
                                    'High'   => '🔴',
                                    'Medium' => '🟡',
                                    default  => '🟢',
                                };
                                ?>
                                <?= $icon ?> <?= htmlspecialchars($row['label'], ENT_QUOTES, 'UTF-8') ?>
                            </span>
                            <div style="font-size:.75rem;color:var(--muted);margin-top:4px;">
                                <?= round($row['risk'] * 100) ?>%
                            </div>
                        </td>
                        <td>
                            <ul class="factors-list">
                                <?php foreach ($row['factors'] as $factor): ?>
                                <li><?= htmlspecialchars($factor, ENT_QUOTES, 'UTF-8') ?></li>
                                <?php endforeach; ?>
                            </ul>
                        </td>
                        <td class="action-cell">
                            <?= htmlspecialchars(ml_noshow_action($row['label']), ENT_QUOTES, 'UTF-8') ?>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
            <?php endif; ?>
        </div>

        <!-- ══════════════════════════════════════════════════════════ -->
        <!-- SECTION 2: FEEDBACK SENTIMENT                             -->
        <!-- ══════════════════════════════════════════════════════════ -->
        <div class="section-title sentiment-section">
            <span class="icon">💬</span> Patient Feedback Sentiment
        </div>

        <?php if ($total_feedback === 0): ?>
            <div class="insights-table-wrap" style="margin-bottom:36px;">
                <div style="padding:40px;text-align:center;color:var(--muted);">
                    <p style="font-size:2rem;margin:0;">📭</p>
                    <p>No feedback submitted yet. Check back once patients start leaving reviews.</p>
                </div>
            </div>
        <?php else: ?>

        <div class="sentiment-charts-row">
            <!-- Donut chart -->
            <div class="sentiment-chart-card">
                <canvas id="sentimentDonut" width="200" height="200"></canvas>
                <p style="font-size:.8rem;color:var(--muted);margin-top:12px;text-align:center;">
                    Based on <?= $total_feedback ?> feedback<?= $total_feedback !== 1 ? 's' : '' ?>
                </p>
            </div>

            <!-- Bar breakdown -->
            <div class="sentiment-bars-card">
                <h3 style="margin-top:0;margin-bottom:18px;font-size:1rem;">Sentiment Breakdown</h3>
                <?php
                $sentiments = [
                    'positive' => ['label' => '😊 Positive', 'color' => 'positive'],
                    'neutral'  => ['label' => '😐 Neutral',  'color' => 'neutral'],
                    'negative' => ['label' => '😞 Negative', 'color' => 'negative'],
                ];
                foreach ($sentiments as $key => $meta):
                    $count = $sentiment_tally[$key];
                    $pct   = $total_feedback > 0 ? round($count / $total_feedback * 100) : 0;
                ?>
                <div class="sent-bar-row">
                    <span class="sent-bar-label"><?= $meta['label'] ?></span>
                    <div class="sent-bar-track">
                        <div class="sent-bar-fill <?= $meta['color'] ?>"
                             style="width:<?= $pct ?>%"></div>
                    </div>
                    <span class="sent-bar-pct"><?= $pct ?>%</span>
                </div>
                <?php endforeach; ?>

                <hr style="border:0;border-top:1px solid var(--line);margin:16px 0;">
                <div style="display:flex;gap:18px;flex-wrap:wrap;">
                    <?php foreach ($sentiments as $key => $meta): ?>
                    <div>
                        <strong style="font-size:1.3rem;"><?= $sentiment_tally[$key] ?></strong>
                        <br><small style="color:var(--muted);"><?= $meta['label'] ?></small>
                    </div>
                    <?php endforeach; ?>
                </div>
            </div>
        </div>

        <!-- Negative messages -->
        <?php if (!empty($negative_list)): ?>
        <div class="section-title" style="font-size:1rem;color:var(--muted);margin-bottom:14px;">
            <span>⚠️ Negative Feedback Requiring Attention (<?= count($negative_list) ?>)</span>
        </div>
        <div class="neg-list" style="margin-bottom:32px;">
            <?php foreach ($negative_list as $fb): ?>
            <div class="neg-card">
                <div class="neg-card-meta">
                    <?= htmlspecialchars($fb['user_name'], ENT_QUOTES, 'UTF-8') ?>
                    &nbsp;·&nbsp;
                    <?= date('M j, Y', strtotime($fb['created_at'])) ?>
                </div>
                <div class="neg-card-msg">
                    "<?= htmlspecialchars($fb['message'], ENT_QUOTES, 'UTF-8') ?>"
                </div>
            </div>
            <?php endforeach; ?>
        </div>
        <?php endif; ?>

        <?php endif; // end if feedback exists ?>

    </div><!-- /admin-main -->
</div>

<script>
<?php if ($total_feedback > 0): ?>
// Sentiment donut chart
(function () {
    const ctx = document.getElementById('sentimentDonut').getContext('2d');
    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Neutral', 'Negative'],
            datasets: [{
                data: [
                    <?= (int)$sentiment_tally['positive'] ?>,
                    <?= (int)$sentiment_tally['neutral'] ?>,
                    <?= (int)$sentiment_tally['negative'] ?>
                ],
                backgroundColor: ['#0ea98b', '#a0aec0', '#ff6b6b'],
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            cutout: '65%',
            plugins: {
                legend: { position: 'bottom', labels: { boxWidth: 12, padding: 14 } },
                tooltip: {
                    callbacks: {
                        label: (ctx) => {
                            const total = ctx.dataset.data.reduce((a, b) => a + b, 0);
                            const pct   = total > 0 ? Math.round(ctx.raw / total * 100) : 0;
                            return ` ${ctx.raw} (${pct}%)`;
                        }
                    }
                }
            }
        }
    });
})();
<?php endif; ?>
</script>
</body>
</html>
