# BillSmart API

A production-ready FastAPI backend for a multi-tenant smart billing + inventory SaaS with authentication, customer management, invoice accounting, subscriptions, and business analytics.

## 🚀 Features

### 🔐 **Advanced Authentication System**
- Email-based login (no username required)
- Email verification for new registrations
- Google OAuth Sign-In integration
- JWT token-based authentication
- Password reset functionality
- Admin and vendor role separation

### 👥 **User Management**
- User registration with email verification
- Profile management with Google integration
- Secure password hashing with bcrypt
- User roles and permissions

### 🏪 **Shop Management**
- Multiple shops per user support
- Shop details and configuration
- Shop ownership validation

### 👤 **Customer Management**
- Customer profiles and contact information
- Customer credit ledger based on invoice dues
- Customer payment history via invoice payments
- Search and filtering capabilities

### 📦 **Product Catalog**
- Product management with pricing and cost tracking
- Inventory tracking with stock levels
- Low stock alerts
- Product categories and SKU management
- Search functionality

### 🧾 **Billing System**
- Invoice generation and management
- Invoice payment tracking
- Credit (due) tracking from unpaid/partial invoices
- Invoice history and analytics

### 💳 **Subscriptions**
- Plan management (monthly/yearly)
- Shop subscription lifecycle
- Subscription payment tracking
- Feature access checks by plan limits

### 📊 **Business Analytics**
- Dashboard with key metrics
- Monthly sales trends
- Product performance analytics
- Customer analytics
- Export functionality (JSON/CSV)

### 📧 **Email System**
- Automated verification emails
- SMTP configuration support
- Beautiful HTML email templates
- Password reset emails

## 🛠️ Tech Stack

- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 12+
- Node.js (optional, for development)
- **Authentication**: JWT + Google OAuth 2.0
- **ORM**: SQLAlchemy 2.0
- **Email**: aiosmtplib + Jinja2 templates
- **Validation**: Pydantic v2
- **Security**: bcrypt, python-jose
- **HTTP Client**: httpx
- **CORS**: FastAPI CORS middleware

## 🏃‍♂️ Quick Start

### Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd smartbill-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create `.env` file with your configuration:
   ```env
   # Database
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=your-db-password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=billsmart_db
   
   # Security
   SECRET_KEY=your-super-secret-key-change-this-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Google OAuth (optional)
   GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-google-client-secret
   
   # Email settings (optional)
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password
   EMAILS_FROM_EMAIL=your-email@gmail.com
   EMAILS_FROM_NAME="BillSmart"
   
   # Frontend URL (for CORS)
   FRONTEND_URL=http://localhost:3000
   ```

5. **Set up the database**
   ```bash
   # Create database and tables
   python -c "from app.core.database import init_db; init_db()"
   ```

6. **Start the server**
   ```bash
   # Development server
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   
   # Or using the start script
   python start_server.py
   ```

7. **Visit the API**
   - Server: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Quick Test

Create an admin user and test the API:

```bash
# Create admin user (optional)
python -c "
from app.core.database import get_db
from app.crud.user import user as crud_user
from app.schemas.user import UserCreate
from app.core.security import get_password_hash

db = next(get_db())
admin = UserCreate(
    email='admin@billsmart.com',
    password='admin123',
    full_name='Admin User',
    is_verified=True
)
crud_user.create(db, obj_in=admin)
print('Admin user created: admin@billsmart.com / admin123')
"
```

## 🔐 Authentication & Authorization

### Authentication Flow
1. **Registration**: User registers with email/password
2. **Email Verification**: System sends verification email (if SMTP configured)
3. **Login**: User logs in with email/password or Google OAuth
4. **JWT Token**: System returns JWT token for API access

### Available Auth Methods
- **Email/Password Login**: Traditional authentication
- **Google OAuth**: Social login integration
- **JWT Tokens**: Stateless authentication for API calls

### API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register new user
- `POST /api/v1/auth/login` - Login (OAuth2 compatible)
- `POST /api/v1/auth/google/login` - Google OAuth login
- `POST /api/v1/auth/verify-email` - Verify email address
- `POST /api/v1/auth/resend-verification` - Resend verification email
- `POST /api/v1/auth/forgot-password` - Request password reset
- `POST /api/v1/auth/reset-password` - Reset password with token

