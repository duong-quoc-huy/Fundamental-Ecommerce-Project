from django.contrib.auth.backends import BaseBackend
from .models import CustomUser

class EmailBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, email=None, **kwargs):
        # Handle both username and email parameters
        if email is None:
            email = username
        
        if email is None or password is None:
            return None
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            CustomUser().set_password(password)
            return None
        
        # Check password
        if user.check_password(password):
            return user
        
        return None
    
    def get_user(self, user_id):
        try:
            return CustomUser.objects.get(pk=user_id)
        except CustomUser.DoesNotExist:
            return None 