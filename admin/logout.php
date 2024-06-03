<?php
require_once '../includes/auth_guard.php';

logout_session();
redirectTo('login.php');
?>