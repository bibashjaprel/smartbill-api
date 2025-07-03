# BillSmart API

A FastAPI-based backend for a smart billing system with advanced authentication, customer management, product catalog, and bill generation.

## 🚀 Features

- 🔐 **Advanced Authentication System**
  - Email-based login (no username required)
  - Email verification for new registrations
  - Google OAuth Sign-In integration
  - JWT token-based authentication
  
- 👥 **User Management**
  - User registration with email verification
  - Profile management with Google integration
  - Secure password hashing
  
- 🏪 **Shop Management**
  - Multiple shops per user
  - Shop details and configuration
  
- 👤 **Customer Management**
  - Customer profiles and contact information
  - Udharo (credit) balance tracking
  
- 📦 **Product Catalog**
  - Product management with pricing
  - Inventory tracking
  
- 🧾 **Billing System**
  - Bill generation and management
  - Udharo transaction tracking
  - Payment status tracking

- 📧 **Email System**
  - Automated verification emails
  - SMTP configuration support
  - Beautiful HTML email templates

## 🛠️ Tech Stack

- **Framework**: FastAPI
- **Database**: MySQL
- **Authentication**: JWT + Google OAuth
- **ORM**: SQLAlchemy
- **Email**: aiosmtplib + Jinja2 templates
- **Validation**: Pydantic
- **Testing**: pytest

## 🏃‍♂️ Quick Start

### Prerequisites

- Python 3.8+
- MySQL 8.0+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd smartbill-api
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   
   Edit `.env` with your configuration:
   ```env
   # Database
   DATABASE_URL=mysql+pymysql://root:@localhost:3306/billsmart_db
   
   # Security
   SECRET_KEY=your-super-secret-key-change-this-in-production
   
   # Google OAuth (optional)
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   
   # Email settings (optional)
   SMTP_HOST=smtp.gmail.com
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   EMAILS_FROM_EMAIL=your-email@gmail.com
   ```

4. **Set up the database**
   ```bash
   # Windows PowerShell
   .\dev.ps1 setup
   
   # Or manually with Python
   python setup_mysql.py
   ```

5. **Start the server**
   ```bash
   # Windows PowerShell
   .\dev.ps1 start
   
   # Or manually
   python run_server.py
   ```

6. **Visit the API docs**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## 🔐 Authentication

### Registration Flow
1. User registers with email/password
2. System sends verification email
3. User clicks verification link
4. User can now login

### Login Options
- **Email/Password**: Regular login with email verification required
- **Google OAuth**: Instant login with Google account (no verification needed)

### API Endpoints

- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (OAuth2 compatible)
- `POST /api/v1/auth/login-email` - Direct email login
- `POST /api/v1/auth/google/login` - Google OAuth login
- `POST /api/v1/auth/verify-email` - Verify email address
- `POST /api/v1/auth/resend-verification` - Resend verification email

## 🛠️ Development Commands

Using the PowerShell development script:

```bash
# Setup development environment
.\dev.ps1 setup

# Start development server
.\dev.ps1 start

# Run tests
.\dev.ps1 test

# Reset database
.\dev.ps1 reset-db

# View documentation
.\dev.ps1 docs
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run API tests
python test_auth.py

# Run unit tests
pytest

# Test specific functionality
pytest tests/test_auth.py -v
```

## ⚙️ Configuration

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Add your domain to authorized origins
4. Copy Client ID and Secret to `.env`

### Email Provider Setup

#### Gmail
1. Enable 2FA on your Google account
2. Generate an App Password
3. Use the App Password in `SMTP_PASSWORD`

#### Other Providers
Update SMTP settings in `.env` for your provider (SendGrid, Mailgun, AWS SES, etc.)

## 📚 API Documentation

The API is fully documented with OpenAPI/Swagger:

- **Interactive docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📁 Project Structure

```
smartbill-api/
├── app/
│   ├── api/
│   │   ├── deps.py              # Dependencies
│   │   └── v1/
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── users.py         # User management
│   │       ├── shops.py         # Shop management
│   │       ├── customers.py     # Customer management
│   │       ├── products.py      # Product management
│   │       └── bills.py         # Bill management
│   ├── core/
│   │   ├── config.py            # Configuration
│   │   ├── database.py          # Database setup
│   │   ├── security.py          # Security utilities
│   │   ├── email.py             # Email utilities
│   │   └── google_auth.py       # Google OAuth utilities
│   ├── crud/                    # Database operations
│   ├── models/                  # SQLAlchemy models
│   ├── schemas/                 # Pydantic schemas
│   └── main.py                  # FastAPI app
├── database_schema.sql          # Database schema
├── setup_mysql.py              # Database setup script
├── run_server.py               # Server entry point
├── test_auth.py                # Authentication tests
├── dev.ps1                     # Development helper script
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── AUTH_SETUP.md              # Authentication setup guide
└── README.md                  # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions and support:
- Check the [Authentication Setup Guide](AUTH_SETUP.md)
- Review the API documentation at `/docs`
- Create an issue on GitHub

## 🎯 Next Steps

- Set up your Google OAuth credentials for Google Sign-In
- Configure your email provider for verification emails
- Customize the email templates in `app/core/email.py`
- Add your frontend domain to CORS settings
- Deploy to your preferred hosting platform

---

**Built with ❤️ using FastAPI**
