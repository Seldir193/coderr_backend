from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError
from coder_app.serializers import OrderSerializer

#def serialize_orders(orders):
   # """
    #Serializes a list of orders.
   # """
    #serializer = OrderSerializer(orders, many=True)
    #return serializer.data

#def error_response(message, status_code=status.HTTP_400_BAD_REQUEST):
    #"""Utility function for standardized error responses."""
    #return Response({'error': message}, status=status_code)

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
