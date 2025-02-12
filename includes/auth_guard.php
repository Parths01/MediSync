<?php
session_start();

function authenticateUser($allowedRoles = []) {
    if (!isset($_SESSION['user_id'])) {
        header("Location: ../auth/login.php");
        exit();
    }
    
    if (!empty($allowedRoles) && !in_array($_SESSION['role'], $allowedRoles)) {
        header("HTTP/1.1 403 Forbidden");
        exit("Access Denied");
    }
}
?>