#### User Management
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile

#### Shop Management
- `GET /api/v1/shops/current` - Get current user's shop
- `POST /api/v1/shops/` - Create new shop
- `PUT /api/v1/shops/{shop_id}` - Update shop

#### Customer Management
- `GET /api/v1/shops/{shop_id}/customers` - List customers
- `POST /api/v1/shops/{shop_id}/customers` - Create customer
- `GET /api/v1/shops/{shop_id}/customers/{customer_id}` - Get customer
- `PUT /api/v1/shops/{shop_id}/customers/{customer_id}` - Update customer
- `DELETE /api/v1/shops/{shop_id}/customers/{customer_id}` - Delete customer

#### Credit Management
- `GET /api/v1/shops/{shop_id}/customers/{customer_id}/credit/summary` - Customer due summary
- `GET /api/v1/shops/{shop_id}/customers/{customer_id}/credit/ledger` - Outstanding invoice ledger
- `POST /api/v1/shops/{shop_id}/customers/{customer_id}/credit/payments` - Apply payment to invoice

#### Product Management
- `GET /api/v1/products/` - List products
- `POST /api/v1/products/` - Create product
- `GET /api/v1/products/{product_id}` - Get product
- `PUT /api/v1/products/{product_id}` - Update product
- `DELETE /api/v1/products/{product_id}` - Delete product
- `PATCH /api/v1/products/{product_id}/stock` - Update stock

#### Invoice Management
- `GET /api/v1/shops/{shop_id}/invoices` - List invoices
- `POST /api/v1/shops/{shop_id}/invoices` - Create invoice
- `POST /api/v1/shops/{shop_id}/invoices/{invoice_id}/payments` - Add invoice payment

#### Subscription Management
- `GET /api/v1/shops/{shop_id}/plans` - List plans
- `GET /api/v1/shops/{shop_id}/subscriptions` - List shop subscriptions
- `POST /api/v1/shops/{shop_id}/subscriptions` - Create subscription
- `POST /api/v1/shops/{shop_id}/subscriptions/{subscription_id}/payments` - Add subscription payment

#### Analytics & Reports
- `GET /api/v1/dashboard/stats` - Dashboard statistics
- `GET /api/v1/dashboard/details` - Detailed dashboard data
- `GET /api/v1/reports/monthly-trends` - Monthly sales trends
- `GET /api/v1/reports/monthly-stats` - Monthly statistics
- `GET /api/v1/reports/top-products` - Top performing products
- `GET /api/v1/reports/export` - Export reports (JSON/CSV)
- `GET /api/v1/audit/logs` - Audit logs (admin/platform)
- `GET /api/v1/notifications` - User notifications

### Local Development

```bash
# Start development server with hot reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run with debug logging
uvicorn app.main:app --reload --log-level debug

# Test API endpoints
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","full_name":"Test User"}'
```

## 🐳 Docker Deployment (Recommended)

This project is configured for a simple and conflict-free Docker flow.

### 1) Prepare environment

```bash
cp .env.example .env
```

Then edit `.env` and set at minimum:
- `POSTGRES_PASSWORD`
- `SECRET_KEY`

### 2) Build and run

```bash
docker compose up --build -d
```

### 3) Verify services

```bash
docker compose ps
curl http://localhost:8000/health
```

### 4) Stop services

```bash
docker compose down
```

### Notes
- API container waits for Postgres, then runs `alembic upgrade head` automatically.
- Ports are configurable via `.env` (`API_PORT`, `DB_PORT`) to avoid local conflicts.
- Do not commit real secrets in `.env`; keep secrets local or in your deployment secret manager.

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py -v

# Run with coverage
pytest --cov=app tests/
```

### Database Management

```bash
# Create tables
python -c "from app.core.database import init_db; init_db()"

# Reset database (⚠️ This will delete all data)
python -c "from app.core.database import reset_db; reset_db()"

# Create admin user
python -c "
from app.core.database import get_db
from app.crud.user import user as crud_user
from app.schemas.user import UserCreate

