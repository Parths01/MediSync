<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser(['admin']);

// Configuration
$upload_dir = '../uploads/doctors/';
$allowed_types = ['image/jpeg', 'image/png', 'image/gif'];
$max_size = 2 * 1024 * 1024; // 2MB

$action = $_GET['action'] ?? '';
$doctor_id = $_GET['id'] ?? 0;
$errors = [];
$success = '';

// Handle form submissions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $name = trim($_POST['name']);
    $specialization = trim($_POST['specialization']);
    $experience = (int)$_POST['experience'];
    $contact = trim($_POST['contact']);
    $photo = $_POST['current_photo'] ?? ''; // Keep existing photo if not changed

    // Validation
    if (empty($name)) $errors[] = "Name is required";
    if (empty($specialization)) $errors[] = "Specialization is required";
    if ($experience < 0) $errors[] = "Invalid experience value";
    if (empty($contact)) $errors[] = "Contact details are required";

    // Handle file upload
    if (isset($_FILES['photo']) && $_FILES['photo']['error'] === UPLOAD_ERR_OK) {
        $file = $_FILES['photo'];
        
        // Validate file
        $finfo = finfo_open(FILEINFO_MIME_TYPE);
        $mime_type = finfo_file($finfo, $file['tmp_name']);
        finfo_close($finfo);

        if (!in_array($mime_type, $allowed_types)) {
            $errors[] = "Only JPG, PNG, and GIF files are allowed";
        } elseif ($file['size'] > $max_size) {
            $errors[] = "File size must be less than 2MB";
        } else {
            // Create upload directory if not exists
            if (!file_exists($upload_dir)) {
                mkdir($upload_dir, 0755, true);
            }
            
            // Generate unique filename
            $ext = pathinfo($file['name'], PATHINFO_EXTENSION);
            $filename = uniqid('doctor_') . '.' . $ext;
            $target_path = $upload_dir . $filename;

            if (move_uploaded_file($file['tmp_name'], $target_path)) {
                $photo = $target_path;
                
                // Delete old photo if exists
                if (!empty($_POST['current_photo']) && file_exists($_POST['current_photo'])) {
                    unlink($_POST['current_photo']);
                }
            } else {
                $errors[] = "Failed to upload photo";
            }
        }
    }

    if (empty($errors)) {
        try {
            if ($_POST['action'] === 'add') {
                $stmt = $pdo->prepare("INSERT INTO doctors 
                    (name, specialization, experience, contact_details, photo)
                    VALUES (?, ?, ?, ?, ?)");
                $stmt->execute([$name, $specialization, $experience, $contact, $photo]);
                $success = "Doctor added successfully!";
            } elseif ($_POST['action'] === 'edit') {
                $stmt = $pdo->prepare("UPDATE doctors SET
                    name = ?,
                    specialization = ?,
                    experience = ?,
                    contact_details = ?,
                    photo = ?
                    WHERE doctor_id = ?");
                $stmt->execute([$name, $specialization, $experience, $contact, $photo, $doctor_id]);
                $success = "Doctor updated successfully!";
            }
        } catch (PDOException $e) {
            error_log('Doctors admin write failed: ' . $e->getMessage());
            $errors[] = "Unable to save doctor details right now.";
        }
    }
}

// Handle delete action
if ($action === 'delete') {
    try {
        // Get current photo path
        $stmt = $pdo->prepare("SELECT photo FROM doctors WHERE doctor_id = ?");
        $stmt->execute([$doctor_id]);
        $doctor = $stmt->fetch();

        // Delete photo if exists
        if (!empty($doctor['photo']) && file_exists($doctor['photo'])) {
            unlink($doctor['photo']);
        }

        // Delete doctor record
        $stmt = $pdo->prepare("DELETE FROM doctors WHERE doctor_id = ?");
        $stmt->execute([$doctor_id]);
        $success = "Doctor deleted successfully!";
    } catch (PDOException $e) {
        error_log('Doctor delete failed: ' . $e->getMessage());
        $errors[] = "Unable to delete doctor right now.";
    }
}

// Get doctor for editing
$current_doctor = [];
if ($action === 'edit' && $doctor_id) {
    try {
        $stmt = $pdo->prepare("SELECT * FROM doctors WHERE doctor_id = ?");
        $stmt->execute([$doctor_id]);
        $current_doctor = $stmt->fetch();
    } catch (PDOException $e) {
        error_log('Doctor fetch for edit failed: ' . $e->getMessage());
        $errors[] = "Unable to load doctor details right now.";
    }
}

// Get all doctors
try {
    $stmt = $pdo->query("SELECT * FROM doctors ORDER BY name");
    $doctors = $stmt->fetchAll();
} catch (PDOException $e) {
    error_log('Doctor list fetch failed: ' . $e->getMessage());
    $errors[] = "Unable to load doctor list right now.";
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Manage Doctors - MediSync</title>
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
        .admin-dashboard {
            display: flex;
            width: 100%;
            height: 100vh;
        }
        .admin-sidebar {
            width: 15%;
            height: 100%;
            padding: 20px;
            background: rgba(0, 0, 0, 0.5);
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
            position: fixed;
        }
        .admin-sidebar h2 {
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .admin-sidebar nav {
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
        .admin-main {
            margin-left: 20%;
            padding: 20px;
            width: 80%;
        }
        .stat-card {
            background: rgba(0, 0, 0, 0.5);
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
            margin-bottom: 20px;
        }
        .stat-card h2 {
            font-size: 1.5rem;
            font-weight: bold;
            margin-bottom: 20px;
        }
        form {
            margin-bottom: 20px;
        }
        .form-row {
            display: flex;
            justify-content: space-between;
        }
        .form-group {
            width: 30%;
        }
        .form-group label {
            font-size: 1.2rem;
        }
        .form-group input {
            width: 95%;
            padding: 10px;
            margin-top: 5px;
            border-radius: 5px;
            border: none;
        }
        .btn {
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
        .alert {
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .alert.error {
            background: #dc3545;
            color: white;
        }
        .alert.success {
            background: #28a745;
            color: white;
        }
        .search-form {
            margin-bottom: 20px;
        }
        .search-form input {
            padding: 10px;
            border-radius: 5px;
            border: none;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        table th, table td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
            text-align: left;
        }
        table th {
            background: #333;
            color: white;
        }
        .no-photo {
            display: inline-block;
            padding: 0.5rem;
            background: #ddd;
            color: #333;
            border-radius: 4px;
        }
        .current-photo {
            margin-top: 1rem;
            padding: 0.5rem;
            border: 1px solid #ddd;
            display: inline-block;
        }
        .current-photo img {
            max-width: 150px;
            height: auto;
        }
        input[type="file"] {
            padding: 0.5rem;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 100%;
        }
        .doctor-photo {
            max-width: 80px;
            height: auto;
            border-radius: 4px;
        }
        .btn-sm {
            padding: 0.5rem 1rem;
            margin-right: 0.5rem;
            border-radius: 4px;
            border: none;
            background: #333;
            color: white;
            font-size: 0.8rem;
            font-weight: bold;
            text-transform: uppercase;
            cursor: pointer;
        }
        .btn-sm:hover {
            background: #555;
        }
        .btn-sm.danger {
            background: #dc3545;
        }
        .btn-sm.danger:hover {
            background: #a71d2a;
        }
        
    </style>
</head>
<body>
    <div class="admin-dashboard">
        <!-- Sidebar -->
        <div class="admin-sidebar">
            <h2>MediSync Admin</h2>
            <nav>
                <a href="dashboard.php" class="nav-link">Dashboard</a>
                <a href="doctors.php" class="nav-link active">Manage Doctors</a>
                <a href="feedback.php" class="nav-link">Patient Feedback</a>
                <a href="reports.php" class="nav-link">System Reports</a>
                <a href="logout.php" class="nav-link">Logout</a>
            </nav>
        </div>

        <div class="admin-main">
            <h1>Manage Doctors</h1>
            
            <!-- Notifications -->
            <?php if ($success): ?>
                <div class="alert success"><?= $success ?></div>
            <?php endif; ?>
            <?php if (!empty($errors)): ?>
                <div class="alert error">
                    <?php foreach ($errors as $error): ?>
                        <p><?= $error ?></p>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>

            <!-- Add/Edit Form -->
            <div class="stat-card">
                <h2><?= $action === 'edit' ? 'Edit Doctor' : 'Add New Doctor' ?></h2>
                <form method="post" enctype="multipart/form-data">
                    <div class="form-row">
                        <div class="form-group">
                            <label>Full Name:</label>
                            <input type="text" name="name" required 
                                   value="<?= htmlspecialchars($current_doctor['name'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label>Specialization:</label>
                            <input type="text" name="specialization" required 
                                   value="<?= htmlspecialchars($current_doctor['specialization'] ?? '') ?>">
                        </div>
                    </div>
                    
                    <div class="form-row">
                        <div class="form-group">
                            <label>Experience (years):</label>
                            <input type="number" name="experience" min="0" required 
                                   value="<?= htmlspecialchars($current_doctor['experience'] ?? '') ?>">
                        </div>
                        <div class="form-group">
                            <label>Contact Details:</label>
                            <input type="text" name="contact" required 
                                   value="<?= htmlspecialchars($current_doctor['contact_details'] ?? '') ?>">
                        </div>
                    </div>

                    <div class="form-group">
                        <label>Photo:</label>
                        <input type="file" name="photo" accept="image/*">
                        <?php if (!empty($current_doctor['photo'])): ?>
                            <div class="current-photo">
                                <img src="<?= $current_doctor['photo'] ?>" alt="Current Photo">
                                <p>Current Photo</p>
                                <input type="hidden" name="current_photo" value="<?= $current_doctor['photo'] ?>">
                            </div>
                        <?php endif; ?>
                    </div>
                    
                    <input type="hidden" name="action" value="<?= $action === 'edit' ? 'edit' : 'add' ?>">
                    <button type="submit" class="btn">
                        <?= $action === 'edit' ? 'Update Doctor' : 'Add Doctor' ?>
                    </button>
                    <?php if ($action === 'edit'): ?>
                        <a href="doctors.php" class="btn">Cancel</a>
                    <?php endif; ?>
                </form>
            </div>

            <!-- Doctors List -->
            <div class="stat-card">
                <h2>Registered Doctors</h2>
                <table>
                    <thead>
                        <tr>
                            <th>Photo</th>
                            <th>Name</th>
                            <th>Specialization</th>
                            <th>Experience</th>
                            <th>Contact</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        <?php foreach ($doctors as $doctor): ?>
                        <tr>
                            <td>
                                <?php if (!empty($doctor['photo'])): ?>
                                    <img src="<?= $doctor['photo'] ?>" alt="Doctor Photo" class="doctor-photo">
                                <?php else: ?>
                                    <span class="no-photo">No photo</span>
                                <?php endif; ?>
                            </td>
                            <td><?= htmlspecialchars($doctor['name']) ?></td>
                            <td><?= htmlspecialchars($doctor['specialization']) ?></td>
                            <td><?= $doctor['experience'] ?> years</td>
                            <td><?= htmlspecialchars($doctor['contact_details']) ?></td>
                            <td>
                                <a href="doctors.php?action=edit&id=<?= $doctor['doctor_id'] ?>" 
                                   class="btn btn-sm">Edit</a>
                                <a href="doctors.php?action=delete&id=<?= $doctor['doctor_id'] ?>" 
                                   class="btn btn-sm danger"
                                   onclick="return confirm('Are you sure?')">Delete</a>
                            </td>
                        </tr>
                        <?php endforeach; ?>
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>