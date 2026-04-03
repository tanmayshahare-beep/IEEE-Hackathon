"""
Flask-Mail OTP Service

Handles OTP generation, sending, and verification for user registration.
"""

import random
import string
from datetime import datetime, timedelta
from typing import Optional, Dict
import hashlib


class OTPService:
    """OTP generation and verification service"""
    
    # In-memory OTP storage (use Redis/MongoDB in production)
    _otp_store: Dict[str, dict] = {}
    
    def __init__(self, app=None):
        self.app = app
        self.mail = None
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        # Get mail instance from app extensions
        self.mail = app.extensions.get('mail')
        if not self.mail:
            from flask_mail import Mail
            self.mail = Mail(app)
    
    def generate_otp(self, length: int = 6) -> str:
        """Generate random numeric OTP"""
        return ''.join(random.choices(string.digits, k=length))
    
    def create_otp(self, email: str) -> str:
        """
        Create OTP for email address
        
        Args:
            email: User's email address
            
        Returns:
            Generated OTP
        """
        # Generate OTP
        otp = self.generate_otp()
        
        # Hash OTP for storage (security)
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        
        # Store OTP with expiry (10 minutes)
        self._otp_store[email] = {
            'otp_hash': otp_hash,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(minutes=10),
            'attempts': 0
        }
        
        return otp
    
    def verify_otp(self, email: str, otp: str) -> bool:
        """
        Verify OTP for email address
        
        Args:
            email: User's email address
            otp: OTP to verify
            
        Returns:
            True if valid, False otherwise
        """
        # Check if OTP exists for email
        if email not in self._otp_store:
            return False
        
        otp_data = self._otp_store[email]
        
        # Check if OTP is expired
        if datetime.utcnow() > otp_data['expires_at']:
            del self._otp_store[email]
            return False
        
        # Check max attempts (5 attempts)
        if otp_data['attempts'] >= 5:
            del self._otp_store[email]
            return False
        
        # Verify OTP
        otp_hash = hashlib.sha256(otp.encode()).hexdigest()
        if otp_hash != otp_data['otp_hash']:
            otp_data['attempts'] += 1
            return False
        
        # OTP verified successfully - clean up
        del self._otp_store[email]
        return True
    
    def resend_otp(self, email: str) -> Optional[str]:
        """
        Resend OTP to email (if still within expiry window)
        
        Args:
            email: User's email address
            
        Returns:
            New OTP if successful, None otherwise
        """
        # Check if there's an existing OTP
        if email not in self._otp_store:
            return None
        
        otp_data = self._otp_store[email]
        
        # Check if expired
        if datetime.utcnow() > otp_data['expires_at']:
            del self._otp_store[email]
            return None
        
        # Generate new OTP
        return self.create_otp(email)
    
    def send_otp_email(self, email: str, otp: str, username: str) -> bool:
        """
        Send OTP via email
        
        Args:
            email: Recipient email
            otp: OTP code
            username: User's name
            
        Returns:
            True if sent successfully
        """
        try:
            from flask_mail import Message
            
            msg = Message(
                subject='🌾 AgroDoc-AI - Email Verification OTP',
                recipients=[email],
                html=f'''
                <html>
                <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                        <div style="background: linear-gradient(135deg, #eab308, #facc15); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
                            <h1 style="color: #1c1917; margin: 0;">🌾 AgroDoc-AI</h1>
                            <p style="color: #1c1917; margin: 10px 0 0 0;">AI-Powered Plant Disease Detection</p>
                        </div>
                        
                        <div style="background: #f9fafb; padding: 30px; border-radius: 0 0 10px 10px;">
                            <h2 style="color: #1f2937;">Email Verification</h2>
                            
                            <p>Hello <strong>{username}</strong>,</p>
                            
                            <p>Thank you for registering with AgroDoc-AI! To complete your registration, please use the following One-Time Password (OTP):</p>
                            
                            <div style="background: #fff; border: 2px dashed #eab308; padding: 20px; text-align: center; margin: 20px 0;">
                                <p style="margin: 0 0 10px 0; color: #6b7280; font-size: 14px;">Your verification code:</p>
                                <p style="font-size: 36px; font-weight: bold; color: #eab308; letter-spacing: 8px; margin: 0;">{otp}</p>
                            </div>
                            
                            <p><strong>This OTP is valid for 10 minutes.</strong></p>
                            
                            <div style="background: #fef3c7; border-left: 4px solid #eab308; padding: 15px; margin: 20px 0;">
                                <p style="margin: 0; font-size: 14px;">
                                    <strong>⚠️ Security Tips:</strong>
                                    <ul style="margin: 5px 0 0 0; padding-left: 20px;">
                                        <li>Do not share this code with anyone</li>
                                        <li>AgroDoc-AI will never ask for your password</li>
                                        <li>If you didn't request this, please ignore this email</li>
                                    </ul>
                                </p>
                            </div>
                            
                            <p style="color: #6b7280; font-size: 14px; margin-top: 30px;">
                                Need help? Contact our support team at support@agrodoc-ai.com
                            </p>
                            
                            <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 30px 0;">
                            
                            <p style="color: #9ca3af; font-size: 12px; text-align: center;">
                                © 2024 AgroDoc-AI. All rights reserved.<br>
                                AI-powered crop disease detection for smarter farming.
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                ''',
                body=f'''
VillageCrop - Email Verification

Hello {username},

Thank you for registering with VillageCrop!

Your One-Time Password (OTP) for email verification is:

{otp}

This OTP is valid for 10 minutes.

Do not share this code with anyone. If you didn't request this, please ignore this email.

---
AgroDoc-AI Team
AI-Powered Plant Disease Detection
                '''
            )
            
            self.mail.send(msg)
            print(f"✓ OTP email sent to: {email}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to send OTP email to {email}: {str(e)}")
            return False


# Global OTP service instance
otp_service = OTPService()
