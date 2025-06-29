from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal handler to perform actions after a user is created or updated
    Currently just a placeholder for future functionality
    """
    if created:
        # Actions to perform when a new user is created
        # For example, create an associated profile, send welcome email, etc.
        pass
    else:
        # Actions to perform when a user is updated
        pass 