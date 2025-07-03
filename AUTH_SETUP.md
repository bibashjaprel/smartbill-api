# Authentication & Email Verification Setup

## Overview

The BillSmart API now supports:
1. **Email-based authentication** (instead of username)
2. **Email verification** for new registrations
3. **Google OAuth Sign-In**
4. **Email verification system**

## API Endpoints

### 1. Registration with Email Verification
- **POST** `/api/v1/auth/register`
- Creates a new user account and sends a verification email
- User must verify email before login is allowed

### 2. Email Login (OAuth2 Compatible)
- **POST** `/api/v1/auth/login` 
- Uses OAuth2PasswordRequestForm (put email in the "username" field)
- Requires email verification to be completed

### 3. Email Login (Direct)
- **POST** `/api/v1/auth/login-email`
- Direct email/password login with JSON body
- Requires email verification to be completed

### 4. Google OAuth Login
- **POST** `/api/v1/auth/google/login`
- Login with Google OAuth token
- No email verification required (Google pre-verifies)

### 5. Email Verification
- **POST** `/api/v1/auth/verify-email`
- Verify email address with token received via email

### 6. Resend Verification
- **POST** `/api/v1/auth/resend-verification`
- Resend verification email to a user

### 7. Forgot Password
- **POST** `/api/v1/auth/forgot-password`
- Send password reset email to user
- Only works for verified users with password-based accounts

### 8. Reset Password
- **POST** `/api/v1/auth/reset-password`
- Reset password using token from email
- Validates password strength requirements

## Environment Configuration

Add these to your `.env` file:

```env
# Google OAuth (Get from Google Cloud Console)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Email settings (Configure with your SMTP provider)
SMTP_TLS=true
SMTP_PORT=587
SMTP_HOST=smtp.gmail.com
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
EMAILS_FROM_EMAIL=your-email@gmail.com
EMAILS_FROM_NAME=BillSmart Team

# Frontend URL for email verification links
FRONTEND_URL=http://localhost:3000

# Email verification
EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS=24

# Password reset
PASSWORD_RESET_TOKEN_EXPIRE_HOURS=2
```

## Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials
5. Add your domain to authorized origins
6. Add your frontend URLs to authorized redirect URIs
7. Copy Client ID and Client Secret to your `.env` file

## Email Provider Setup

### Gmail Setup
1. Enable 2-factor authentication on your Gmail account
2. Generate an App Password for your application
3. Use the App Password in `SMTP_PASSWORD`

### Other Providers
The system supports any SMTP provider. Update the SMTP settings accordingly:
- **SendGrid**: Use API key as password with SMTP
- **Mailgun**: Use Mailgun SMTP credentials
- **AWS SES**: Use SES SMTP credentials

## Testing the API

### 1. Test Registration
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "testpassword123",
       "full_name": "Test User"
     }'
```

### 2. Test Email Login (OAuth2 Form)
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=test@example.com&password=testpassword123"
```

### 3. Test Direct Email Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login-email" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "testpassword123"
     }'
```

### 4. Test Google Login
```bash
curl -X POST "http://localhost:8000/api/v1/auth/google/login" \
     -H "Content-Type: application/json" \
     -d '{
       "token": "google-oauth-token-here"
     }'
```

### 5. Test Forgot Password
```bash
curl -X POST "http://localhost:8000/api/v1/auth/forgot-password" \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com"
     }'
```

### 6. Test Reset Password
```bash
curl -X POST "http://localhost:8000/api/v1/auth/reset-password" \
     -H "Content-Type: application/json" \
     -d '{
       "token": "reset-token-from-email",
       "new_password": "newpassword123"
     }'
```

## Database Changes

The user table now includes:
- `is_verified` (BOOLEAN): Email verification status
- `google_id` (VARCHAR): Google OAuth user ID
- `profile_picture` (VARCHAR): Profile picture URL
- `password_hash` is now nullable for OAuth users

## Frontend Integration

### Email Verification Flow
1. User registers → receives verification email
2. User clicks link in email → redirects to frontend with token
3. Frontend calls `/api/v1/auth/verify-email` with token
4. User can now login

### Google OAuth Flow
1. Frontend uses Google OAuth library to get token
2. Frontend sends token to `/api/v1/auth/google/login`
3. Backend verifies token and creates/logs in user
4. User is immediately logged in (no email verification needed)

### Password Reset Flow
1. User requests password reset → receives reset email
2. User clicks link in email → redirects to frontend with token
3. Frontend calls `/api/v1/auth/reset-password` with token and new password
4. User can now login with new password

## Error Handling

The API returns appropriate error messages for:
- Invalid credentials
- Unverified email addresses
- Expired verification tokens
- Invalid Google tokens
- Duplicate email registrations
- Invalid or expired password reset tokens
- Password strength validation
- OAuth users trying to reset password

## Security Notes

- Email verification tokens expire after 24 hours
- Password reset tokens expire after 2 hours  
- Access tokens expire after 30 minutes (configurable)
- Google OAuth tokens are verified with Google's servers
- Password hashing uses bcrypt
- Password reset requires minimum 8 character length
- OAuth users cannot use password reset (must use Google Sign-In)
- All endpoints support CORS for frontend integration
