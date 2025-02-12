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
    $error = "Error fetching doctors: " . $e->getMessage();
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Our Doctors - MediSync</title>
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
        .user-main {
            width: 80%;
            margin-left: 20%;
            padding: 20px;
        }
        h1 {
        
            margin-bottom: 2rem;
        }
        .alert {
            background: #f44336;
            color: white;
            padding: 1rem;
            margin-bottom: 1rem;
        }
        .no-doctors {
            text-align: center;
            font-size: 1.5rem;
            margin-top: 2rem;
        }
        .doctors-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        .doctor-card {
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            padding: 20px;
            display: flex;
            gap: 20px;
        }
        .doctor-photo {
            width: 100px;
            height: 100px;
            border-radius: 50%;
            object-fit: cover;
        }
        .doctor-info {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        .doctor-name {
            font-size: 1.5rem;
            font-weight: bold;
        }
        .doctor-specialization {
            font-size: 1.2rem;
        }
        .doctor-experience {
            font-size: 1rem;
        }
        .doctor-contact {
            font-size: 1rem;
        }
        .btn {
            padding: 10px 20px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            text-align: center;
            transition: 0.5s;
        }
        .btn:hover {
            background: #0056b3;
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
            <h1>Our Medical Specialists</h1>
            
            <?php if ($error): ?>
                <div class="alert error"><?= $error ?></div>
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
                                <?= $doctor['experience'] ?>+ years experience
                            </div>
                            <div class="doctor-contact">
                                📞 <?= htmlspecialchars($doctor['contact_details']) ?>
                            </div>
                            <a href="book_appointment.php?doctor_id=<?= $doctor['doctor_id'] ?>" 
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