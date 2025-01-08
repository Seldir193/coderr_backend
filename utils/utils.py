from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError


def create_token_for_user(user):
    """Creates or retrieves a token for the user."""
    token, created = Token.objects.get_or_create(user=user)
    return token.key

def authenticate_user(username, password):
    """Authenticates a user with username and password."""
    user = authenticate(username=username, password=password)
    if not user:
        raise ValidationError("Invalid credentials")
    return user
