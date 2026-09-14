<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';

// Redirect logged-in admins
if (isset($_SESSION['user_id']) && isset($_SESSION['role']) && $_SESSION['role'] === 'admin') {
    header("Location: dashboard.php");
    exit();
}

$error = '';
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    verify_csrf_token();
    $email = filter_input(INPUT_POST, 'email', FILTER_SANITIZE_EMAIL);
    $password = $_POST['password'];

    if (empty($email) || empty($password)) {
        $error = "Please fill in all fields";
    } else {
        $stmt = $pdo->prepare("SELECT * FROM users WHERE email = ?");
        $stmt->execute([$email]);
        $admin = $stmt->fetch();

        $isValidPassword = false;
        if ($admin) {
            $isValidPassword = password_verify($password, $admin['password']);
        }

        if ($admin && $isValidPassword && $admin['role'] === 'admin') {
            establish_session($admin);
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
            <div class="alert error"><?= htmlspecialchars($error) ?></div>
        <?php endif; ?>

        <form action="login.php" method="post">
            <?= csrf_field() ?>
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