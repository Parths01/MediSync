CREATE DATABASE IF NOT EXISTS medisync CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE medisync;

CREATE TABLE IF NOT EXISTS users (
    user_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    dob DATE NOT NULL,
    gender ENUM('Male','Female','Other') NOT NULL,
    age INT NOT NULL,
    contact VARCHAR(15) NOT NULL,
    email VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    blood_group ENUM('A+','A-','B+','B-','AB+','AB-','O+','O-') DEFAULT NULL,
    role ENUM('patient','admin') DEFAULT 'patient',
    registration_date TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_email (email)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS doctors (
    doctor_id INT NOT NULL AUTO_INCREMENT,
    name VARCHAR(255) NOT NULL,
    specialization VARCHAR(255) NOT NULL,
    experience INT NOT NULL,
    contact_details VARCHAR(255) NOT NULL,
    photo VARCHAR(255) DEFAULT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (doctor_id)
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS appointments (
    appointment_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    doctor_id INT NOT NULL,
    appointment_date DATETIME NOT NULL,
    description TEXT,
    status ENUM('pending','confirmed','completed','rejected','cancelled') DEFAULT 'pending',
    assigned_by ENUM('user','admin') NOT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (appointment_id),
    KEY idx_appointments_user_id (user_id),
    KEY idx_appointments_doctor_id (doctor_id),
    CONSTRAINT fk_appointments_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    CONSTRAINT fk_appointments_doctor FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS contact_messages (
    contact_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    status ENUM('open','closed') DEFAULT 'open',
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (contact_id),
    KEY idx_contact_messages_user_id (user_id),
    CONSTRAINT fk_contact_messages_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS feedback (
    feedback_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (feedback_id),
    KEY idx_feedback_user_id (user_id),
    CONSTRAINT fk_feedback_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

CREATE TABLE IF NOT EXISTS medical_history (
    history_id INT NOT NULL AUTO_INCREMENT,
    user_id INT NOT NULL,
    diagnosis VARCHAR(255) NOT NULL,
    treatment TEXT,
    notes TEXT,
    recorded_at DATE NOT NULL,
    created_at TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (history_id),
    KEY idx_medical_history_user_id (user_id),
    CONSTRAINT fk_medical_history_user FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Demo data: all accounts use the password Demo@123.
INSERT INTO doctors (name, specialization, experience, contact_details)
SELECT 'Aarav Mehta', 'Neurologist', 12, '9000000001'
WHERE NOT EXISTS (SELECT 1 FROM doctors WHERE name = 'Aarav Mehta');

INSERT INTO doctors (name, specialization, experience, contact_details)
SELECT 'Anaya Shah', 'Gynecologist', 10, '9000000002'
WHERE NOT EXISTS (SELECT 1 FROM doctors WHERE name = 'Anaya Shah');

INSERT INTO doctors (name, specialization, experience, contact_details)
SELECT 'Kabir Joshi', 'Physiotherapy', 8, '9000000003'
WHERE NOT EXISTS (SELECT 1 FROM doctors WHERE name = 'Kabir Joshi');

INSERT IGNORE INTO users (name, dob, gender, age, contact, email, password, blood_group, role)
VALUES
        ('Aditi Patil', '1998-04-12', 'Female', 28, '9000010001', 'demo01@medisync.test', '$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK', 'A+', 'patient'),
        ('Rohan Kulkarni', '1995-09-21', 'Male', 31, '9000010002', 'demo02@medisync.test', '$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK', 'O+', 'patient'),
        ('Sneha Deshmukh', '2001-01-08', 'Female', 25, '9000010003', 'demo03@medisync.test', '$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK', 'B+', 'patient'),
        ('Vivek Nair', '1989-06-16', 'Male', 37, '9000010004', 'demo04@medisync.test', '$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK', 'AB+', 'patient'),
        ('Meera Iyer', '1992-11-03', 'Female', 33, '9000010005', 'demo05@medisync.test', '$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK', 'O-', 'patient'),
        ('Arjun Rao', '1985-02-27', 'Male', 41, '9000010006', 'demo06@medisync.test', '$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK', 'A-', 'patient'),
        ('Kavya Menon', '1999-07-19', 'Female', 27, '9000010007', 'demo07@medisync.test', '$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK', 'B-', 'patient'),
        ('Ishaan Verma', '1996-12-30', 'Male', 29, '9000010008', 'demo08@medisync.test', '$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK', 'AB-', 'patient'),
        ('Pooja Singh', '1990-05-25', 'Female', 36, '9000010009', 'demo09@medisync.test', '$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK', 'A+', 'patient'),
        ('Nikhil Gupta', '1988-10-14', 'Male', 37, '9000010010', 'demo10@medisync.test', '$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK', 'O+', 'patient');

INSERT INTO appointments (user_id, doctor_id, appointment_date, description, status, assigned_by)
SELECT u.user_id, d.doctor_id, DATE_SUB(NOW(), INTERVAL 30 DAY), 'Demo follow-up consultation', 'completed', 'admin'
FROM users u
JOIN doctors d ON d.name = 'Aarav Mehta'
WHERE u.email LIKE 'demo%@medisync.test'
    AND NOT EXISTS (
            SELECT 1 FROM appointments a
            WHERE a.user_id = u.user_id AND a.description = 'Demo follow-up consultation'
    );

INSERT INTO medical_history (user_id, diagnosis, treatment, notes, recorded_at)
SELECT u.user_id, 'Seasonal allergy', 'Antihistamine as prescribed', 'Demo medical history entry', DATE_SUB(CURDATE(), INTERVAL 45 DAY)
FROM users u
WHERE u.email LIKE 'demo%@medisync.test'
    AND NOT EXISTS (
            SELECT 1 FROM medical_history h
            WHERE h.user_id = u.user_id AND h.diagnosis = 'Seasonal allergy'
    );
