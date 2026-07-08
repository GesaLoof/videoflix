from django.urls import path, include
from rest_framework_simplejwt.views import TokenRefreshView
from .views import RegisterView, ActivateAccountView, CookieTokenObtainPairView, LogoutView, CookieTokenRefreshView, PasswordResetRequestView, PasswordResetConfirmView

urlpatterns = [
    path("register/", RegisterView.as_view()),
    path("activate/<uidb64>/<token>/", ActivateAccountView.as_view()),
    path("login/", CookieTokenObtainPairView.as_view()),
    path("token/refresh/", CookieTokenRefreshView.as_view()),
    path("logout/", LogoutView.as_view(), name = "logout"),
    path("password_reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password_confirm/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_confirm"),
]