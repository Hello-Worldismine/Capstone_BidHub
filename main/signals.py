# main/signals.py
from django.conf import settings # Import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
# from django.contrib.auth.models import User # Remove direct import
from .models import Profile

# Connect to the custom user model specified in settings
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
