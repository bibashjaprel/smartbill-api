# MySQL Setup Guide for BillSmart API

## Prerequisites

Make sure you have MySQL installed on your system:

### Windows
- Download MySQL from: https://dev.mysql.com/downloads/mysql/
- Or use XAMPP: https://www.apachefriends.org/

### macOS
```bash
brew install mysql
brew services start mysql
```

### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install mysql-server
sudo systemctl start mysql
```

## Setup Steps

### 1. Install Python Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Start MySQL Service
Make sure MySQL is running on your system.

### 3. Create Database
```sql
-- Login to MySQL as root
mysql -u root -p

-- Create database
CREATE DATABASE billsmart_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (optional - you can also use root)
CREATE USER 'billsmart_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON billsmart_db.* TO 'billsmart_user'@'localhost';
FLUSH PRIVILEGES;

-- Exit MySQL
EXIT;
```

### 4. Configure Environment
Update the `.env` file:
```env
# For root user (no password)
DATABASE_URL=mysql+pymysql://root:@localhost:3306/billsmart_db

# For custom user
DATABASE_URL=mysql+pymysql://billsmart_user:your_secure_password@localhost:3306/billsmart_db
```

### 5. Create Tables
```powershell
python create_database.py
```

### 6. Start the API Server
```powershell
python run_server.py
```

## Using Helper Scripts

### PowerShell (Windows)
```powershell
# Complete setup
.\dev.ps1 -Command setup

# Start server
.\dev.ps1 -Command start

# Reset database
.\dev.ps1 -Command reset-db

# Run tests
.\dev.ps1 -Command test

# Show documentation URLs
.\dev.ps1 -Command docs
```

### Docker (Alternative)
```powershell
# Start everything with Docker
docker-compose up --build

# Stop services
docker-compose down
```

## Verification

1. Check if the API is running: http://localhost:8000/health
2. View API documentation: http://localhost:8000/docs
3. Test the endpoints using the Swagger UI

## Troubleshooting

### Common Issues

1. **"Access denied for user" error**
   - Check your MySQL credentials in the `.env` file
   - Make sure the user has proper permissions

2. **"Can't connect to MySQL server" error**
   - Ensure MySQL service is running
   - Check if MySQL is listening on port 3306

3. **"Unknown database" error**
   - Make sure you created the `billsmart_db` database
   - Run the database creation commands again

4. **Import errors**
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Check if you're in the correct virtual environment

### MySQL Commands

```sql
-- Check if database exists
SHOW DATABASES;

-- Check if user exists
SELECT User, Host FROM mysql.user;

-- Check table structure
DESCRIBE users;

-- View all tables
SHOW TABLES;

-- Check MySQL version
SELECT VERSION();
```

### Reset Everything
If you need to start fresh:

```sql
-- Drop the database
DROP DATABASE IF EXISTS billsmart_db;

-- Recreate it
CREATE DATABASE billsmart_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Then run `python create_database.py` again.

## Performance Tips

1. **Indexes**: The schema includes proper indexes for better query performance
2. **Connection Pooling**: SQLAlchemy handles connection pooling automatically
3. **Query Optimization**: Use the provided CRUD methods which include optimized queries

## Security Notes

1. **Production**: Change default passwords and use environment variables
2. **SSL**: Enable SSL for production MySQL connections
3. **Firewall**: Restrict MySQL access to localhost only for development
4. **Backup**: Regular database backups for production
