import secrets
import logging
from django.core.mail import send_mail
from .models import EmailOTP
from django.conf import settings
import random
logger = logging.getLogger(__name__)




def generate_otp(user):
	otp_code = secrets.randbelow(900000) + 100000
	EmailOTP.objects.create(user=user, code=otp_code)
	return otp_code

def send_otp_via_email(user, purpose='verification'):
	otp = str(random.randint(100000, 999999))
	
	EmailOTP.objects.create(
		user=user,
		code=otp,
		purpose=purpose
	)
	
	if purpose == 'password_reset':
		subject = 'Password Reset OTP'
		message = f'''
Hello {user.first_name or 'there'},

You requested to reset your password. Your OTP code is:

{otp}

This code will expire in 10 minutes.

If you didn't request this, please ignore this email.

Best regards,
Firefly E-commerce 
		'''
	else:
		subject = 'Email Verification OTP'
		message = f'''
Hello {user.first_name or 'there'},

Your verification code is:

{otp}

This code will expire in 10 minutes.

Best regards,
Firefly E-commerce
		'''
	
	send_mail(
		subject,
		message,
		settings.DEFAULT_FROM_EMAIL,
		[user.email],
		fail_silently=False,
	)


