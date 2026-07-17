from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings

def send_activation_email(user, uid, token):
    """
    Build an activation link with uid and token as query parameters, render
    the HTML email template and send it as a multipart email with a plain
    text fallback for clients that do not support HTML.
    """
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
    """
    Build a password reset link with uid and token as query parameters, render
    the HTML email template and send it as a multipart email with a plain
    text fallback for clients that do not support HTML.
    """
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