from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    
    fieldsets = UserAdmin.fieldsets + (
        ('추가 정보', {
            'fields': ('gender', 'birth_date', 'bio', 'region', 'address', 'phone', 'mobile', 'terms_conditions')
        }),
    )
    
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('추가 정보', {
            'fields': ('email', 'gender', 'birth_date', 'region', 'phone', 'terms_conditions')
        }),
    )
