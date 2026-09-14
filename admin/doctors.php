<?php
require_once '../includes/auth_guard.php';
require_once '../includes/db_connection.php';
authenticateUser(['admin']);

// Configuration
$upload_dir = '../uploads/doctors/';
$allowed_types = ['image/jpeg', 'image/png', 'image/gif'];
$max_size = 2 * 1024 * 1024; // 2MB

$action = $_GET['action'] ?? '';
$doctor_id = (int) ($_GET['id'] ?? 0);
$errors = [];
$success = '';

// Handle form submissions
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    verify_csrf_token();
    $action = $_POST['action'] ?? '';
    $doctor_id = (int) ($_POST['doctor_id'] ?? 0);
    $name = trim($_POST['name']);
    $specialization = trim($_POST['specialization']);
    $experience = (int)$_POST['experience'];
    $contact = trim($_POST['contact']);
    $photo = '';
    if ($action === 'edit' && $doctor_id > 0) {
        $existing = $pdo->prepare("SELECT photo FROM doctors WHERE doctor_id = ?");
        $existing->execute([$doctor_id]);
        $existing = $existing->fetch();
        $photo = $existing['photo'] ?? '';
    }

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

        if (!in_array($mime_type, $allowed_types, true)) {
            $errors[] = "Only JPG, PNG, and GIF files are allowed";
        } elseif ($file['size'] > $max_size) {
            $errors[] = "File size must be less than 2MB";
        } else {
            // Create upload directory if not exists
            if (!file_exists($upload_dir)) {
                mkdir($upload_dir, 0755, true);
            }
            
            // Generate unique filename
            $extensions = ['image/jpeg' => 'jpg', 'image/png' => 'png', 'image/gif' => 'gif'];
            $filename = 'doctor_' . bin2hex(random_bytes(16)) . '.' . $extensions[$mime_type];
            $target_path = $upload_dir . $filename;

            if (move_uploaded_file($file['tmp_name'], $target_path)) {
                $old_photo = $photo;
                $photo = $target_path;
                
                if (!empty($old_photo) && basename($old_photo) === $old_photo) {
                    $old_photo = $upload_dir . $old_photo;
                }
                if (!empty($old_photo) && preg_match('#^\.\./uploads/doctors/[^/\\\\]+$#', $old_photo) &&
                    is_file($old_photo)) {
                    unlink($old_photo);
                }
            } else {
                $errors[] = "Failed to upload photo";
            }
        }
    }

    if (empty($errors)) {
        try {
            if ($action === 'add') {
                $stmt = $pdo->prepare("INSERT INTO doctors 
                    (name, specialization, experience, contact_details, photo)
                    VALUES (?, ?, ?, ?, ?)");
                $stmt->execute([$name, $specialization, $experience, $contact, $photo]);
                $success = "Doctor added successfully!";
            } elseif ($action === 'edit' && $doctor_id > 0) {
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
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $action === 'delete') {
    try {
        // Get current photo path
        $stmt = $pdo->prepare("SELECT photo FROM doctors WHERE doctor_id = ?");
        $stmt->execute([$doctor_id]);
        $doctor = $stmt->fetch();

        // Delete photo if exists
        if (!empty($doctor['photo']) &&
            preg_match('#^\.\./uploads/doctors/[^/\\\\]+$#', $doctor['photo']) &&
            is_file($doctor['photo'])) {
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
                <div class="alert success"><?= htmlspecialchars($success, ENT_QUOTES, 'UTF-8') ?></div>
            <?php endif; ?>
            <?php if (!empty($errors)): ?>
                <div class="alert error">
                    <?php foreach ($errors as $error): ?>
                        <p><?= htmlspecialchars($error, ENT_QUOTES, 'UTF-8') ?></p>
                    <?php endforeach; ?>
                </div>
            <?php endif; ?>

            <!-- Add/Edit Form -->
            <div class="stat-card">
                <h2><?= $action === 'edit' ? 'Edit Doctor' : 'Add New Doctor' ?></h2>
                <form method="post" enctype="multipart/form-data">
                    <?= csrf_field() ?>
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
                                <img src="<?= htmlspecialchars($current_doctor['photo'], ENT_QUOTES, 'UTF-8') ?>" alt="Current Photo">
                                <p>Current Photo</p>
                            </div>
                        <?php endif; ?>
                    </div>
                    
                    <input type="hidden" name="action" value="<?= $action === 'edit' ? 'edit' : 'add' ?>">
                    <input type="hidden" name="doctor_id" value="<?= $doctor_id ?>">
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
                                    <img src="<?= htmlspecialchars($doctor['photo'], ENT_QUOTES, 'UTF-8') ?>" alt="Doctor Photo" class="doctor-photo">
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
                                <form method="post" style="display:inline" onsubmit="return confirm('Are you sure?')">
                                    <?= csrf_field() ?>
                                    <input type="hidden" name="action" value="delete">
                                    <input type="hidden" name="doctor_id" value="<?= $doctor['doctor_id'] ?>">
                                    <button type="submit" class="btn btn-sm danger">Delete</button>
                                </form>
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