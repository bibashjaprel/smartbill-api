import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from jinja2 import Template
from .config import settings


async def send_email(
    email_to: str,
    subject: str,
    html_content: str,
    text_content: Optional[str] = None,
) -> None:
    """Send an email"""
    if not settings.SMTP_HOST:
        print(f"Email sending disabled - would send to {email_to}: {subject}")
        return
    
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
    message["To"] = email_to

    if text_content:
        text_part = MIMEText(text_content, "plain")
        message.attach(text_part)

    html_part = MIMEText(html_content, "html")
    message.attach(html_part)

    await aiosmtplib.send(
        message,
        hostname=settings.SMTP_HOST,
        port=settings.SMTP_PORT,
        start_tls=settings.SMTP_TLS,
        username=settings.SMTP_USER,
        password=settings.SMTP_PASSWORD,
    )


def generate_verification_email(email: str, token: str, user_name: str) -> tuple[str, str]:
    """Generate email verification email content"""
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    html_template = Template("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Verify Your Email - {{ project_name }}</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #4CAF50;">Welcome to {{ project_name }}!</h2>
            <p>Hi {{ user_name }},</p>
            <p>Thank you for signing up! Please verify your email address by clicking the button below:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ verification_url }}" 
                   style="background-color: #4CAF50; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                   Verify Email Address
                </a>
            </div>
            
            <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{{ verification_url }}</p>
            
            <p>This verification link will expire in {{ expire_hours }} hours.</p>
            
            <p>If you didn't create an account with us, you can safely ignore this email.</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">
                This email was sent by {{ project_name }}. If you have any questions, please contact our support team.
            </p>
        </div>
    </body>
    </html>
    """)
    
    text_template = Template("""
    Welcome to {{ project_name }}!

    Hi {{ user_name }},

    Thank you for signing up! Please verify your email address by visiting this link:
    {{ verification_url }}

    This verification link will expire in {{ expire_hours }} hours.

    If you didn't create an account with us, you can safely ignore this email.

    ---
    {{ project_name }} Team
    """)
    
    context = {
        "project_name": settings.PROJECT_NAME,
        "user_name": user_name or "there",
        "verification_url": verification_url,
        "expire_hours": settings.EMAIL_VERIFICATION_TOKEN_EXPIRE_HOURS,
    }
    
    html_content = html_template.render(**context)
    text_content = text_template.render(**context)
    
    return html_content, text_content


async def send_verification_email(email: str, token: str, user_name: str) -> None:
    """Send email verification email"""
    html_content, text_content = generate_verification_email(email, token, user_name)
    
    await send_email(
        email_to=email,
        subject=f"Verify your email - {settings.PROJECT_NAME}",
        html_content=html_content,
        text_content=text_content,
    )


def generate_password_reset_email(email: str, token: str, user_name: str) -> tuple[str, str]:
    """Generate password reset email content"""
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    
    html_template = Template("""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Reset Your Password - {{ project_name }}</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
            <h2 style="color: #FF6B35;">Password Reset Request</h2>
            <p>Hi {{ user_name }},</p>
            <p>You recently requested to reset your password for your {{ project_name }} account. Click the button below to reset it:</p>
            
            <div style="text-align: center; margin: 30px 0;">
                <a href="{{ reset_url }}" 
                   style="background-color: #FF6B35; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;">
                   Reset Password
                </a>
            </div>
            
            <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
            <p style="word-break: break-all; color: #666;">{{ reset_url }}</p>
            
            <p><strong>This password reset link will expire in {{ expire_hours }} hours.</strong></p>
            
            <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
            
            <hr style="margin: 30px 0; border: none; border-top: 1px solid #eee;">
            <p style="color: #666; font-size: 12px;">
                This email was sent by {{ project_name }}. If you have any questions, please contact our support team.
            </p>
        </div>
    </body>
    </html>
    """)
    
    text_template = Template("""
    Password Reset Request - {{ project_name }}

    Hi {{ user_name }},

    You recently requested to reset your password for your {{ project_name }} account. 
    
    Click this link to reset your password:
    {{ reset_url }}

    This password reset link will expire in {{ expire_hours }} hours.

    If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.

    ---
    {{ project_name }} Team
    """)
    
    context = {
        "project_name": settings.PROJECT_NAME,
        "user_name": user_name or "there",
        "reset_url": reset_url,
        "expire_hours": settings.PASSWORD_RESET_TOKEN_EXPIRE_HOURS,
    }
    
    html_content = html_template.render(**context)
    text_content = text_template.render(**context)
    
    return html_content, text_content


async def send_password_reset_email(email: str, token: str, user_name: str) -> None:
    """Send password reset email"""
    html_content, text_content = generate_password_reset_email(email, token, user_name)
    
    await send_email(
        email_to=email,
        subject=f"Reset your password - {settings.PROJECT_NAME}",
        html_content=html_content,
        text_content=text_content,
    )
