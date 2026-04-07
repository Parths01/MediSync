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
    <style>
        body{
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            color: white;
            box-sizing: border-box;
            background-image: url('../assets/image/wave.png');
            background-repeat: no-repeat;
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            justify-items: center;
            margin-bottom: 10px;
        }
        .dashboard-container {
            display: flex;
            width: 100%;
            height: 100vh;
        }
        .user-sidebar {
            width: 15%;
            height: 100%;
            padding: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
            position: fixed;
        }
        .user-sidebar h2 {
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .user-sidebar nav {
            display: flex;
            flex-direction: column;
        }
        .nav-link {
            color: white;
            text-decoration: none;
            padding: 10px 0;
            margin-bottom: 10px;
        }
        .nav-link:hover, .nav-link.active {
            background-color: white;
            border-radius: 0 20px 20px 0px;
            font-weight: bold;
            color: black;
            transition: 0.5s;
        }
        .nav-link.active {
            font-weight: bold;
        }
        .user-main {
            width: 80%;
            height: 100%;
            padding: 10px;
            margin-left: 20%;
        }
        .appointment-card {
            width: 30%;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            padding: 10px;
            margin-bottom: 10px;
        }
        .appointment-doctor {
            font-size: 1.5rem;
            font-weight: bold;
        }
        .appointment-specialization {
            font-size: 1rem;
            font-weight: normal;
        }
        .appointment-time {
            font-size: 1rem;
            font-weight: bold;
            margin-top: 5px;
        }
        .appointment-status {
            font-size: 1rem;
            font-weight: bold;
            text-transform: uppercase;
            padding: 5px 10px;
            border-radius: 5px;
            margin-top: 5px;
        }
        .status-confirmed {
            background-color: #28a745;
        }
        .status-pending {
            background-color: #ffc107;
        }
        
    </style>
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
                <div class="alert error"><?= $error ?></div>
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
                        <div class="appointment-status status-<?= $appt['status'] ?>">
                            <?= ucfirst($appt['status']) ?>
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