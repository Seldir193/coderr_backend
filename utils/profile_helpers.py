from coder_app.models import CustomerProfile, BusinessProfile
from rest_framework.exceptions import ValidationError
from django.contrib.auth.models import User
from django.utils.timezone import now

# serializers

# userProfileSerializers_logic.py
def get_user_type(obj):
    """
    Returns the type of the user: superuser, business, customer, or unknown.
    """
    #if obj.is_superuser:
        #return "superuser"
    if hasattr(obj, 'business_profile'):
        return "business"
    elif hasattr(obj, 'customer_profile'):
        return "customer"
    return "unknown"

def get_user_profile_image(obj):
    """
    Returns the URL of the profile image based on the user's profile type.
    """
    if hasattr(obj, 'business_profile') and getattr(obj.business_profile, 'file', None):
        try:
            return obj.business_profile.file.url  # Gibt die URL der Datei zurück
        except AttributeError:
            return None
    if hasattr(obj, 'customer_profile') and getattr(obj.customer_profile, 'file', None):
        try:
            return obj.customer_profile.file.url  # Gibt die URL der Datei zurück
        except AttributeError:
            return None
    return None
# End of userProfileSerializers_logic.py

# registrationSerializers_logic.py
def create_new_user(validated_data):
    """
    Creates a new user and sets their password.
    """
    user = User(
        username=validated_data['username'],
        email=validated_data['email']
    )
    user.set_password(validated_data['password'])
    user.save()
    return user

def create_user_profile(user, profile_type, validated_data):
    """
    Creates the appropriate profile for the user based on the profile type.
    """
    if profile_type == 'customer':
        CustomerProfile.objects.create(
            user=user,
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            created_at=now()
        )
    elif profile_type == 'business':
        BusinessProfile.objects.create(
            user=user,
            company_name="Default Company",  
            company_address="Default Address",  
            created_at=now()
        )
    else:
        raise ValidationError("Unknown profile type.")
# End of registrationSerializers_logic.py






