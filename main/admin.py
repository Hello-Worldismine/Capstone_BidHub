from django.contrib import admin
from .models import Profile, FavoriteProperty

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio_short')
    search_fields = ('user__username', 'user__email')
    
    def bio_short(self, obj):
        return obj.bio[:50] + "..." if len(obj.bio) > 50 else obj.bio
    bio_short.short_description = "자기소개"

@admin.register(FavoriteProperty)
class FavoritePropertyAdmin(admin.ModelAdmin):
    list_display = ('user', 'case_number', 'created_at')
    search_fields = ('user__username', 'case_number')
    list_filter = ('created_at',)
    ordering = ('-created_at',)

