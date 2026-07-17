from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_activation_email(user, uid, token):
    activation_link = f"{settings.FRONTEND_URL}/pages/auth/activate.html?uid={uid}&token={token}"
    
    context = {
        'activation_link': activation_link,
        'user': user,
    }
    
    html_content = render_to_string('emails/activation.html', context)
    text_content = f"Click to activate your account: {activation_link}"
    
    email = EmailMultiAlternatives(
        subject="Activate your account",
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()


def send_password_reset_email(user, uid, token):
    reset_link = f"{settings.FRONTEND_URL}/pages/auth/confirm_password.html?uid={uid}&token={token}"
    
    context = {
        'reset_link': reset_link,
        'user': user,
    }
    
    html_content = render_to_string('emails/password_reset.html', context)
    text_content = f"Click to reset your password: {reset_link}"
    
    email = EmailMultiAlternatives(
        subject="Reset your password",
        body=text_content,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    email.attach_alternative(html_content, "text/html")
    email.send()