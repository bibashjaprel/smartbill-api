# 🚀 BillSmart API Deployment Guide

## Issues Fixed

### ✅ Product Stock Attribute Error
- **Problem**: `'Product' object has no attribute 'stock'`
- **Solution**: Updated `convert_product_for_frontend()` to use `product.stock_quantity`
- **Location**: `app/utils/api.py`

### ✅ Docker Configuration
- **Updated**: Dockerfile to use MySQL instead of PostgreSQL
- **Updated**: docker-compose.yml with health checks and better configuration

## Quick Start (Fixed Version)

### 1. Local Development
```bash
# Clone and setup
git clone <repository-url>
cd smartbill-api
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Setup environment
cp .env.example .env
# Edit .env with your configuration

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. Docker Development
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Access services
# API: http://localhost:8000
# Database UI: http://localhost:8080
```

### 3. Test the Fixed API
```bash
# Test products endpoint
python test_products_endpoint.py

# Or manually test
curl -X GET "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Production Deployment

### Environment Variables
```env
# Required
DATABASE_URL=mysql+pymysql://user:pass@host:3306/dbname
SECRET_KEY=your-super-secret-key

# Optional
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-secret
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Docker Production
```bash
# Build production image
docker build -t billsmart-api:latest .

# Run with production settings
docker run -d \
  --name billsmart-api \
  -p 8000:8000 \
  --env-file .env \
  billsmart-api:latest
```

### Cloud Deployment

#### AWS ECS
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker tag billsmart-api:latest ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/billsmart-api:latest
docker push ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/billsmart-api:latest
```

#### Heroku
```bash
# Login and create app
heroku login
heroku create your-app-name

# Set environment variables
heroku config:set DATABASE_URL=your-database-url
heroku config:set SECRET_KEY=your-secret-key

# Deploy
git push heroku main
```

#### DigitalOcean App Platform
1. Connect GitHub repository
2. Set environment variables in dashboard
3. Deploy automatically

## Verification

### Health Check
```bash
# Check API health
curl http://localhost:8000/health

# Check API docs
curl http://localhost:8000/docs
```

### API Testing
```bash
# Register user
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","full_name":"Test User"}'

# Login
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123"}'

# Get products (with token)
curl -X GET "http://localhost:8000/api/v1/products/" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Monitoring

### Logs
```bash
# Docker logs
docker-compose logs -f api

# Application logs
tail -f logs/app.log
```

### Metrics
- Response times
- Error rates
- Database connections
- Memory usage

## Support

- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Database UI**: http://localhost:8080 (in development)

---

**✅ All stock attribute errors have been resolved!**
**🚀 Ready for production deployment!**