db = next(get_db())
admin = UserCreate(email='admin@example.com', password='admin123', full_name='Admin')
crud_user.create(db, obj_in=admin)
print('Admin created')
"
```

## 🧪 Testing & Quality Assurance

### API Testing

Test all endpoints with the included test scripts:

```bash
# Test authentication flow
python test_auth.py

# Test customer management
pytest tests/test_saas_services.py -v

# Test product management
python test_products.py

# Test dashboard and analytics
python test_dashboard.py
```

### Manual Testing

Use the interactive API documentation:
1. Start the server: `uvicorn app.main:app --reload`
2. Open browser: http://localhost:8000/docs
3. Test endpoints directly in the Swagger UI

### Production Testing

```bash
# Test with production-like settings
POSTGRES_USER=user \
POSTGRES_PASSWORD=pass \
POSTGRES_HOST=prod-db \
POSTGRES_PORT=5432 \
POSTGRES_DB=billsmart \
SECRET_KEY=production-secret-key \
uvicorn app.main:app --host 0.0.0.0 --port 8000
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
│   │   ├── deps.py              # API dependencies
│   │   └── v1/
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── users.py         # User management
│   │       ├── admin.py         # Admin endpoints
│   │       ├── shops.py         # Shop management
│   │       ├── customers_mgmt.py # Customer management
│   │       ├── credits.py       # Credit ledger endpoints
│   │       ├── products.py      # Product management
│   │       ├── billing.py       # Invoice & payment endpoints
│   │       ├── subscriptions.py # Plan/subscription endpoints
│   │       ├── inventory.py     # Stock and inventory alerts
│   │       ├── notifications.py # Notification endpoints
│   │       ├── audit.py         # Audit endpoints
│   │       ├── dashboard.py     # Dashboard analytics
│   │       └── reports.py       # Reports and exports
│   ├── core/
│   │   ├── config.py            # Configuration settings
│   │   ├── database.py          # Database setup
│   │   ├── security.py          # Security utilities
│   │   ├── email.py             # Email utilities
│   │   └── google_auth.py       # Google OAuth utilities
│   ├── crud/                    # Database operations
│   │   ├── base.py              # Base CRUD operations
│   │   ├── user.py              # User CRUD
│   │   ├── shop.py              # Shop CRUD
│   │   ├── customer.py          # Customer CRUD
│   │   ├── product.py           # Product CRUD
│   │   ├── invoice.py           # Invoice CRUD
│   │   ├── credit.py            # Credit helper CRUD
│   │   ├── subscription.py      # Subscription CRUD
│   │   ├── inventory_alert.py   # Inventory alert CRUD
│   │   ├── notification.py      # Notification CRUD
│   │   └── audit_log.py         # Audit log CRUD
│   ├── models/                  # SQLAlchemy models
│   │   ├── user.py              # User model
│   │   ├── shop.py              # Shop model
│   │   ├── customer.py          # Customer model
│   │   ├── product.py           # Product model
│   │   ├── invoice.py           # Invoice models
│   │   ├── subscription.py      # Subscription models
│   │   ├── inventory_alert.py   # Inventory alert model
│   │   ├── notification.py      # Notification model
│   │   └── audit_log.py         # Audit log model
│   ├── schemas/                 # Pydantic schemas
│   │   ├── user.py              # User schemas
│   │   ├── shop.py              # Shop schemas
│   │   ├── customer.py          # Customer schemas
│   │   ├── product.py           # Product schemas
│   │   ├── invoice.py           # Invoice schemas
│   │   ├── credit.py            # Credit schemas
│   │   ├── subscription.py      # Subscription schemas
│   │   ├── inventory.py         # Inventory schemas
│   │   ├── notification.py      # Notification schemas
│   │   └── audit.py             # Audit schemas
│   ├── utils/                   # Utility functions
│   │   ├── __init__.py          # Utils package
│   │   ├── common.py            # Common utilities
│   │   ├── api.py               # API utilities
│   │   ├── error_handlers.py    # Error handling
│   │   └── README.md            # Utils documentation
│   └── main.py                  # FastAPI app
├── tests/                       # Test files
│   ├── test_auth.py            # Authentication tests
│   ├── test_products.py        # Product tests
│   └── test_saas_services.py   # SaaS services tests (subscriptions/invoices/inventory/credit)
├── database_schema.sql          # Database schema
├── start_server.py             # Server entry point
├── requirements.txt            # Python dependencies
├── .env                        # Environment variables
├── .gitignore                  # Git ignore rules
├── Dockerfile                  # Docker configuration
├── FRONTEND_INTEGRATION_README.md  # Frontend integration guide
├── CODE_REFINEMENT_SUMMARY.md # Code refinement summary
└── README.md                   # This file
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DATABASE_URL` | Yes | - | PostgreSQL connection string |
| `SECRET_KEY` | Yes | - | JWT secret key |
| `ALGORITHM` | No | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | `30` | Token expiration time |
| `GOOGLE_CLIENT_ID` | No | - | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | No | - | Google OAuth client secret |
| `SMTP_HOST` | No | - | SMTP server host |
| `SMTP_PORT` | No | `587` | SMTP server port |
| `SMTP_USER` | No | - | SMTP username |
| `SMTP_PASSWORD` | No | - | SMTP password |
| `EMAILS_FROM_EMAIL` | No | - | From email address |
| `EMAILS_FROM_NAME` | No | `BillSmart` | From name |
| `FRONTEND_URL` | No | `http://localhost:3000` | Frontend URL for CORS |

