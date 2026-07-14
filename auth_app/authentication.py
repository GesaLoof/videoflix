# authentication.py
from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        print("ALL COOKIES:", request.COOKIES)
        access_token = request.COOKIES.get(settings.AUTH_COOKIE_ACCESS)
        print("ACCESS TOKEN:", access_token)
        if not access_token:
            return None
        
        try:
            validated_token = self.get_validated_token(access_token)
            return self.get_user(validated_token), validated_token
        except InvalidToken:
            return None