from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.exceptions import ValidationError


# viesw.py
# registrationsView_logic.py
def create_token_for_user(user):
    """Creates or retrieves a token for the user."""
    token, created = Token.objects.get_or_create(user=user)
    return token.key


# End of registrationsView_logic.py


# loginView_logic.py
def authenticate_user(username, password):
    """Authenticates a user with username and password."""
    user = authenticate(username=username, password=password)
    if not user:
        raise ValidationError("Invalid credentials")
    return user


# End of loginView_logic.py


# model.py
#  order_logic.py
def set_order_defaults(order):
    """
    Set default values for an order instance if not already provided.
    """
    if not order.business_user and order.offer:
        order.business_user = order.offer.user

    if order.offer_detail and not order.features:
        order.features = order.offer_detail.features or []

    if not order.title:
        order.title = order.offer.title

    if not order.price:
        order.price = order.offer_detail.variant_price

    if not order.delivery_time_in_days:
        order.delivery_time_in_days = order.offer_detail.delivery_time_in_days


# End of order_logic.py
