from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CustomUser


@receiver(post_save, sender=CustomUser)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal to handle actions when a new user is created.
    This can be extended to create default playlists or other user-related data.
    """
    if created:
        # Add any initialization code here
        pass 