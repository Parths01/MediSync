<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser(['admin']);


$error = '';
$success = '';
$reports = [];

// Handle status change
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['action'], $_POST['id'])) {
    verify_csrf_token();
    $action = $_POST['action'];
    $contact_id = (int)$_POST['id'];
    
    try {
        if (!in_array($action, ['close', 'open'], true)) {
            $error = "Invalid report action.";
            $new_status = null;
        } else {
            $new_status = $action === 'close' ? 'closed' : 'open';
        }
        if ($new_status !== null) {
            $stmt = $pdo->prepare("UPDATE contact_messages SET status = ? WHERE contact_id = ?");
            $stmt->execute([$new_status, $contact_id]);
        }
        
        if ($new_status !== null && $stmt->rowCount() > 0) {
            $success = "Status updated successfully!";
        } else {
            $error = "No changes made. Message might not exist.";
        }
    } catch (PDOException $e) {
        error_log('Report status update failed: ' . $e->getMessage());
        $error = "Unable to update status right now.";
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
    error_log('Reports fetch failed: ' . $e->getMessage());
    $error = "Unable to load reports right now.";
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>System Reports - MediSync Admin</title>
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
                <a href="feedback.php" class="nav-link">Patient Feedback</a>
                <a href="reports.php" class="nav-link active">System Reports</a>
                <a href="logout.php" class="nav-link">Logout</a>
            </nav>
        </div>

        <div class="admin-main">
            <h1>User Inquiries & Reports</h1>
            
            <?php if ($error): ?>
                <div class="alert error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
            <?php endif; ?>
            
            <?php if ($success): ?>
                <div class="alert success"><?= htmlspecialchars($success, ENT_QUOTES, 'UTF-8') ?></div>
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
                                    <span class="status-badge status-<?= htmlspecialchars((string) $report['status'], ENT_QUOTES, 'UTF-8') ?>">
                                        <?= ucfirst($report['status']) ?>
                                    </span>
                                </td>
                                <td class="action-buttons">
                                    <?php if ($report['status'] === 'open'): ?>
                                        <form method="post" style="display:inline">
                                            <?= csrf_field() ?>
                                            <input type="hidden" name="action" value="close">
                                            <input type="hidden" name="id" value="<?= $report['contact_id'] ?>">
                                            <button type="submit" class="btn btn-sm danger">Close</button>
                                        </form>
                                    <?php else: ?>
                                        <form method="post" style="display:inline">
                                            <?= csrf_field() ?>
                                            <input type="hidden" name="action" value="open">
                                            <input type="hidden" name="id" value="<?= $report['contact_id'] ?>">
                                            <button type="submit" class="btn btn-sm success">Reopen</button>
                                        </form>
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