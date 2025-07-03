#!/bin/bash

# BillSmart API Development Helper Script

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if PostgreSQL is running
check_postgres() {
    if pg_isready -h localhost -p 5432 > /dev/null 2>&1; then
        print_status "PostgreSQL is running"
        return 0
    else
        print_error "PostgreSQL is not running"
        return 1
    fi
}

# Function to create database
setup_database() {
    print_status "Setting up database..."
    
    # Check if database exists
    if psql -lqt | cut -d \| -f 1 | grep -qw billsmart_db; then
        print_warning "Database 'billsmart_db' already exists"
    else
        createdb billsmart_db
        print_status "Database 'billsmart_db' created"
    fi
    
    # Check if user exists
    if psql -t -c '\du' | cut -d \| -f 1 | grep -qw billsmart_user; then
        print_warning "User 'billsmart_user' already exists"
    else
        psql -c "CREATE USER billsmart_user WITH PASSWORD 'your_secure_password';"
        psql -c "GRANT ALL PRIVILEGES ON DATABASE billsmart_db TO billsmart_user;"
        print_status "User 'billsmart_user' created and granted permissions"
    fi
    
    # Apply schema
    if [ -f "database_schema.sql" ]; then
        psql -U billsmart_user -d billsmart_db -f database_schema.sql
        print_status "Database schema applied"
    else
        print_error "database_schema.sql not found"
    fi
}

# Function to install dependencies
install_deps() {
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    print_status "Dependencies installed"
}

# Function to run migrations
run_migrations() {
    print_status "Running database migrations..."
    
    # Check if alembic is initialized
    if [ ! -d "alembic/versions" ]; then
        print_warning "Alembic not initialized. Creating initial migration..."
        alembic revision --autogenerate -m "Initial migration"
    fi
    
    alembic upgrade head
    print_status "Migrations completed"
}

# Function to start the server
start_server() {
    print_status "Starting FastAPI server..."
    python run_server.py
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    pytest test_main.py -v
}

# Function to show API docs
show_docs() {
    print_status "API Documentation available at:"
    echo "  - Swagger UI: http://localhost:8000/docs"
    echo "  - ReDoc: http://localhost:8000/redoc"
    echo "  - Health Check: http://localhost:8000/health"
}

# Main script logic
case "$1" in
    "setup")
        print_status "Setting up BillSmart API development environment..."
        install_deps
        if check_postgres; then
            setup_database
            run_migrations
        else
            print_error "Please start PostgreSQL first"
            exit 1
        fi
        print_status "Setup complete!"
        show_docs
        ;;
    "start"|"run")
        if check_postgres; then
            start_server
        else
            print_error "Please start PostgreSQL first"
            exit 1
        fi
        ;;
    "test")
        run_tests
        ;;
    "migrate")
        run_migrations
        ;;
    "docs")
        show_docs
        ;;
    "docker")
        print_status "Starting with Docker Compose..."
        docker-compose up --build
        ;;
    "docker-down")
        print_status "Stopping Docker services..."
        docker-compose down
        ;;
    *)
        echo "BillSmart API Development Helper"
        echo ""
        echo "Usage: $0 {setup|start|test|migrate|docs|docker|docker-down}"
        echo ""
        echo "Commands:"
        echo "  setup       - Install dependencies and set up database"
        echo "  start|run   - Start the development server"
        echo "  test        - Run tests"
        echo "  migrate     - Run database migrations"
        echo "  docs        - Show API documentation URLs"
        echo "  docker      - Start with Docker Compose"
        echo "  docker-down - Stop Docker services"
        echo ""
        exit 1
        ;;
esac
