# # schedularapp/signals.py
# from django.db.models.signals import post_save
# from django.dispatch import receiver
# from django.contrib.auth import get_user_model
# from .models import UserProfile

# User = get_user_model()

# @receiver(post_save, sender=User)
# def create_profile(sender, instance, created, **kwargs):
#     if created:
#         UserProfile.objects.create(user=instance)

# schedularapp/signals.py
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_profile(sender, instance, created, **kwargs):
    # create profile when user is created; if superuser, default role Admin
    if created:
        role = "Admin" if getattr(instance, "is_superuser", False) else "User"
        UserProfile.objects.create(user=instance, role=role)
    else:
        # if user became superuser later, ensure profile role reflects it
        profile, _ = UserProfile.objects.get_or_create(user=instance)
        if instance.is_superuser and profile.role != "Admin":
            profile.role = "Admin"
            profile.save()

