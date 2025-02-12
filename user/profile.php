<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser();

$user_id = $_SESSION['user_id'];
$error = '';
$success = '';
$user_data = [];
$feedback_error = '';
$feedback_success = '';

// Fetch user data
try {
    $stmt = $pdo->prepare("SELECT * FROM users WHERE user_id = ?");
    $stmt->execute([$user_id]);
    $user_data = $stmt->fetch();
} catch (PDOException $e) {
    $error = "Error fetching profile data: " . $e->getMessage();
}

// Handle profile update
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['update_profile'])) {
    $name = trim($_POST['name']);
    $dob = $_POST['dob'];
    $gender = $_POST['gender'];
    $age = (int)$_POST['age'];
    $contact = trim($_POST['contact']);
    $blood_group = $_POST['blood_group'];
    $password = $_POST['password'];

    // Validation
    $errors = [];
    if (empty($name)) $errors[] = "Name is required";
    if (empty($dob)) $errors[] = "Date of Birth is required";
    if (!in_array($gender, ['Male', 'Female', 'Other'])) $errors[] = "Invalid gender";
    if ($age < 1 || $age > 120) $errors[] = "Invalid age";
    if (empty($contact)) $errors[] = "Contact number is required";
    if (empty($blood_group)) $errors[] = "Blood group is required";

    if (empty($errors)) {
        try {
            // Update query
            $query = "UPDATE users SET 
                name = ?,
                dob = ?,
                gender = ?,
                age = ?,
                contact = ?,
                blood_group = ?";
            
            $params = [$name, $dob, $gender, $age, $contact, $blood_group];

            // Add password update if provided
            if (!empty($password)) {
                if (strlen($password) < 8) {
                    $errors[] = "Password must be at least 8 characters";
                } else {
                    $query .= ", password = ?";
                    $params[] = password_hash($password, PASSWORD_DEFAULT);
                }
            }

            $query .= " WHERE user_id = ?";
            $params[] = $user_id;

            $stmt = $pdo->prepare($query);
            $stmt->execute($params);

            // Update session name
            $_SESSION['name'] = $name;
            $success = "Profile updated successfully!";
            
            // Refresh user data
            $stmt = $pdo->prepare("SELECT * FROM users WHERE user_id = ?");
            $stmt->execute([$user_id]);
            $user_data = $stmt->fetch();

        } catch (PDOException $e) {
            $error = "Error updating profile: " . $e->getMessage();
        }
    } else {
        $error = implode("<br>", $errors);
    }
}

// Handle feedback submission
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['submit_feedback'])) {
    $message = trim($_POST['message']);

    if (empty($message)) {
        $feedback_error = "Please enter your feedback message";
    } else {
        try {
            $stmt = $pdo->prepare("INSERT INTO feedback (user_id, message) VALUES (?, ?)");
            $stmt->execute([$user_id, $message]);
            $feedback_success = "Thank you for your feedback!";
        } catch (PDOException $e) {
            $feedback_error = "Error submitting feedback: " . $e->getMessage();
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>My Profile - MediSync</title>
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
        }
        .success {
            background: #4CAF50;
        }
        .form-section {
            background: rgba(0, 0, 0, 0.5);
            padding: 20px;
            width: 90%;
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .form-group {
            margin-bottom: 1rem;
        }
        .form-group label {
            display: block;
            font-weight: bold;
            margin-bottom: 5px;
        }
        .form-group input, .form-group select {
            width: 80%;
            padding: 10px;
            font-size: 1rem;
            border: 1px solid #ccc;
            border-radius: 5px;
        }
        .form-row {
            display: flex;
            justify-content: space-between;
        }
        .btn {
            padding: 10px 20px;
            background: #4CAF50;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1rem;
        }
        .btn:hover {
            background: #45a049;
        }
        .feedback-section {
            background: rgba(0, 0, 0, 0.5);
            padding: 20px;
            border-radius: 10px;
            width: 50%;
        }
        .profile-info {
            margin-top: 2rem;
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
                <a href="profile.php" class="nav-link active">My Profile</a>
                <a href="../auth/logout.php" class="nav-link">Logout</a>
            </nav>
        </div>

        <!-- Main Content -->
        <div class="user-main">
            <h1>My Profile</h1>
            
            <?php if ($error): ?>
                <div class="alert error"><?= $error ?></div>
            <?php endif; ?>
            <?php if ($success): ?>
                <div class="alert success"><?= $success ?></div>
            <?php endif; ?>

            <div class="profile-section">
                <!-- Profile Update Form -->
                <div class="form-section">
                    <h2>Edit Profile</h2>
                    <form method="post">
                        <div class="form-group">
                            <label>Full Name:</label>
                            <input type="text" name="name" required 
                                   value="<?= htmlspecialchars($user_data['name'] ?? '') ?>">
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Date of Birth:</label>
                                <input type="date" name="dob" required 
                                       value="<?= htmlspecialchars($user_data['dob'] ?? '') ?>">
                            </div>
                            <div class="form-group">
                                <label>Gender:</label>
                                <select name="gender" required>
                                    <option value="Male" <?= ($user_data['gender'] ?? '') === 'Male' ? 'selected' : '' ?>>Male</option>
                                    <option value="Female" <?= ($user_data['gender'] ?? '') === 'Female' ? 'selected' : '' ?>>Female</option>
                                    <option value="Other" <?= ($user_data['gender'] ?? '') === 'Other' ? 'selected' : '' ?>>Other</option>
                                </select>
                            </div>
                        </div>

                        <div class="form-row">
                            <div class="form-group">
                                <label>Age:</label>
                                <input type="number" name="age" min="1" max="120" required 
                                       value="<?= htmlspecialchars($user_data['age'] ?? '') ?>">
                            </div>
                            <div class="form-group">
                                <label>Blood Group:</label>
                                <select name="blood_group" required>
                                    <?php
                                    $blood_groups = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
                                    foreach ($blood_groups as $bg) {
                                        $selected = ($user_data['blood_group'] ?? '') === $bg ? 'selected' : '';
                                        echo "<option value='$bg' $selected>$bg</option>";
                                    }
                                    ?>
                                </select>
                            </div>
                        </div>

                        <div class="form-group">
                            <label>Contact Number:</label>
                            <input type="tel" name="contact" required 
                                   value="<?= htmlspecialchars($user_data['contact'] ?? '') ?>">
                        </div>

                        <div class="form-group">
                            <label>New Password (leave blank to keep current):</label>
                            <input type="password" name="password">
                        </div>

                        <button type="submit" name="update_profile" class="btn">Update Profile</button>
                    </form>
                </div>

                <!-- Feedback Section -->
                <div class="feedback-section">
                    <h2>Send Feedback</h2>
                    <?php if ($feedback_error): ?>
                        <div class="alert error"><?= $feedback_error ?></div>
                    <?php endif; ?>
                    <?php if ($feedback_success): ?>
                        <div class="alert success"><?= $feedback_success ?></div>
                    <?php endif; ?>
                    
                    <form method="post">
                        <div class="form-group">
                            <label>Your Message:</label>
                            <textarea name="message" rows="5" required></textarea>
                        </div>
                        <button type="submit" name="submit_feedback" class="btn">Send Feedback</button>
                    </form>

                    <!-- Profile Info -->
                    <div class="profile-info" style="margin-top: 2rem;">
                        <h3>Account Information</h3>
                        <p>Email: <?= htmlspecialchars($user_data['email'] ?? '') ?></p>
                        <p>Member since: <?= date('F Y', strtotime($user_data['registration_date'] ?? '')) ?></p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>