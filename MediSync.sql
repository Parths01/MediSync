CREATE DATABASE  IF NOT EXISTS `medisync` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;
USE `medisync`;
-- MySQL dump 10.13  Distrib 8.0.40, for Win64 (x86_64)
--
-- Host: localhost    Database: medisync
-- ------------------------------------------------------
-- Server version	8.0.40

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `appointments`
--

DROP TABLE IF EXISTS appointments;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE appointments (
  appointment_id int NOT NULL AUTO_INCREMENT,
  user_id int NOT NULL,
  doctor_id int NOT NULL,
  appointment_date datetime NOT NULL,
  `description` text,
  `status` enum('pending','confirmed','completed','rejected','cancelled') DEFAULT 'pending',
  assigned_by enum('user','admin') NOT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (appointment_id),
  KEY idx_appointments_user_id (user_id),
  KEY idx_appointments_doctor_id (doctor_id),
  CONSTRAINT appointments_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
  CONSTRAINT appointments_ibfk_2 FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `appointments`
--

LOCK TABLES appointments WRITE;
/*!40000 ALTER TABLE appointments DISABLE KEYS */;
INSERT INTO appointments VALUES (1,2,1,'2025-02-11','Neuro OPD monthly Checkup','pending','user','2025-02-08 21:25:13');
/*!40000 ALTER TABLE appointments ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contact_messages`
--

DROP TABLE IF EXISTS contact_messages;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE contact_messages (
  contact_id int NOT NULL AUTO_INCREMENT,
  user_id int NOT NULL,
  message text NOT NULL,
  `status` enum('open','closed') DEFAULT 'open',
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (contact_id),
  KEY user_id (user_id),
  CONSTRAINT contact_messages_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contact_messages`
--

LOCK TABLES contact_messages WRITE;
/*!40000 ALTER TABLE contact_messages DISABLE KEYS */;
/*!40000 ALTER TABLE contact_messages ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `doctors`
--

DROP TABLE IF EXISTS doctors;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE doctors (
  doctor_id int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  specialization varchar(255) NOT NULL,
  experience int NOT NULL,
  contact_details varchar(255) NOT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  photo varchar(255) DEFAULT NULL,
  PRIMARY KEY (doctor_id)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doctors`
--

LOCK TABLES doctors WRITE;
/*!40000 ALTER TABLE doctors DISABLE KEYS */;
INSERT INTO doctors VALUES (1,'Parth Suryawanshi','Neurologist',15,'8600291347','2025-02-08 20:55:31','../uploads/doctors/doctor_67a7c4c352372.jpg'),(5,'Palak Vora','Gynecologist',10,'9518736451','2025-02-08 20:59:07','../uploads/doctors/doctor_67a7c59b2e847.jpg'),(6,'Khushi Rathi','Physiotherapy',5,'7821892792','2025-02-08 20:59:46','../uploads/doctors/doctor_67a7c5c2d5f41.jpg'),(7,'Aarav Mehta','Neurologist',12,'9000000001','2026-09-14 00:00:00',NULL),(8,'Anaya Shah','Gynecologist',10,'9000000002','2026-09-14 00:00:00',NULL),(9,'Kabir Joshi','Physiotherapy',8,'9000000003','2026-09-14 00:00:00',NULL);
/*!40000 ALTER TABLE doctors ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `feedback`
--

DROP TABLE IF EXISTS feedback;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE feedback (
  feedback_id int NOT NULL AUTO_INCREMENT,
  user_id int NOT NULL,
  message text NOT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (feedback_id),
  KEY user_id (user_id),
  CONSTRAINT feedback_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feedback`
--

LOCK TABLES feedback WRITE;
/*!40000 ALTER TABLE feedback DISABLE KEYS */;
/*!40000 ALTER TABLE feedback ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medical_history`
--

DROP TABLE IF EXISTS medical_history;
CREATE TABLE medical_history (
  history_id int NOT NULL AUTO_INCREMENT,
  user_id int NOT NULL,
  diagnosis varchar(255) NOT NULL,
  treatment text,
  notes text,
  recorded_at date NOT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (history_id),
  KEY idx_medical_history_user_id (user_id),
  CONSTRAINT medical_history_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS users;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE users (
  user_id int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  dob date NOT NULL,
  gender enum('Male','Female','Other') NOT NULL,
  age int NOT NULL,
  contact varchar(15) NOT NULL,
  email varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  blood_group enum('A+','A-','B+','B-','AB+','AB-','O+','O-') DEFAULT NULL,
  `role` enum('patient','admin') DEFAULT 'patient',
  registration_date timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (user_id),
  UNIQUE KEY email (email)
) ENGINE=InnoDB AUTO_INCREMENT=13 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES users WRITE;
/*!40000 ALTER TABLE users DISABLE KEYS */;
INSERT INTO users VALUES (1,'Parth Suryawanshi','2003-08-10','Male',21,'+91 8600291347','parth001@gmail.com','parth001','A+','admin','2025-02-08 20:11:37'),(2,'Balaji Suryawanshi','1977-06-14','Male',48,'9503208977','balajisuryawanshi171@gmail.com','$2y$10$0hduDFhw6hkq5CAUEzw0y.X3YWRjFqMDJFzxQk2xuJLGpUyFtPKBe','A+','patient','2025-02-08 21:25:13');
INSERT INTO users (name, dob, gender, age, contact, email, password, blood_group, role)
VALUES
('Aditi Patil','1998-04-12','Female',28,'9000010001','demo01@medisync.test','$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK','A+','patient'),
('Rohan Kulkarni','1995-09-21','Male',31,'9000010002','demo02@medisync.test','$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK','O+','patient'),
('Sneha Deshmukh','2001-01-08','Female',25,'9000010003','demo03@medisync.test','$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK','B+','patient'),
('Vivek Nair','1989-06-16','Male',37,'9000010004','demo04@medisync.test','$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK','AB+','patient'),
('Meera Iyer','1992-11-03','Female',33,'9000010005','demo05@medisync.test','$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK','O-','patient'),
('Arjun Rao','1985-02-27','Male',41,'9000010006','demo06@medisync.test','$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK','A-','patient'),
('Kavya Menon','1999-07-19','Female',27,'9000010007','demo07@medisync.test','$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK','B-','patient'),
('Ishaan Verma','1996-12-30','Male',29,'9000010008','demo08@medisync.test','$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK','AB-','patient'),
('Pooja Singh','1990-05-25','Female',36,'9000010009','demo09@medisync.test','$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK','A+','patient'),
('Nikhil Gupta','1988-10-14','Male',37,'9000010010','demo10@medisync.test','$2y$10$XIIb3iKeRjE0HR/aHbajuu3iACFiA1ZQpnCQz20qrt4CzyQje88GK','O+','patient');
/*!40000 ALTER TABLE users ENABLE KEYS */;
UNLOCK TABLES;

INSERT INTO appointments (user_id, doctor_id, appointment_date, description, status, assigned_by)
SELECT u.user_id, d.doctor_id, DATE_SUB(NOW(), INTERVAL 30 DAY), 'Demo follow-up consultation', 'completed', 'admin'
FROM users u
JOIN doctors d ON d.name = 'Aarav Mehta'
WHERE u.email LIKE 'demo%@medisync.test';

INSERT INTO medical_history (user_id, diagnosis, treatment, notes, recorded_at)
SELECT user_id, 'Seasonal allergy', 'Antihistamine as prescribed', 'Demo medical history entry', DATE_SUB(CURDATE(), INTERVAL 45 DAY)
FROM users
WHERE email LIKE 'demo%@medisync.test';
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-02-09  3:40:02
