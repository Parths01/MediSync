<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser();

$error = '';
$doctors = [];

try {
    $stmt = $pdo->query("SELECT * FROM doctors ORDER BY name");
    $doctors = $stmt->fetchAll();
} catch (PDOException $e) {
    error_log('User doctors fetch failed: ' . $e->getMessage());
    $error = "Unable to load doctors right now.";
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Our Doctors - MediSync</title>
    <link href="../assets/css/style.css" rel="stylesheet">
</head>
<body>
    <div class="dashboard-container">
        <!-- Sidebar -->
        <div class="user-sidebar">
            <h2>Welcome, <?= htmlspecialchars($_SESSION['name']) ?></h2>
            <nav>
                <a href="dashboard.php" class="nav-link">Dashboard</a>
                <a href="doctors.php" class="nav-link active">Book Appointment</a>
                <a href="contact.php" class="nav-link">Contact Us</a>
                <a href="profile.php" class="nav-link">My Profile</a>
                <a href="../auth/logout.php" class="nav-link">Logout</a>
            </nav>
        </div>

        <!-- Main Content -->
        <div class="user-main">
            <h1>Our Medical Specialists</h1>
            
            <?php if ($error): ?>
                <div class="alert error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
            <?php endif; ?>

            <?php if (empty($doctors)): ?>
                <div class="no-doctors">
                    <p>No doctors available at the moment. Please check back later.</p>
                </div>
            <?php else: ?>
                <div class="doctors-grid">
                    <?php foreach ($doctors as $doctor): ?>
                    <div class="doctor-card">
                        <?php if (!empty($doctor['photo'])): ?>
                            <img src="<?= htmlspecialchars($doctor['photo']) ?>" 
                                 alt="Dr. <?= htmlspecialchars($doctor['name']) ?>" 
                                 class="doctor-photo">
                        <?php else: ?>
                            <div class="doctor-photo" style="background: #f0f0f0;"></div>
                        <?php endif; ?>
                        
                        <div class="doctor-info">
                            <h3 class="doctor-name">
                                Dr. <?= htmlspecialchars($doctor['name']) ?>
                            </h3>
                            <div class="doctor-specialization">
                                <?= htmlspecialchars($doctor['specialization']) ?>
                            </div>
                            <div class="doctor-experience">
                                <?= htmlspecialchars((string) $doctor['experience'], ENT_QUOTES, 'UTF-8') ?>+ years experience
                            </div>
                            <div class="doctor-contact">
                                📞 <?= htmlspecialchars($doctor['contact_details']) ?>
                            </div>
                            <a href="book_appointment.php?doctor_id=<?= urlencode((string) $doctor['doctor_id']) ?>"
                               class="btn">
                                Book Appointment
                            </a>
                        </div>
                    </div>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>
        </div>
    </div>
</body>
</html>