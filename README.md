# MediSync

MediSync is a web-based healthcare appointment management system that helps patients book doctor appointments online and allows admins to manage doctors, feedback, and reports.

## Purpose of the Project

The main goal of MediSync is to simplify hospital or clinic appointment workflows.

- Patients can register, log in, browse doctors, and book appointments.
- Patients can manage profile details and send contact messages/feedback.
- Admin users can manage doctor records and review user feedback/reports.
- The system keeps all records in a MySQL database for easy tracking.

## Stack Used

- Frontend: HTML, CSS, Bootstrap
- Backend: Core PHP (procedural + PDO)
- Database: MySQL
- Web Server: Apache (recommended)
- Version Control: Git

## Project Structure

- `index.php` -> landing page
- `auth/` -> user authentication (login, register, logout)
- `user/` -> patient dashboard, booking, contact, profile
- `admin/` -> admin login, dashboard, doctor management, reports
- `includes/` -> shared auth and database connection files
- `assets/` -> CSS and images
- `uploads/doctors/` -> uploaded doctor photos
- `database/schema.sql` -> clean database schema for setup

## Prerequisites

- PHP 8.1 or higher
- MySQL 8.0+ (or MariaDB equivalent)
- Apache with `mod_headers` enabled

## Steps to Setup the Project

1. Clone the repository:

```bash
git clone <your-repo-url>
cd MediSync
```

2. Create environment file:

```bash
cp .env.example .env
```

3. Update `.env` with your database credentials:

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=medisync
DB_USER=your_db_user
DB_PASS=your_db_password
DB_CHARSET=utf8mb4
```

4. Create database and import schema:

```bash
mysql -u your_db_user -p < database/schema.sql
```

5. Create the first admin user:

```sql
INSERT INTO users (name, dob, gender, age, contact, email, password, blood_group, role)
VALUES (
  'Admin User',
  '1990-01-01',
  'Other',
  35,
  '0000000000',
  'admin@example.com',
  '$2y$10$Q7vA0F4wW9sY2H0m9w2dEuEFmG3vN8z0vY9QKQvGfbc4fmd7wQ6sK',
  'O+',
  'admin'
);
```

Default password for this hash: `Admin@123`

6. Ensure upload directory is writable:

```bash
chmod -R 775 uploads/doctors
```

7. Run the project on Apache:

- Set your Apache document root to this project folder, or
- Place the project in your web root and open it in browser:

```text
http://localhost/MediSync
```

## Notes

- Keep `.env` private and never commit it.
- Use HTTPS in production.
- Use `database/schema.sql` for clean setup.
- Older SQL dump files are development snapshots.
