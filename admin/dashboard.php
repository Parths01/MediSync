<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser(['admin']);

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
                                <span class="status-badge <?= htmlspecialchars((string) $appointment['status'], ENT_QUOTES, 'UTF-8') ?>">
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