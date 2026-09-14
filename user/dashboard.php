<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser();

$user_id = $_SESSION['user_id'];
$error = '';
$appointments = [];

try {
    $stmt = $pdo->prepare("SELECT a.*, d.name AS doctor_name, d.specialization, d.contact_details 
                         FROM appointments a
                         JOIN doctors d ON a.doctor_id = d.doctor_id
                         WHERE a.user_id = ? 
                         AND a.appointment_date >= CURDATE()
                         ORDER BY a.appointment_date ASC");
    $stmt->execute([$user_id]);
    $appointments = $stmt->fetchAll();
} catch (PDOException $e) {
    error_log('User dashboard appointment fetch failed: ' . $e->getMessage());
    $error = "Unable to load appointments right now.";
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Dashboard - MediSync</title>
    <link href="../assets/css/style.css" rel="stylesheet">
</head>
<body>
    <div class="dashboard-container">
        <!-- Sidebar -->
        <div class="user-sidebar">
            <h2>Welcome, <?= htmlspecialchars($_SESSION['name']) ?></h2>
            <nav>
                <a href="dashboard.php" class="nav-link active">Dashboard</a>
                <a href="doctors.php" class="nav-link">Book Appointment</a>
                <a href="contact.php" class="nav-link">Contact Us</a>
                <a href="profile.php" class="nav-link">My Profile</a>
                <a href="../auth/logout.php" class="nav-link">Logout</a>
            </nav>
        </div>

        <!-- Main Content -->
        <div class="user-main">
            <h1>Upcoming Appointments</h1>
            
            <?php if ($error): ?>
                <div class="alert error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
            <?php endif; ?>

            <?php if (empty($appointments)): ?>
                <div class="alert info">
                    No upcoming appointments. <a href="doctors.php">Book an appointment now!</a>
                </div>
            <?php else: ?>
                <div class="appointments-list">
                    <?php foreach ($appointments as $appt): ?>
                    <div class="appointment-card">
                        <div class="appointment-doctor">
                            Dr. <?= htmlspecialchars($appt['doctor_name']) ?> 
                            <span class="appointment-specialization">(<?= htmlspecialchars($appt['specialization']) ?>)</span>
                        </div>
                        <div class="appointment-time">
                            <?= date('F j, Y \a\t g:i A', strtotime($appt['appointment_date'])) ?>
                        </div>
                        <?php $status = preg_replace('/[^a-z]/', '', strtolower((string) $appt['status'])); ?>
                        <div class="appointment-status status-<?= htmlspecialchars($status, ENT_QUOTES, 'UTF-8') ?>">
                            <?= htmlspecialchars(ucfirst((string) $appt['status']), ENT_QUOTES, 'UTF-8') ?>
                        </div>
                        <?php if (!empty($appt['description'])): ?>
                        <div class="appointment-description">
                            <p><?= htmlspecialchars($appt['description']) ?></p>
                        </div>
                        <?php endif; ?>
                        <div class="appointment-contact">
                            Contact: <?= htmlspecialchars($appt['contact_details']) ?>
                        </div>
                    </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>
        </div>
    </div>
</body>
</html>