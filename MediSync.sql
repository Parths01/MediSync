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
  appointment_date date NOT NULL,
  `description` text,
  `status` enum('pending','confirmed','completed') DEFAULT 'pending',
  assigned_by enum('user','admin') NOT NULL,
  created_at timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (appointment_id),
  KEY user_id (user_id),
  KEY doctor_id (doctor_id),
  CONSTRAINT appointments_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id),
  CONSTRAINT appointments_ibfk_2 FOREIGN KEY (doctor_id) REFERENCES doctors (doctor_id)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  CONSTRAINT contact_messages_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id)
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
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doctors`
--

LOCK TABLES doctors WRITE;
/*!40000 ALTER TABLE doctors DISABLE KEYS */;
INSERT INTO doctors VALUES (1,'Parth Suryawanshi','Neurologist',15,'8600291347','2025-02-08 20:55:31','../uploads/doctors/doctor_67a7c4c352372.jpg'),(5,'Palak Vora','Gynecologist',10,'9518736451','2025-02-08 20:59:07','../uploads/doctors/doctor_67a7c59b2e847.jpg'),(6,'Khushi Rathi','Physiotherapy',5,'7821892792','2025-02-08 20:59:46','../uploads/doctors/doctor_67a7c5c2d5f41.jpg');
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
  CONSTRAINT feedback_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (user_id)
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
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES users WRITE;
/*!40000 ALTER TABLE users DISABLE KEYS */;
INSERT INTO users VALUES (1,'Parth Suryawanshi','2003-08-10','Male',21,'+91 8600291347','parth001@gmail.com','parth001','A+','admin','2025-02-08 20:11:37'),(2,'Balaji Suryawanshi','1977-06-14','Male',48,'9503208977','balajisuryawanshi171@gmail.com','$2y$10$0hduDFhw6hkq5CAUEzw0y.X3YWRjFqMDJFzxQk2xuJLGpUyFtPKBe','A+','patient','2025-02-08 21:25:13');
/*!40000 ALTER TABLE users ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-02-09  3:40:02
