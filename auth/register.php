<?php
session_start();
require_once '../includes/db_connection.php';

// Redirect logged-in users
if (isset($_SESSION['user_id'])) {
    header("Location: ../user/dashboard.php");
    exit();
}

$errors = [];
$doctors = [];

try {
    // Fetch all doctors for the dropdown
    $stmt = $pdo->query("SELECT doctor_id, name, specialization FROM doctors");
    $doctors = $stmt->fetchAll();
} catch (PDOException $e) {
    error_log('Register page doctor fetch failed: ' . $e->getMessage());
    $errors[] = "Unable to load doctors right now. Please try again later.";
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    // User Data
    $name = trim($_POST['name']);
    $dob = $_POST['dob'];
    $gender = $_POST['gender'];
    $age = (int)$_POST['age'];
    $contact = trim($_POST['contact']);
    $email = trim($_POST['email']);
    $password = $_POST['password'];
    $blood_group = $_POST['blood_group'];
    
    // Appointment Data
    $doctor_id = (int)$_POST['doctor_id'];
    $appointment_date = $_POST['appointment_date'];
    $description = trim($_POST['description']);

    // Validation
    if (empty($name)) $errors[] = "Name is required";
    if (empty($dob)) $errors[] = "Date of Birth is required";
    if (!in_array($gender, ['Male', 'Female', 'Other'])) $errors[] = "Invalid gender";
    if ($age < 1 || $age > 120) $errors[] = "Invalid age";
    if (empty($contact)) $errors[] = "Contact number is required";
    if (!filter_var($email, FILTER_VALIDATE_EMAIL)) $errors[] = "Invalid email format";
    if (strlen($password) < 8) $errors[] = "Password must be at least 8 characters";
    if (empty($blood_group)) $errors[] = "Blood group is required";
    if (empty($doctor_id)) $errors[] = "Please select a doctor";
    if (empty($appointment_date)) $errors[] = "Appointment date is required";

    if (empty($errors)) {
        try {
            $pdo->beginTransaction();

            // Check if email exists
            $stmt = $pdo->prepare("SELECT user_id FROM users WHERE email = ?");
            $stmt->execute([$email]);
            if ($stmt->fetch()) {
                $errors[] = "Email already registered";
                throw new Exception("Duplicate email");
            }

            // Insert user
            $hashed_password = password_hash($password, PASSWORD_DEFAULT);
            $stmt = $pdo->prepare("INSERT INTO users 
                (name, dob, gender, age, contact, email, password, blood_group)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)");
            
            $stmt->execute([
                $name,
                $dob,
                $gender,
                $age,
                $contact,
                $email,
                $hashed_password,
                $blood_group
            ]);
            
            $user_id = $pdo->lastInsertId();

            // Insert appointment
            $stmt = $pdo->prepare("INSERT INTO appointments 
                (user_id, doctor_id, appointment_date, description, status, assigned_by)
                VALUES (?, ?, ?, ?, 'pending', 'user')");
            
            $stmt->execute([
                $user_id,
                $doctor_id,
                $appointment_date,
                $description
            ]);

            $pdo->commit();
            
            $_SESSION['registration_success'] = true;
            header("Location: login.php");
            exit();

        } catch (Exception $e) {
            $pdo->rollBack();
            if (!in_array("Email already registered", $errors)) {
                error_log('Registration failed: ' . $e->getMessage());
                $errors[] = "Registration failed. Please try again.";
            }
        }
    }
}
?>
<!DOCTYPE html>
<html lang="en">
    <meta charset="UTF-8">
    <title>MediSync - Register</title>
    <link href="../assets/css/style.css" rel="stylesheet">
    <style>
        body {
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
        }
        .navbar {
            backdrop-filter: blur(40px);
            border-radius: 10px;
            margin-top: 2%;
            padding: 1rem;
            width: 95%;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
        }
        
        .navbar-brand {
            font-size: 1.5rem;
            font-weight: bold;
            color: white;
        }
        /* Registration Page Styles */
        .register-container {
            max-width: 800px;
            margin: 50px auto;
            padding: 2rem;
            backdrop-filter: blur(40px);
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }

        .register-container h2 {
            text-align: center;
            margin-bottom: 1.5rem;
        }

        .form-row {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
        }

        .form-row .form-group {
            flex: 1;
        }

        .form-group {
            margin-bottom: 1rem;
        }

        .form-group label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 500;
        }

        .form-group input,
        .form-group select,
        .form-group textarea {
            width: 90%;
            padding: 0.8rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1rem;
        }

        .form-group textarea {
            resize: vertical;
            min-height: 100px;
        }

        .alert.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
            padding: 1rem;
            margin-bottom: 1rem;
            border-radius: 4px;
        }

        .alert.error p {
            margin: 0.3rem 0;
        }

        .btn {
            padding: 0.8rem 1.5rem;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            font-size: 1rem;
            cursor: pointer;
        }

        .btn:hover {
            background: #0056b3;
        }

        p {
            text-align: center;
            margin-top: 1rem;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="container">
            <a class="navbar-brand" href="../index.php">MediSync</a>
        </div>
    </nav>
    <!-- Registration Form -->
    <div class="register-container">
        <h2>Create New Account</h2>
        
        <?php if (!empty($errors)): ?>
            <div class="alert error">
                <?php foreach ($errors as $error): ?>
                    <p><?= $error ?></p>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>

        <form action="register.php" method="post">
            <div class="form-group">
                <label>Full Name:</label>
                <input type="text" name="name" required value="<?= htmlspecialchars($_POST['name'] ?? '') ?>">
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label>Date of Birth:</label>
                    <input type="date" name="dob" required value="<?= htmlspecialchars($_POST['dob'] ?? '') ?>">
                </div>

                <div class="form-group">
                    <label>Gender:</label>
                    <select name="gender" required>
                        <option value="Male" <?= ($_POST['gender'] ?? '') === 'Male' ? 'selected' : '' ?>>Male</option>
                        <option value="Female" <?= ($_POST['gender'] ?? '') === 'Female' ? 'selected' : '' ?>>Female</option>
                        <option value="Other" <?= ($_POST['gender'] ?? '') === 'Other' ? 'selected' : '' ?>>Other</option>
                    </select>
                </div>
            </div>

            <div class="form-row">
                <div class="form-group">
                    <label>Age:</label>
                    <input type="number" name="age" min="1" max="120" required value="<?= htmlspecialchars($_POST['age'] ?? '') ?>">
                </div>

                <div class="form-group">
                    <label>Blood Group:</label>
                    <select name="blood_group" required>
                        <option value="A+">A+</option>
                        <option value="A-">A-</option>
                        <option value="B+">B+</option>
                        <option value="B-">B-</option>
                        <option value="AB+">AB+</option>
                        <option value="AB-">AB-</option>
                        <option value="O+">O+</option>
                        <option value="O-">O-</option>
                    </select>
                </div>
            </div>

            <div class="form-group">
                <label>Contact Number:</label>
                <input type="tel" name="contact" required value="<?= htmlspecialchars($_POST['contact'] ?? '') ?>">
            </div>

            <div class="form-group">
                <label>Email:</label>
                <input type="email" name="email" required value="<?= htmlspecialchars($_POST['email'] ?? '') ?>">
            </div>

            <div class="form-group">
                <label>Password:</label>
                <div style="position: relative;">
                    <input type="password" name="password" id="password" required style="padding-right: 30px;">
                    <button type="button" onclick="togglePasswordVisibility()" style="position: absolute; right: 5px; top: 50%; transform: translateY(-50%); background: none; border: none; cursor: pointer;">👁️</button>
                </div>
            </div>
            <script>
                function togglePasswordVisibility() {
                    var passwordField = document.getElementById('password');
                    if (passwordField.type === 'password') {
                        passwordField.type = 'text';
                    } else {
                        passwordField.type = 'password';
                    }
                }
            </script>

            <div class="form-row">
                <div class="form-group">
                    <label>Select Doctor:</label>
                    <select name="doctor_id" required>
                        <option value="">Choose Doctor</option>
                        <?php foreach ($doctors as $doctor): ?>
                            <option value="<?= $doctor['doctor_id'] ?>"
                                <?= ($_POST['doctor_id'] ?? '') == $doctor['doctor_id'] ? 'selected' : '' ?>>
                                Dr. <?= htmlspecialchars($doctor['name']) ?> - <?= $doctor['specialization'] ?>
                            </option>
                        <?php endforeach; ?>
                    </select>
                </div>

                <div class="form-group">
                    <label>Appointment Date:</label>
                    <input type="date" name="appointment_date" required value="<?= htmlspecialchars($_POST['appointment_date'] ?? '') ?>">
                </div>
            </div>

            <div class="form-group">
                <label>Medical Description:</label>
                <textarea name="description" rows="3"><?= htmlspecialchars($_POST['description'] ?? '') ?></textarea>
            </div>

            <button type="submit" class="btn">Register</button>
        </form>

        <p>Already have an account? <a href="login.php">Login here</a></p>
    </div>
</body>
</html>