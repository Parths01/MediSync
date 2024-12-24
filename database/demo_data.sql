USE medisync;

-- Demo patient login password for all accounts: Demo@123
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
