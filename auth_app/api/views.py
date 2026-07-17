from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
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
from auth_app.emails import send_activation_email, send_password_reset_email

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """
    Extends CreateAPIView to add activation email sending after user creation.
    The default perform_create() only calls serializer.save(), this override
    adds uid/token generation and triggers the activation email.
    """
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        """Save the user, then generate uid and token and send the activation email."""
        user = serializer.save()
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = account_activation_token.make_token(user)
        send_activation_email(user, uid, token)


class ActivateAccountView(APIView):
    """
    Validates the activation token and sets is_active=True.
    The token becomes invalid after activation because is_active is hashed
    into the token, flipping it to True invalidates any further use.
    Uses GET since the link is clicked directly from an email client.
    """
    def get(self, request, uidb64, token):
        """Decode the uid, validate the token, and activate the account."""
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



class CookieTokenObtainPairView(TokenObtainPairView):
    """
    Extends TokenObtainPairView to store JWTs in httpOnly cookies instead of
    the response body, preventing JavaScript from accessing them directly (XSS protection).
    Also authenticates via email using EmailTokenObtainPairSerializer.
    """
    serializer_class = EmailTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        """Authenticate the user and set access_token and refresh_token as httpOnly cookies."""
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
    """
    Extends TokenRefreshView to read the refresh token from a cookie instead
    of the request body, since httpOnly cookies cannot be read by JavaScript.
    Issues a new access_token cookie on success.
    """

    def post(self, request, *args, **kwargs):
        """
        Read the refresh token cookie, validate it, and set a new access_token cookie. 
        Get new refresh token if previeus refresh token is rotated.
        """
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
        new_refresh_token = serializer.validated_data.get("refresh")  #get new refresh token

        response = Response({"message": "Token refreshed successfully"})
        response.set_cookie(
            key="access_token",
            value=str(access_token),
            httponly=True,
            secure=True,
            samesite="Lax",
        )
        if new_refresh_token:  #set new refresh token cookie
            response.set_cookie(
                key="refresh_token",
                value=str(new_refresh_token),
                httponly=True,
                secure=True,
                samesite="Lax",
            )
        return response


class LogoutView(APIView):
    """
    Blacklists the refresh token and clears auth cookies.
    Uses AllowAny so users can log out even after the access token has expired —
    requiring IsAuthenticated would block logout in that case.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Log out the current user. Blacklist the refresh token and delete both auth cookies."""
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
    """
    Generates a password reset token and emails a reset link.
    Returns the same response whether the email exists or not
    to prevent user enumeration.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        """Look up user by email and send a password reset link if found."""
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
        send_password_reset_email(user, uid, token)

        return Response({"detail": "If that email exists, a reset link has been sent."})



class PasswordResetConfirmView(APIView):
    """
    Validates the reset token and updates the password.
    The token automatically invalidates after use because the user's
    password hash is included in the token, changing it voids the token.
    """
    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        """Decode the uid, validate the token, and set the new password."""
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
