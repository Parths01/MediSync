<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser();

$doctor_id = $_GET['doctor_id'] ?? null;
$error = '';
$success = '';
$doctor = [];

// Fetch doctor details
try {
    if (!$doctor_id) {
        header("Location: doctors.php");
        exit();
    }

    $stmt = $pdo->prepare("SELECT * FROM doctors WHERE doctor_id = ?");
    $stmt->execute([$doctor_id]);
    $doctor = $stmt->fetch();

    if (!$doctor) {
        $error = "Doctor not found";
    }
} catch (PDOException $e) {
    error_log('Book appointment doctor fetch failed: ' . $e->getMessage());
    $error = "Unable to load doctor details right now.";
}

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    verify_csrf_token();
    $user_id = $_SESSION['user_id'];
    $appointment_date = $_POST['appointment_date'];
    $description = trim($_POST['description']);

    // Validation
    if (empty($appointment_date)) {
        $error = "Please select a date and time";
    } elseif (!DateTime::createFromFormat('Y-m-d\TH:i', $appointment_date) ||
        DateTime::createFromFormat('Y-m-d\TH:i', $appointment_date)->getTimestamp() <= time()) {
        $error = "Appointment date cannot be in the past";
    } elseif (empty($description)) {
        $error = "Please enter a description of your symptoms";
    }

    if (empty($error)) {
        try {
            $stmt = $pdo->prepare("SELECT doctor_id FROM doctors WHERE doctor_id = ?");
            $stmt->execute([(int) $doctor_id]);
            if (!$stmt->fetch()) {
                $error = "Doctor not found";
            }
            $appointment = DateTime::createFromFormat('Y-m-d\TH:i', $appointment_date);
            $stmt = $pdo->prepare("SELECT appointment_id FROM appointments
                WHERE doctor_id = ? AND appointment_date = ?
                AND status IN ('pending', 'confirmed')");
            $stmt->execute([(int) $doctor_id, $appointment->format('Y-m-d H:i:s')]);
            if ($stmt->fetch()) {
                $error = "That appointment time is already booked";
            }
            if (empty($error)) {
                $stmt = $pdo->prepare("INSERT INTO appointments
                (user_id, doctor_id, appointment_date, description, status, assigned_by)
                VALUES (?, ?, ?, ?, 'pending', 'user')");
            
                $stmt->execute([
                $user_id,
                $doctor_id,
                $appointment->format('Y-m-d H:i:s'),
                $description
                ]);

                $success = "Appointment booked successfully!";
                $description = '';
            }
        } catch (PDOException $e) {
            error_log('Appointment booking failed: ' . $e->getMessage());
            $error = "Unable to book appointment right now.";
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Book Appointment - MediSync</title>
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
            <div class="booking-container">
                <h1>Book Appointment</h1>
                
                <?php if ($error): ?>
                    <div class="alert error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
                <?php endif; ?>
                
                <?php if ($success): ?>
                    <div class="alert success"><?= htmlspecialchars($success, ENT_QUOTES, 'UTF-8') ?></div>
                <?php endif; ?>

                <?php if ($doctor): ?>
                    <div class="doctor-info">
                        <h3>Dr. <?= htmlspecialchars($doctor['name']) ?></h3>
                        <p>Specialization: <?= htmlspecialchars($doctor['specialization']) ?></p>
                        <p>Experience: <?= htmlspecialchars((string) $doctor['experience'], ENT_QUOTES, 'UTF-8') ?> years</p>
                        <p>Contact: <?= htmlspecialchars($doctor['contact_details']) ?></p>
                    </div>

                    <form method="post">
                        <?= csrf_field() ?>
                        <div class="form-group">
                            <label>Appointment Date & Time:</label>
                            <input type="datetime-local" name="appointment_date" 
                                   min="<?= date('Y-m-d\TH:i') ?>" required>
                        </div>

                        <div class="form-group">
                            <label>Description of Symptoms:</label>
                            <textarea name="description" required><?= htmlspecialchars($description ?? '') ?></textarea>
                            <br>
                            <small>Please describe your symptoms and any important details</small>
                        </div>

                        <div class="form-group">
                            <button type="submit" class="btn">Book Appointment</button>
                            <a href="doctors.php" class="btn">Cancel</a>
                        </div>
                    </form>
                <?php else: ?>
                    <div class="alert error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
                    <a href="doctors.php" class="btn">Back to Doctors List</a>
                <?php endif; ?>
            </div>
        </div>
    </div>
</body>
</html>