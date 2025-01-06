from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg
from coder_app.models import  Review,Order
from rest_framework.exceptions import ValidationError
from coder_app.models import Review
from django.contrib.auth.models import User
from rest_framework.exceptions import NotFound
# view.py

# customerProfileView_logic.py
def get_customer_profile_or_error(user):
    """
    Checks if a user has a `customer_profile`.
    Returns the profile or an error response if not found.
    """
    if not hasattr(user, 'customer_profile'):
        return Response({"error": "Customer profile not found."}, status=status.HTTP_404_NOT_FOUND)
    return user.customer_profile
# End of customerProfilView_logic.py


# baseInfoView_logic.py
def calculate_average_rating(business_user=None):
    """
    Calculates the average rating. Optionally, can specify a business user.
    """
    queryset = Review.objects.all()
    if business_user:
        queryset = queryset.filter(business_user=business_user)
    return queryset.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.0
# End of baseInfoView_logic.py

# customerProfileView_logic.py
def get_user_or_error(user_id):
    """
    Fetches a user by ID or returns an error.
    """
    user = User.objects.filter(id=user_id).first()
    if not user:
        raise NotFound({'error': 'User not found.'})
    return user

#def count_completed_orders_for_user(user):
    #"""
    #Counts completed orders for a user based on their profile type.
    #"""
    #if hasattr(user, 'business_profile'):
       # return Order.objects.filter(business_user_id=user, status='completed').count()
   # elif hasattr(user, 'customer_profile'):
       # return Order.objects.filter(user=user, status='completed').count()
    #else:
        #raise ValidationError({'error': 'User does not have a valid profile (business or customer).'})
     #End of customerProfilView_logic.py
