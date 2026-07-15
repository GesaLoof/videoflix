from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode

from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from auth_app.tokens import account_activation_token, password_reset_token
from .serializers import (
    RegisterSerializer,
    EmailTokenObtainPairSerializer,
    PasswordResetConfirmSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new user and send an activation email."""

    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        """Create the user and trigger account activation."""
        user = serializer.save()
        self.send_activation_email(user)

    def send_activation_email(self, user):
        """Send an account activation email."""
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        activation_link = f"{settings.FRONTEND_URL}/activate/{uid}/{token}/"
        send_mail(
            subject="Activate your account",
            message=f"Click to activate your account: {activation_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )


class ActivateAccountView(APIView):
    """Activate a user account from an email link."""

    # Uses GET because it matches the assignment specification.
    # Change to POST if the API contract changes (safer)
    def get(self, request, uidb64, token):
        """Validate the activation token and activate the account."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save(update_fields=["is_active"])
            return Response({"detail": "Account successfully activated."})

        return Response(
            {"detail": "Invalid or expired link."}, status=status.HTTP_400_BAD_REQUEST
        )


class EmailTokenObtainPairView(TokenObtainPairView):
    """Return JWT access and refresh tokens."""

    serializer_class = EmailTokenObtainPairSerializer


class CookieTokenObtainPairView(TokenObtainPairView):
    """Authenticate a user and store JWTs in HTTP-only cookies."""

    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """Log in the user and set authentication cookies."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        access = serializer.validated_data["access"]
        refresh = serializer.validated_data["refresh"]

        response = Response(
            {
                "detail": "Login successful",
                "user": {
                    "id": user.id,
                    "username": user.email,
                },
            }
        )
        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        response.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        return response


class CookieTokenRefreshView(TokenRefreshView):
    """Refresh the access token using the refresh token cookie."""

    def post(self, request, *args, **kwargs):
        """Issue a new access token."""
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response(
                {"error": "Refresh token not found in cookies"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = {"refresh": refresh_token}
        serializer = self.get_serializer(data=data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)

        access_token = serializer.validated_data.get("access")
        response = Response({"message": "Token refreshed successfully"})
        response.set_cookie(
            key="access_token",
            value=str(access_token),
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        return response


class LogoutView(APIView):
    """Blacklist the refresh token and clear authentication cookies."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Log out the current user."""
        refresh_token = request.COOKIES.get("refresh_token")
        if refresh_token:
            try:
                RefreshToken(refresh_token).blacklist()
            except TokenError:
                pass
        else:
            return Response(
                {"error": "Refresh token not found in cookies"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        response = Response(
            {
                "detail": "Logout successful! All tokens will be deleted. Refresh token is now invalid."
            }
        )
        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")
        return response


class PasswordResetRequestView(APIView):
    """Send a password reset email if the user exists."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Generate and email a password reset link."""
        email = request.data.get("email")
        if not email:
            return Response(
                {"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # vague response to prevent user enumeration
            return Response(
                {"detail": "If that email exists, a reset link has been sent."}
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = password_reset_token.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/password_confirm/{uid}/{token}/"

        send_mail(
            subject="Reset your password",
            message=f"Click the link to reset your password: {reset_link}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
        )

        return Response({"detail": "If that email exists, a reset link has been sent."})


class PasswordResetConfirmView(APIView):
    """Reset a user's password using a valid reset token."""
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        """Validate the reset token and update the password."""
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, User.DoesNotExist):
            return Response(
                {"error": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST
            )

        if not password_reset_token.check_token(user, token):
            return Response(
                {"error": "Reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            user.set_password(serializer.validated_data["new_password"])
            user.save()
            return Response({"detail": "Password has been reset successfully."})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
