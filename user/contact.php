<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser();

$error = '';
$success = '';

// Handle form submission
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
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
        .contact-container {
            background: rgba(0, 0, 0, 0.5);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
        }
        .contact-container h1 {
            margin-bottom: 1rem;
        }
        .alert {
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 5px;
        }
        .error {
            background: #f44336;
            color: white;
        }
        .success {
            background: #4CAF50;
            color: white;
        }
        .contact-info {
            margin-bottom: 1rem;
        }
        .contact-info p {
            margin-bottom: 0.5rem;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        label {
            font-size: 1.2rem;
            font-weight: bold;
        }
        textarea {
            width: 80%;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #ccc;
            font-size: 1rem;
        }
        .btn {
            padding: 10px 20px;
            font-size: 1rem;
            font-weight: bold;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .btn:hover {
            background: #45a049;
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
                    <div class="alert error"><?= $error ?></div>
                <?php endif; ?>
                
                <?php if ($success): ?>
                    <div class="alert success"><?= $success ?></div>
                <?php endif; ?>

                <div class="contact-info">
                    <h3>Our Contact Information</h3>
                    <p><strong>Address:</strong> 123 Medical Street, Health City, HC 12345</p>
                    <p><strong>Phone:</strong> +91 860029XXXX</p>
                    <p><strong>Email:</strong> parths001@proton.me</p>
                    <p><strong>Office Hours:</strong> Mon-Fri 9:00 AM - 5:00 PM</p>
                </div>

                <form method="post">
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