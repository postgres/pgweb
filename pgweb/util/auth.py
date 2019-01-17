from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend

# Special version of the authentication backend, so we can handle things like
# forced lowercasing of usernames.
class AuthBackend(ModelBackend):
    def authenticate(self, username=None, password=None):
        try:
            user = User.objects.get(username=username.lower())

            # If user is found, check the password using the django
            # methods alone.
            if user.check_password(password):
                return user

            # User found but password wrong --> tell django it is wrong
            return None
        except User.DoesNotExist:
            # User not found, so clearly they can't log in!
            return None

        return None # Should never get here, but just in case...
