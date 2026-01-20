# email_utils.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_welcome_email(user_email, user_name):
    """Send a beautiful HTML welcome email"""
    
    # Context data for the template
    context = {
        'user_name': user_name,
        'website_url': 'https://firefly-ecommerce.duckdns.org/',
        'unsubscribe_url': 'http://yourwebsite.com/unsubscribe',
        'preferences_url': 'http://yourwebsite.com/preferences',
    }
    
    # Render HTML template
    html_content = render_to_string('emails/welcome_email.html', context)
    
    # Plain text fallback (for email clients that don't support HTML)
    text_content = f"""
    Hi {user_name},
    
    Thank you for subscribing to our newsletter! We're thrilled to have you as part of our community.
    
    Get ready to receive exciting updates, exclusive offers, and valuable content delivered straight to your inbox.
    
    Visit our website: https://yourwebsite.com
    
    Best regards,
    The Team
    """
    
    # Create email
    email = EmailMultiAlternatives(
        subject='Welcome to Our Newsletter! 🎉',
        body=text_content,  # Plain text version
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user_email],
    )
    
    # Attach HTML version
    email.attach_alternative(html_content, "text/html")
    
    # Send email
    email.send(fail_silently=False)