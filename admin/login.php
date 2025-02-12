<?php
session_start();
require_once '../includes/db_connection.php';

// Redirect logged-in admins
if (isset($_SESSION['admin_id'])) {
    header("Location: dashboard.php");
    exit();
}

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $email = filter_input(INPUT_POST, 'email', FILTER_SANITIZE_EMAIL);
    $password = $_POST['password'];

    if (empty($email) || empty($password)) {
        $error = "Please fill in all fields";
    } else {
        // Corrected SQL query (removed incorrect password check)
        $stmt = $pdo->prepare("SELECT * FROM users WHERE email = ?");
        $stmt->execute([$email]);
        $admin = $stmt->fetch();

        // Ensure user exists and compare plain-text passwords
        if ($admin && $password === $admin['password']) {
            $_SESSION['admin_id'] = $admin['user_id'];
            $_SESSION['admin_name'] = $admin['name'];
            header("Location: dashboard.php");
            exit();
        } else {
            $error = "Invalid credentials";
        }
    }
}
?>


<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>MediSync - Admin Login</title>
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
            padding: 20px;
            width: 95%;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
        }
        .navbar-brand {
            font-size: 1.5rem;
            font-weight: bold;
            color: white;
        }
        .admin-login-box {
            margin: 0 auto;
            margin-top: 10%;
            width: 300px;
            padding: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
        }
        .admin-logo {
            text-align: center;
        }
        .admin-logo img {
            width: 100px;
        }
        .form-group {
            margin-top: 20px;
        }
        .form-group label {
            font-size: 1.2rem;
            font-weight: bold;
        }
        .form-group input {
            width: 90%;
            padding: 10px;
            margin-top: 5px;
            border-radius: 5px;
            border: none;
        }
        .btn {
            width: 100%;
            padding: 10px;
            margin-top: 20px;
            border-radius: 5px;
            border: none;
            background: #333;
            color: white;
            font-size: 1.2rem;
            font-weight: bold;
            cursor: pointer;
        }
        .btn:hover {
            background: #555;
        }
    </style>
</head>
<body class="admin-login">
     <!-- Navigation -->
     <nav class="navbar">
        <div class="container">
            <a class="navbar-brand" href="../index.php">MediSync</a>
        </div>
    </nav>
    <div class="admin-login-box">
        <div class="admin-logo">
            <img src="../assets/image/Admin-logo.png" alt="Admin Portal">
        </div>
        
        <?php if ($error): ?>
            <div class="alert error"><?= $error ?></div>
        <?php endif; ?>

        <form action="login.php" method="post">
            <div class="form-group">
                <label>Admin Email:</label>
                <input type="email" name="email" required autocomplete="off">
            </div>
            
            <div class="form-group">
                <label>Password:</label>
                <input type="password" name="password" required>
            </div>
            
            <button type="submit" class="btn btn-dark">Login</button>
        </form>
    </div>
</body>
</html>