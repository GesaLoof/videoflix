from django.contrib import admin
from django.contrib.auth import get_user_model

User = get_user_model()

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'is_staff', 'date_joined']
    list_filter = ['is_active', 'is_staff']
    search_fields = ['email']
    readonly_fields = ['date_joined', 'last_login']