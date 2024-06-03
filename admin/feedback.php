<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser(['admin']);


$error = '';
$feedback_list = [];

try {
    $stmt = $pdo->query("SELECT f.*, u.name AS user_name 
                       FROM feedback f
                       JOIN users u ON f.user_id = u.user_id
                       ORDER BY f.created_at DESC");
    $feedback_list = $stmt->fetchAll();
} catch (PDOException $e) {
    error_log('Feedback fetch failed: ' . $e->getMessage());
    $error = "Unable to load feedback right now.";
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Patient Feedback - MediSync Admin</title>
    <link href="../assets/css/style.css" rel="stylesheet">
</head>
<body>
    <div class="admin-dashboard">
        <!-- Sidebar -->
        <div class="admin-sidebar">
            <h2>MediSync Admin</h2>
            <nav>
                <a href="dashboard.php" class="nav-link">Dashboard</a>
                <a href="doctors.php" class="nav-link">Manage Doctors</a>
                <a href="feedback.php" class="nav-link active">Patient Feedback</a>
                <a href="reports.php" class="nav-link">System Reports</a>
                <a href="logout.php" class="nav-link">Logout</a>
            </nav>
        </div>

        <div class="admin-main">
            <h1>Patient Feedback Management</h1>
            
            <?php if ($error): ?>
                <div class="alert error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
            <?php endif; ?>

            <div class="stat-card">
                <h2>Submitted Feedback</h2>
                
                <?php if (empty($feedback_list)): ?>
                    <p>No feedback submitted yet.</p>
                <?php else: ?>
                    <table class="feedback-table">
                        <thead>
                            <tr>
                                <th>User</th>
                                <th>Feedback</th>
                                <th>Date Submitted</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($feedback_list as $feedback): ?>
                            <tr>
                                <td><?= htmlspecialchars($feedback['user_name']) ?></td>
                                <td class="feedback-message"><?= htmlspecialchars($feedback['message']) ?></td>
                                <td class="feedback-date">
                                    <?= date('F j, Y, g:i a', strtotime($feedback['created_at'])) ?>
                                </td>
                            </tr>
                            <?php endforeach; ?>
                        </tbody>
                    </table>
                <?php endif; ?>
            </div>
        </div>
    </div>
</body>
</html>