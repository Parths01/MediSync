<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';


$error = '';
$success = '';
$reports = [];

// Handle status change
if (isset($_GET['action']) && isset($_GET['id'])) {
    $action = $_GET['action'];
    $contact_id = (int)$_GET['id'];
    
    try {
        $new_status = $action === 'close' ? 'closed' : 'open';
        $stmt = $pdo->prepare("UPDATE contact_messages SET status = ? WHERE contact_id = ?");
        $stmt->execute([$new_status, $contact_id]);
        
        if ($stmt->rowCount() > 0) {
            $success = "Status updated successfully!";
        } else {
            $error = "No changes made. Message might not exist.";
        }
    } catch (PDOException $e) {
        $error = "Error updating status: " . $e->getMessage();
    }
}

// Fetch all contact messages
try {
    $stmt = $pdo->query("SELECT cm.*, u.name AS user_name 
                       FROM contact_messages cm
                       JOIN users u ON cm.user_id = u.user_id
                       ORDER BY cm.created_at DESC");
    $reports = $stmt->fetchAll();
} catch (PDOException $e) {
    $error = "Error fetching reports: " . $e->getMessage();
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>System Reports - MediSync Admin</title>
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
        .status-badge {
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.875rem;
            display: inline-block;
        }
        .status-open { background: #d4edda; color: #155724; }
        .status-closed { background: #f8d7da; color: #721c24; }
        .action-buttons a {
            margin: 0 0.25rem;
            padding: 0.25rem 0.5rem;
            font-size: 0.875rem;
        }
        .message-content {
            max-width: 500px;
            word-wrap: break-word;
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

        .success {
            background-color: #d4edda;
            color: #155724;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }

        th, td {
            padding: 1rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }

        th {
            background-color: #333;
            border-top: 1px solid #333;
        }

        tr:hover {
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
                <a href="dashboard.php" class="nav-link">Dashboard</a>
                <a href="doctors.php" class="nav-link">Manage Doctors</a>
                <a href="feedback.php" class="nav-link">Patient Feedback</a>
                <a href="reports.php" class="nav-link active">System Reports</a>
                <a href="logout.php" class="nav-link">Logout</a>
            </nav>
        </div>

        <div class="admin-main">
            <h1>User Inquiries & Reports</h1>
            
            <?php if ($error): ?>
                <div class="alert error"><?= $error ?></div>
            <?php endif; ?>
            
            <?php if ($success): ?>
                <div class="alert success"><?= $success ?></div>
            <?php endif; ?>

            <div class="stat-card">
                <?php if (empty($reports)): ?>
                    <p>No inquiries found.</p>
                <?php else: ?>
                    <table>
                        <thead>
                            <tr>
                                <th>User</th>
                                <th>Message</th>
                                <th>Date</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            <?php foreach ($reports as $report): ?>
                            <tr>
                                <td><?= htmlspecialchars($report['user_name']) ?></td>
                                <td class="message-content"><?= htmlspecialchars($report['message']) ?></td>
                                <td><?= date('M j, Y H:i', strtotime($report['created_at'])) ?></td>
                                <td>
                                    <span class="status-badge status-<?= $report['status'] ?>">
                                        <?= ucfirst($report['status']) ?>
                                    </span>
                                </td>
                                <td class="action-buttons">
                                    <?php if ($report['status'] === 'open'): ?>
                                        <a href="reports.php?action=close&id=<?= $report['contact_id'] ?>" 
                                           class="btn btn-sm danger">Close</a>
                                    <?php else: ?>
                                        <a href="reports.php?action=open&id=<?= $report['contact_id'] ?>" 
                                           class="btn btn-sm success">Reopen</a>
                                    <?php endif; ?>
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