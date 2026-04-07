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
    $user_id = $_SESSION['user_id'];
    $appointment_date = $_POST['appointment_date'];
    $description = trim($_POST['description']);

    // Validation
    if (empty($appointment_date)) {
        $error = "Please select a date and time";
    } elseif (strtotime($appointment_date) < time()) {
        $error = "Appointment date cannot be in the past";
    } elseif (empty($description)) {
        $error = "Please enter a description of your symptoms";
    }

    if (empty($error)) {
        try {
            $stmt = $pdo->prepare("INSERT INTO appointments 
                (user_id, doctor_id, appointment_date, description, status, assigned_by)
                VALUES (?, ?, ?, ?, 'pending', 'user')");
            
            $stmt->execute([
                $user_id,
                $doctor_id,
                $appointment_date,
                $description
            ]);

            $success = "Appointment booked successfully!";
            // Clear form inputs
            $description = '';
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
        h1 {
            margin-bottom: 2rem;
        }
        .alert {
            background: #f44336;
            color: white;
            padding: 10px;
            margin-bottom: 1rem;
            border-radius: 5px;
        }
        .success {
            background: #4CAF50;
        }
        .doctor-info {
            background: rgba(0, 0, 0, 0.5);
            padding: 10px;
            border-radius: 10px;
            margin-bottom: 1rem;
        }
        .doctor-info h3 {
            font-size: 1.5rem;
            font-weight: bold;
        }
        .doctor-info p {
            font-size: 1rem;
            font-weight: normal;
            margin: 5px 0;
        }
        form {
            background: rgba(0, 0, 0, 0.5);
            padding: 10px;
            border-radius: 10px;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        label {
            font-size: 1rem;
            font-weight: bold;
        }
        input, textarea {
            width: 70%;
            padding: 10px;
            font-size: 1rem;
            margin-top: 5px;
            border-radius: 10px;
            border: none;
        }
        textarea {
            height: 100px;
        }
        small {
            font-size: 0.8rem;
            color: #ccc;
        }
        .btn {
            padding: 10px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-right: 10px;
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
                    <div class="alert error"><?= $error ?></div>
                <?php endif; ?>
                
                <?php if ($success): ?>
                    <div class="alert success"><?= $success ?></div>
                <?php endif; ?>

                <?php if ($doctor): ?>
                    <div class="doctor-info">
                        <h3>Dr. <?= htmlspecialchars($doctor['name']) ?></h3>
                        <p>Specialization: <?= htmlspecialchars($doctor['specialization']) ?></p>
                        <p>Experience: <?= $doctor['experience'] ?> years</p>
                        <p>Contact: <?= htmlspecialchars($doctor['contact_details']) ?></p>
                    </div>

                    <form method="post">
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
                    <div class="alert error"><?= $error ?></div>
                    <a href="doctors.php" class="btn">Back to Doctors List</a>
                <?php endif; ?>
            </div>
        </div>
    </div>
</body>
</html>