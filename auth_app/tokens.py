from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.is_active}{timestamp}"


class PasswordResetTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{user.password}{timestamp}{user.is_active}"


account_activation_token = AccountActivationTokenGenerator()
password_reset_token = PasswordResetTokenGenerator()