### Database Configuration

The application uses PostgreSQL with the following configuration:
- **Engine**: PostgreSQL 12+
- **Driver**: psycopg2-binary
- **Connection Pool**: SQLAlchemy connection pooling
- **Migrations**: Alembic (`alembic/versions/*`)

### Security Configuration

- **Password Hashing**: bcrypt with salt rounds
- **JWT Tokens**: RS256 algorithm (configurable)
- **CORS**: Configured for frontend integration
- **Rate Limiting**: Can be added with slowapi
- **Input Validation**: Pydantic schemas

## 🚀 Deployment

### Production Deployment

1. **Environment Setup**
   ```bash
   # Set production environment variables
   export POSTGRES_USER=user
   export POSTGRES_PASSWORD=pass
   export POSTGRES_HOST=prod-db
   export POSTGRES_PORT=5432
   export POSTGRES_DB=billsmart
   export SECRET_KEY=your-production-secret-key
   export FRONTEND_URL=https://your-frontend-domain.com
   ```

2. **Database Setup**
   ```bash
   # Create production database
   python -c "from app.core.database import init_db; init_db()"
   ```

3. **Start Production Server**
   ```bash
   # Using Gunicorn (recommended)
   pip install gunicorn
   gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
   
   # Or using Uvicorn
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t billsmart-api .
docker run -p 8000:8000 --env-file .env billsmart-api
```

### Cloud Deployment

#### AWS
- **Elastic Beanstalk**: Deploy with `eb init` and `eb deploy`
- **ECS**: Use Docker container with AWS ECS
- **Lambda**: Use Mangum for serverless deployment

#### Heroku
```bash
# Install Heroku CLI and login
heroku create your-app-name
heroku config:set DATABASE_URL=your-database-url
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
```

#### DigitalOcean
- **App Platform**: Deploy directly from GitHub
- **Droplet**: Use traditional VPS deployment

## 📊 Monitoring & Logging

### Application Monitoring

```python
# Add to main.py for basic monitoring
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url} - {response.status_code} - {process_time:.2f}s")
    return response
```

### Error Tracking

Integrate with error tracking services:
- **Sentry**: `pip install sentry-sdk`
- **Rollbar**: `pip install rollbar`
- **Bugsnag**: `pip install bugsnag`

### Performance Monitoring

- **Application Performance Monitoring (APM)**
- **Database query monitoring**
- **API response time tracking**
- **Error rate monitoring**

## 🤝 Contributing

We welcome contributions to BillSmart API! Here's how to get started:

### Development Workflow

1. **Fork the repository**
   ```bash
   git clone https://github.com/your-username/smartbill-api.git
   cd smartbill-api
   ```

