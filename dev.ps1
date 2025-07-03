# BillSmart API Development Helper Script for Windows PowerShell

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("setup", "start", "run", "test", "migrate", "docs", "docker", "docker-down", "reset-db")]
    [string]$Command
)

# Function to print colored output
function Write-Status {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Function to check if MySQL is running
function Test-MySQL {
    try {
        $result = & mysql -u root -e "SELECT 1;" 2>$null
        if ($LASTEXITCODE -eq 0) {
            Write-Status "MySQL is running"
            return $true
        } else {
            Write-Error "MySQL is not running"
            return $false
        }
    } catch {
        Write-Error "MySQL is not running or mysql client not found"
        return $false
    }
}

# Function to create database
function Setup-Database {
    Write-Status "Setting up database..."
    
    # Create database
    Write-Status "Creating database 'billsmart_db'..."
    & mysql -u root -e "CREATE DATABASE IF NOT EXISTS billsmart_db;"
    
    # Create user (optional, can use root for local development)
    Write-Status "Setting up database user..."
    & mysql -u root -e "CREATE USER IF NOT EXISTS 'billsmart_user'@'localhost' IDENTIFIED BY 'your_secure_password';"
    & mysql -u root -e "GRANT ALL PRIVILEGES ON billsmart_db.* TO 'billsmart_user'@'localhost';"
    & mysql -u root -e "FLUSH PRIVILEGES;"
    
    # Apply schema using Python script
    Write-Status "Creating database tables..."
    & python create_database.py
}

# Function to install dependencies
function Install-Dependencies {
    Write-Status "Installing Python dependencies..."
    & pip install -r requirements.txt
    Write-Status "Dependencies installed"
}

# Function to run migrations
function Invoke-Migrations {
    Write-Status "Running database migrations..."
    
    # Check if alembic is initialized
    if (!(Test-Path "alembic\versions")) {
        Write-Warning "Alembic not initialized. Creating initial migration..."
        & alembic revision --autogenerate -m "Initial migration"
    }
    
    & alembic upgrade head
    Write-Status "Migrations completed"
}

# Function to start the server
function Start-Server {
    Write-Status "Starting FastAPI server..."
    & python run_server.py
}

# Function to run tests
function Invoke-Tests {
    Write-Status "Running tests..."
    & pytest test_main.py -v
}

# Function to show API docs
function Show-Documentation {
    Write-Status "API Documentation available at:"
    Write-Host "  - Swagger UI: http://localhost:8000/docs"
    Write-Host "  - ReDoc: http://localhost:8000/redoc"
    Write-Host "  - Health Check: http://localhost:8000/health"
}

# Main script logic
switch ($Command) {
    "setup" {
        Write-Status "Setting up BillSmart API development environment..."
        Install-Dependencies
        if (Test-MySQL) {
            Setup-Database
        } else {
            Write-Error "Please start MySQL first"
            exit 1
        }
        Write-Status "Setup complete!"
        Show-Documentation
    }
    
    "start" {
        if (Test-MySQL) {
            Start-Server
        } else {
            Write-Error "Please start MySQL first"
            exit 1
        }
    }
    
    "run" {
        if (Test-MySQL) {
            Start-Server
        } else {
            Write-Error "Please start MySQL first"
            exit 1
        }
    }
    
    "test" {
        Invoke-Tests
    }
    
    "reset-db" {
        Write-Status "Resetting database..."
        & mysql -u root -e "DROP DATABASE IF EXISTS billsmart_db;"
        Setup-Database
        Write-Status "Database reset complete!"
    }
    
    "docs" {
        Show-Documentation
    }
    
    "docker" {
        Write-Status "Starting with Docker Compose..."
        & docker-compose up --build
    }
    
    "docker-down" {
        Write-Status "Stopping Docker services..."
        & docker-compose down
    }
}

# Usage information
if ($Command -eq "help" -or $Command -eq "" -or $null -eq $Command) {
    Write-Host "BillSmart API Development Helper for Windows"
    Write-Host ""
    Write-Host "Usage: .\dev.ps1 -Command <command>"
    Write-Host ""
    Write-Host "Commands:"
    Write-Host "  setup       - Install dependencies and set up database"
    Write-Host "  start|run   - Start the development server"
    Write-Host "  test        - Run tests"
    Write-Host "  migrate     - Run database migrations"
    Write-Host "  docs        - Show API documentation URLs"
    Write-Host "  docker      - Start with Docker Compose"
    Write-Host "  docker-down - Stop Docker services"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\dev.ps1 -Command setup"
    Write-Host "  .\dev.ps1 -Command start"
    Write-Host "  .\dev.ps1 -Command test"
}
