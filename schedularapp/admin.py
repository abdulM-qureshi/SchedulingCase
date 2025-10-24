from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.admin.sites import NotRegistered
from .models import UserProfile

User = get_user_model()


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = "Profile"
    fk_name = "user"


# Extend the built-in UserAdmin to show the profile inline and add role column
class CustomUserAdmin(DjangoUserAdmin):
    inlines = (UserProfileInline,)
    list_display = ("username", "email", "first_name", "last_name", "get_role", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")

    def get_role(self, obj):
        try:
            return obj.profile.role
        except Exception:
            return "-"
    get_role.short_description = "Role"


# Unregister if registered, safely
try:
    admin.site.unregister(User)
except NotRegistered:
    pass

# Register the custom admin
admin.site.register(User, CustomUserAdmin)

# Also register UserProfile separately (optional but useful)
try:
    admin.site.register(UserProfile)
except Exception:
    # if already registered, ignore
    pass
