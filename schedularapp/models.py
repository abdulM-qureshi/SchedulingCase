from django.conf import settings
from django.db import models

class UserProfile(models.Model):
    ROLE_CHOICES = (("Admin", "Admin"), ("User", "User"))
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default="User")
    def __str__(self): return f"{self.user.username} ({self.role})"
