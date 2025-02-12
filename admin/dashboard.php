<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';

// Get statistics
$stmt = $pdo->query("SELECT COUNT(*) AS total_users FROM users");
$total_users = $stmt->fetch()['total_users'];

$stmt = $pdo->query("SELECT COUNT(*) AS total_appointments FROM appointments");
$total_appointments = $stmt->fetch()['total_appointments'];

$stmt = $pdo->prepare("SELECT COUNT(*) AS new_users FROM users 
                      WHERE registration_date > DATE_SUB(NOW(), INTERVAL 30 DAY)");
$stmt->execute();
$new_users = $stmt->fetch()['new_users'];

$stmt = $pdo->query("SELECT COUNT(*) AS pending_appointments FROM appointments 
                    WHERE status = 'pending'");
$pending_appointments = $stmt->fetch()['pending_appointments'];

// Get recent appointments
$stmt = $pdo->query("SELECT a.*, u.name AS patient_name, d.name AS doctor_name
                    FROM appointments a
                    JOIN users u ON a.user_id = u.user_id
                    JOIN doctors d ON a.doctor_id = d.doctor_id
                    ORDER BY a.appointment_date DESC
                    LIMIT 10");
$recent_appointments = $stmt->fetchAll();
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Admin Dashboard - MediSync</title>
    <link href="../assets/css/style.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
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
        .admin-dashboard {
            display: flex;
            width: 100%;
            height: 100vh;
        }
        .admin-sidebar {
            width: 15%;
            height: 100%;
            padding: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
            position: fixed;
        }
        .admin-sidebar h2 {
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .admin-sidebar nav {
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
        .admin-main {
            width: 80%;
            height: 100%;
            padding: 10px;
            margin-left: 20%;
        }
        .admin-main h1 {
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .status-badge {
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
        }
        .status-badge.pending {
            background-color: #f39c12;
        }
        .status-badge.approved {
            background-color: #28a745;
        }
        .status-badge.rejected {
            background-color: #dc3545;
        }
        .status-badge.completed {
            background-color: #007bff;
        }
        .status-badge.cancelled {
            background-color: #6c757d;
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
            margin-bottom: 20px;
        }
        .stat-card {
            padding: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
        }
        .stat-card h3 {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .stat-number {
            font-size: 1.5rem;
            font-weight: bold;
        }
        .chart-container {
            margin-bottom: 20px;
            width: 30%;
            margin: 0 auto;
        }

        .recent-appointments {
            background-color: #333;
            padding: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
        }
        .recent-appointments h2 {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .recent-appointments table {
            width: 100%;
            border-collapse: collapse;
        }
        .recent-appointments table thead {
            background-color: #333;
        }
        .recent-appointments table th, .recent-appointments table td {
            padding: 10px;
            border: 1px solid white;
            text-align: left;
        }
        .recent-appointments table th {
            color: white;
        }
        .recent-appointments table tbody tr:nth-child(even) {
            background-color: rgba(255, 255, 255, 0.1);
        }
    </style>
</head>
<body>
    <div class="admin-dashboard">
        <!-- Sidebar -->
        <div class="admin-sidebar">
            <h2>MediSync Admin</h2>
            <nav>
                <a href="dashboard.php" class="nav-link active">Dashboard</a>
                <a href="doctors.php" class="nav-link">Manage Doctors</a>
                <a href="feedback.php" class="nav-link">Patient Feedback</a>
                <a href="reports.php" class="nav-link">System Reports</a>
                <a href="logout.php" class="nav-link">Logout</a>
            </nav>
        </div>

        <!-- Main Content -->
        <div class="admin-main">
            <h1>Admin Dashboard</h1>
            
            <!-- Statistics Grid -->
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>Total Users</h3>
                    <p class="stat-number"><?= $total_users ?></p>
                </div>
                <div class="stat-card">
                    <h3>Total Appointments</h3>
                    <p class="stat-number"><?= $total_appointments ?></p>
                </div>
                <div class="stat-card">
                    <h3>New Users (30d)</h3>
                    <p class="stat-number"><?= $new_users ?></p>
                </div>
                <div class="stat-card">
                    <h3>Pending Appointments</h3>
                    <p class="stat-number"><?= $pending_appointments ?></p>
                </div>
            </div>

            <!-- Pie Chart -->
            <div class="chart-container">
                <canvas id="usersChart"></canvas>
            </div>

            <!-- Recent Appointments -->
            <div class="recent-appointments">
                <h2>Recent Appointments</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Patient</th>
                            <th>Doctor</th>
                            <th>Date</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($recent_appointments as $appointment): ?>
                        <tr>
                            <td><?= htmlspecialchars($appointment['patient_name']) ?></td>
                            <td>Dr. <?= htmlspecialchars($appointment['doctor_name']) ?></td>
                            <td><?= date('M j, Y', strtotime($appointment['appointment_date'])) ?></td>
                            <td>
                                <span class="status-badge <?= $appointment['status'] ?>">
                                    <?= ucfirst($appointment['status']) ?>
                                </span>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
            <br>
            <br>
        </div>
    </div>

    <script>
        // Users Chart
        const ctx = document.getElementById('usersChart').getContext('2d');
        new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['New Users', 'Existing Users'],
                datasets: [{
                    data: [<?= $new_users ?>, <?= $total_users - $new_users ?>],
                    backgroundColor: ['#4e73df', '#1cc88a']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' },
                    title: {
                        display: true,
                        text: 'User Distribution (Last 30 Days)'
                    }
                }
            }
        });
    </script>
</body>
</html>