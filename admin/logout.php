<?php
require_once '../includes/auth_guard.php';
logout_session();
header("Location: login.php");
exit();
?>