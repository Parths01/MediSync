<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser();

$user_id = $_SESSION['user_id'];
$error = '';
$success = '';
$appointments = [];
$medical_history = [];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $diagnosis = trim($_POST['diagnosis'] ?? '');
    $treatment = trim($_POST['treatment'] ?? '');
    $notes = trim($_POST['notes'] ?? '');
    $recorded_at = $_POST['recorded_at'] ?? '';

    if ($diagnosis === '' || $recorded_at === '') {
        $error = 'Diagnosis and record date are required.';
    } else {
        try {
            $stmt = $pdo->prepare(
                'INSERT INTO medical_history (user_id, diagnosis, treatment, notes, recorded_at)
                 VALUES (?, ?, ?, ?, ?)'
            );
            $stmt->execute([$user_id, $diagnosis, $treatment, $notes, $recorded_at]);
            $success = 'Medical history entry added.';
        } catch (PDOException $e) {
            error_log('Medical history insert failed: ' . $e->getMessage());
            $error = 'Unable to save medical history right now.';
        }
    }
}

try {
    $stmt = $pdo->prepare(
        'SELECT a.*, d.name AS doctor_name, d.specialization
         FROM appointments a
         JOIN doctors d ON a.doctor_id = d.doctor_id
         WHERE a.user_id = ? AND (a.appointment_date < NOW() OR a.status = \'completed\')
         ORDER BY a.appointment_date DESC'
    );
    $stmt->execute([$user_id]);
    $appointments = $stmt->fetchAll();

    $stmt = $pdo->prepare(
        'SELECT diagnosis, treatment, notes, recorded_at
         FROM medical_history
         WHERE user_id = ?
         ORDER BY recorded_at DESC, history_id DESC'
    );
    $stmt->execute([$user_id]);
    $medical_history = $stmt->fetchAll();
} catch (PDOException $e) {
    error_log('History fetch failed: ' . $e->getMessage());
    $error = 'Unable to load history right now.';
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>My History - MediSync</title>
    <link href="../assets/css/style.css" rel="stylesheet">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; color: white; background: #173b57; }
        .dashboard-container { display: flex; min-height: 100vh; }
        .user-sidebar { width: 15%; min-width: 180px; padding: 20px; background: rgba(0, 0, 0, 0.5); position: fixed; height: 100vh; }
        .nav-link { display: block; color: white; text-decoration: none; padding: 10px 0; margin-bottom: 10px; }
        .nav-link:hover, .nav-link.active { background: white; color: black; border-radius: 0 20px 20px 0; }
        .user-main { width: 80%; margin-left: 20%; padding: 24px; }
        .history-section { background: rgba(0, 0, 0, 0.4); padding: 20px; margin-bottom: 20px; border-radius: 10px; }
        .history-entry { border-bottom: 1px solid rgba(255,255,255,.3); padding: 12px 0; }
        .history-entry:last-child { border-bottom: 0; }
        label { display: block; margin: 10px 0 5px; font-weight: bold; }
        input, textarea { width: 95%; padding: 9px; border-radius: 4px; border: 1px solid #ccc; }
        textarea { min-height: 70px; }
        .btn { margin-top: 14px; padding: 10px 18px; border: 0; border-radius: 4px; cursor: pointer; }
        .alert { padding: 10px; margin-bottom: 16px; background: #b52b37; }
        .success { background: #287d46; }
        .muted { opacity: .75; }
    </style>
</head>
<body>
<div class="dashboard-container">
    <aside class="user-sidebar">
        <h2>Welcome, <?= htmlspecialchars($_SESSION['name']) ?></h2>
        <nav>
            <a href="dashboard.php" class="nav-link">Dashboard</a>
            <a href="history.php" class="nav-link active">My History</a>
            <a href="doctors.php" class="nav-link">Book Appointment</a>
            <a href="contact.php" class="nav-link">Contact Us</a>
            <a href="profile.php" class="nav-link">My Profile</a>
            <a href="../auth/logout.php" class="nav-link">Logout</a>
        </nav>
    </aside>

    <main class="user-main">
        <h1>My Health History</h1>
        <?php if ($error): ?><div class="alert"><?= htmlspecialchars($error) ?></div><?php endif; ?>
        <?php if ($success): ?><div class="alert success"><?= htmlspecialchars($success) ?></div><?php endif; ?>

        <section class="history-section">
            <h2>Past Appointments</h2>
            <?php if (!$appointments): ?>
                <p class="muted">No past appointments found.</p>
            <?php else: ?>
                <?php foreach ($appointments as $appointment): ?>
                    <div class="history-entry">
                        <strong>Dr. <?= htmlspecialchars($appointment['doctor_name']) ?></strong>
                        <span>(<?= htmlspecialchars($appointment['specialization']) ?>)</span>
                        <div><?= date('F j, Y g:i A', strtotime($appointment['appointment_date'])) ?></div>
                        <div>Status: <?= htmlspecialchars(ucfirst($appointment['status'])) ?></div>
                        <?php if (!empty($appointment['description'])): ?>
                            <div><?= htmlspecialchars($appointment['description']) ?></div>
                        <?php endif; ?>
                    </div>
                <?php endforeach; ?>
            <?php endif; ?>
        </section>

        <section class="history-section">
            <h2>Medical History</h2>
            <?php if (!$medical_history): ?>
                <p class="muted">No medical history entries found.</p>
            <?php else: ?>
                <?php foreach ($medical_history as $entry): ?>
                    <div class="history-entry">
                        <strong><?= htmlspecialchars($entry['diagnosis']) ?></strong>
                        <div>Recorded: <?= date('F j, Y', strtotime($entry['recorded_at'])) ?></div>
                        <?php if (!empty($entry['treatment'])): ?><div>Treatment: <?= htmlspecialchars($entry['treatment']) ?></div><?php endif; ?>
                        <?php if (!empty($entry['notes'])): ?><div>Notes: <?= htmlspecialchars($entry['notes']) ?></div><?php endif; ?>
                    </div>
                <?php endforeach; ?>
            <?php endif; ?>
        </section>

        <section class="history-section">
            <h2>Add Medical History</h2>
            <form method="post">
                <label for="diagnosis">Diagnosis</label>
                <input id="diagnosis" name="diagnosis" required maxlength="255">
                <label for="treatment">Treatment</label>
                <textarea id="treatment" name="treatment"></textarea>
                <label for="notes">Notes</label>
                <textarea id="notes" name="notes"></textarea>
                <label for="recorded_at">Record date</label>
                <input id="recorded_at" type="date" name="recorded_at" required max="<?= date('Y-m-d') ?>">
                <button class="btn" type="submit">Save Entry</button>
            </form>
        </section>
    </main>
</div>
</body>
</html>
