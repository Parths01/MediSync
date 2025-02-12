<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MediSync - Online Appointment System</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/5.0.0-alpha1/css/bootstrap.min.css">
    <style>
        body {
            font-family: 'Arial', sans-serif;
            margin: 0;
            padding: 0;
            color: white;
            box-sizing: border-box;
            background-image: url('./assets/image/wave.png');
            background-repeat: no-repeat;
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
            justify-items: center;
        }
        .navbar {
            backdrop-filter: blur(40px);
            border-radius: 10px;
            margin-top: 2%;
            width: 95%;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
        }
        .navbar-brand {
            font-size: 1.5rem;
            font-weight: bold;
            color: white;
        }
        .hero {
            width: 95%;
            height: 50vh;
            display: flex;
            justify-content: center;
            align-items: center;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
            border-radius: 20px;
            backdrop-filter: blur(40px);
        }
        .hero-content {
            width: 80%;
        }
        .hero h1 {
            font-size: 3rem;
            font-weight: bold;
        }
        .hero p {
            font-size: 1.5rem;
            font-weight: bold;
        }
        .cta-buttons {
            margin-top: 20px;
        }
        .btn {
            padding: 10px 20px;
            margin: 10px;
            border: none;
            border-radius: 5px;
            background-color: #007bff;
            color: white;
            font-size: 1rem;
            font-weight: bold;
            text-decoration: none;
        }
        .btn:hover {
            background-color: #0056b3;
        }
        .admin-btn {
            background-color: #28a745;
        }
        .admin-btn:hover {
            background-color: #218838;
        }
        .features {
            width: 95%;
            justify-content: center;
            align-items: center;
            display: flex;
            flex-wrap: wrap;
            margin-top: 20px;
        }
        .features .container {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-wrap: wrap;
        }
        .feature-card {
            width: 30%;
            margin: 10px;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
            backdrop-filter: blur(40px);
            text-align: center;
            flex: 1 1 calc(33.333% - 20px);
            box-sizing: border-box;
        }
        .feature-card h3 {
            font-size: 1.5rem;
            font-weight: bold;
        }
        .feature-card p {
            font-size: 1rem;
        }
        .footer {
            width: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
            margin-top: 20px;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 10);
            backdrop-filter: blur(40px);
        }
        .footer .container {
            display: flex;
            justify-content: center;
            align-items: center;
            flex-direction: column;
        }
        .footer p {
            font-size: 1rem;
        }
        .footer a {
            font-size: 1rem;
            color: white;
            text-decoration: none;
            margin: 0 10px;
        }
        .footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar">
        <div class="container">
            <a class="navbar-brand" href="index.php">MediSync</a>
        </div>
    </nav>
    <br>
    <!-- Hero Section -->
    <header class="hero">
        <div class="hero-content">
            <h1>Book Your Medical Appointment Online</h1>
            <p>Fast, Convenient, and Reliable Healthcare Services</p>
            <div class="cta-buttons">
                <a href="auth/login.php" class="btn">Login</a>
                <a href="auth/register.php" class="btn">Register</a>
                <a href="admin/login.php" class="btn admin-btn">Admin</a>
            </div>
        </div>
    </header>
    <br>
    <!-- Features Section -->
    <section class="features">
        <div class="container">
            <div class="feature-card">
                <h3>24/7 Access</h3>
                <p>Book appointments anytime, anywhere with our online platform.</p>
            </div>
            <div class="feature-card">
                <h3>Expert Doctors</h3>
                <p>Choose from our qualified and experienced medical professionals.</p>
            </div>
            <div class="feature-card">
                <h3>Instant Booking</h3>
                <p>Quick and easy appointment scheduling in just few clicks.</p>
            </div>
        </div>
    </section>

    <!-- Footer -->
    <footer class="footer">
        <div class="container">
            <p>&copy; 2024 MediSync. All rights reserved.
            <a href="#">Privacy Policy</a>
            <a href="#">Terms of Service</a>
            </p>
        </div>
    </footer>
</body>
</html>