2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up development environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   pip install -r requirements.txt
   ```

4. **Make your changes**
   - Follow the existing code style
   - Add tests for new functionality
   - Update documentation as needed

5. **Run tests**
   ```bash
   pytest
   python test_auth.py
   ```

6. **Submit a pull request**
   - Ensure all tests pass
   - Include a clear description of changes
   - Reference any related issues

### Code Style

- **Python**: Follow PEP 8 guidelines
- **Type Hints**: Use type hints for all functions
- **Docstrings**: Include docstrings for all public functions
- **Error Handling**: Use consistent error handling patterns

### Adding New Features

1. **API Endpoints**: Add to appropriate module in `app/api/v1/`
2. **Database Models**: Add to `app/models/`
3. **Schemas**: Add Pydantic schemas to `app/schemas/`
4. **CRUD Operations**: Add to `app/crud/`
5. **Tests**: Add comprehensive tests

## 🐛 Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Error: Can't connect to PostgreSQL
# Solution: Check PostgreSQL service and credentials
psql -U postgres  # Test connection
```

#### Import Errors
```bash
# Error: ModuleNotFoundError
# Solution: Activate virtual environment
.venv\Scripts\activate
pip install -r requirements.txt
```

#### Email Not Sending
```bash
# Check SMTP settings
# For Gmail: Use App Password, not regular password
# Enable 2FA and generate App Password
```

#### Google OAuth Issues
```bash
# Check Google Console configuration
# Verify redirect URIs
# Check client ID and secret
```

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Run with debug:
```bash
uvicorn app.main:app --reload --log-level debug
```

### Getting Help

1. **Check Documentation**: Review API docs at `/docs`
2. **Search Issues**: Look through GitHub issues
3. **Create Issue**: Report bugs or request features
4. **Discord/Slack**: Join community discussions

## 📋 Roadmap

### Upcoming Features

- [ ] **Advanced Analytics**
  - Sales forecasting
  - Customer behavior analysis
  - Inventory optimization

- [ ] **Multi-tenant Support**
  - Organization-level isolation
  - Role-based access control
  - Subscription management

- [ ] **API Enhancements**
  - GraphQL support
  - Webhook system
  - Rate limiting

- [ ] **Mobile API**
  - Mobile-optimized endpoints
  - Offline sync capabilities
  - Push notifications

- [ ] **Integrations**
  - Payment gateway integration
  - Accounting software sync
  - Third-party app connectors

### Version History

- **v1.0.0** - Initial release with core features
- **v1.1.0** - Added Google OAuth and email verification
- **v1.2.0** - Added analytics and reporting
- **v1.3.0** - Code refinement and production optimization

## 📄 License

This project is licensed under the MIT License:

```
MIT License

Copyright (c) 2025 BillSmart API

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 🆘 Support & Community

### Getting Support

- **Documentation**: Start with this README and API docs
- **GitHub Issues**: Report bugs and request features
- **Stack Overflow**: Tag questions with `billsmart-api`
- **Email**: support@billsmart.com

### Contributing to Documentation

- **API Docs**: Auto-generated from code comments
- **README**: This file - submit PRs for improvements
- **Guides**: Add setup guides for specific platforms
- **Examples**: Add example integrations and use cases

### Community

- **GitHub Discussions**: Share ideas and get help
- **Twitter**: Follow @BillSmartAPI for updates
- **Blog**: Technical articles and tutorials
- **Newsletter**: Monthly updates and tips

## 🎯 Quick Links

- **Live Demo**: [demo.billsmart.com](https://demo.billsmart.com)
- **API Documentation**: [docs.billsmart.com](https://docs.billsmart.com)
- **Frontend Repo**: [github.com/billsmart/frontend](https://github.com/billsmart/frontend)
- **Status Page**: [status.billsmart.com](https://status.billsmart.com)

---

## 🚀 Ready to Get Started?

1. **Clone the repo**: `git clone <repository-url>`
2. **Install dependencies**: `pip install -r requirements.txt`
3. **Set up environment**: Copy `.env.example` to `.env`
4. **Start developing**: `uvicorn app.main:app --reload`
5. **Visit docs**: http://localhost:8000/docs

**Built with ❤️ using FastAPI, SQLAlchemy, and modern Python**

*For detailed setup instructions, see the [Installation Guide](#installation) above.*
