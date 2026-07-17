from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt import serializers as jwt_serializers
from rest_framework_simplejwt.exceptions import AuthenticationFailed

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """Validates registration input and creates an inactive user account."""
    password = serializers.CharField(write_only=True, min_length=8)
    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["email", "password", "confirmed_password"]

    def validate(self, attrs):
        """Check that password and confirmed_password match."""
        if attrs["password"] != attrs["confirmed_password"]:
            raise serializers.ValidationError(
                {"confirmed_password": "Passwords do not match."}
            )
        return attrs

    def create(self, validated_data):
        """
        Remove confirmed_password before saving, create the user and set
        is_active to False so the account requires email activation before login.
        """
        validated_data.pop("confirmed_password")
        user = User.objects.create_user(**validated_data)
        user.is_active = False
        user.save()
        return user


class EmailTokenObtainPairSerializer(jwt_serializers.TokenObtainPairSerializer):
    """
    Extends TokenObtainPairSerializer to authenticate via email instead of username.
    Overrides validate() to intercept AuthenticationFailed errors and provide
    a more specific message when the account exists but has not been activated yet,
    rather than the generic invalid credentials response.
    """
    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        """Authenticate the user and return tokens, throw an error for inactive accounts."""
        try:
            return super().validate(attrs)
        except AuthenticationFailed:
            user = User.objects.filter(email=attrs.get("email")).first()
            if user and not user.is_active:
                raise AuthenticationFailed(
                    "Account is not activated. Check your email."
                )
            raise


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Validates that new_password and confirm_password are present and matching."""
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        """Check that new_password and confirm_password match."""
        if attrs["new_password"] != attrs["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return attrs
