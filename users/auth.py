from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Authentication backend that supports login with either username or email
    """
    def authenticate(self, request, username=None, email=None, password=None, **kwargs):
        if email is not None:
            # Try to authenticate with email
            try:
                user = User.objects.get(email=email)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                return None
        
        if username is not None:
            # Try to authenticate with username
            try:
                user = User.objects.get(username=username)
                if user.check_password(password):
                    return user
            except User.DoesNotExist:
                return None
                
        return None 