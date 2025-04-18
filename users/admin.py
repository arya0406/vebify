from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserMoodHistory


class CustomUserAdmin(UserAdmin):
    """Admin configuration for CustomUser model."""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login', 'date_joined')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined', 'last_login')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    fieldsets = UserAdmin.fieldsets + (
        ('User Profile', {'fields': ('profile_picture', 'bio', 'dark_mode')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('User Profile', {'fields': ('profile_picture', 'bio', 'dark_mode')}),
    )


class UserMoodHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for UserMoodHistory model."""
    list_display = ('user', 'mood', 'timestamp')
    list_filter = ('mood', 'timestamp')
    search_fields = ('user__username', 'mood')
    ordering = ('-timestamp',)


admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserMoodHistory, UserMoodHistoryAdmin) 