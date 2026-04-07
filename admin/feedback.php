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
            margin-left: 20%;
            padding: 20px;
            width: 80%;
        }
        .admin-main h1 {
            margin-bottom: 1rem;
        }
        .alert {
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 5px;
        }
        .error {
            background-color: #f8d7da;
            color: #721c24;
        }
        .feedback-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        .feedback-table th, 
        .feedback-table td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        .feedback-table th {
            background-color:;
        }
        .feedback-message {
            max-width: 500px;
            word-wrap: break-word;
        }
        .feedback-date {
            white-space: nowrap;
        }
    </style>
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
                <div class="alert error"><?= $error ?></div>
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