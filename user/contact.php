<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser();

$error = '';
$success = '';

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    verify_csrf_token();
    $user_id = $_SESSION['user_id'];
    $message = trim($_POST['message']);

    // Validation
    if (empty($message)) {
        $error = "Please enter your message";
    } elseif (strlen($message) < 10) {
        $error = "Message must be at least 10 characters";
    }

    if (empty($error)) {
        try {
            $stmt = $pdo->prepare("INSERT INTO contact_messages 
                (user_id, message) 
                VALUES (?, ?)");
            $stmt->execute([$user_id, $message]);
            
            $success = "Your message has been sent successfully!";
            // Clear form input
            $message = '';
        } catch (PDOException $e) {
            error_log('Contact message submit failed: ' . $e->getMessage());
            $error = "Unable to send your message right now.";
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Contact Us - MediSync</title>
    <link href="../assets/css/style.css" rel="stylesheet">
</head>
<body>
    <div class="dashboard-container">
        <!-- Sidebar -->
        <div class="user-sidebar">
            <h2>Welcome, <?= htmlspecialchars($_SESSION['name']) ?></h2>
            <nav>
                <a href="dashboard.php" class="nav-link">Dashboard</a>
                <a href="doctors.php" class="nav-link">Book Appointment</a>
                <a href="contact.php" class="nav-link active">Contact Us</a>
                <a href="profile.php" class="nav-link">My Profile</a>
                <a href="../auth/logout.php" class="nav-link">Logout</a>
            </nav>
        </div>

        <!-- Main Content -->
        <div class="user-main">
            <div class="contact-container">
                <h1>Contact Us</h1>
                
                <?php if ($error): ?>
                    <div class="alert error"><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></div>
                <?php endif; ?>
                
                <?php if ($success): ?>
                    <div class="alert success"><?= htmlspecialchars($success, ENT_QUOTES, 'UTF-8') ?></div>
                <?php endif; ?>

                <div class="contact-info">
                    <h3>Our Contact Information</h3>
                    <p><strong>Address:</strong> 123 Medical Street, Health City, HC 12345</p>
                    <p><strong>Phone:</strong> +91 860029XXXX</p>
                    <p><strong>Email:</strong> parths001@proton.me</p>
                    <p><strong>Office Hours:</strong> Mon-Fri 9:00 AM - 5:00 PM</p>
                </div>

                <form method="post">
                    <?= csrf_field() ?>
                    <div class="form-group">
                        <label>Your Message:</label>
                        <textarea name="message" required><?= htmlspecialchars($message ?? '') ?></textarea>
                        <br><br>
                        <small>Please describe your inquiry or issue in detail</small>
                    </div>

                    <div class="form-group">
                        <button type="submit" class="btn">Send Message</button>
                    </div>
                </form>
            </div>
        </div>
    </div>
</body>
</html>