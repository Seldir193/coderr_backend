from rest_framework.response import Response
from rest_framework import status
from coder_app.serializers import OfferSerializer,OrderSerializer
from django.db.models import Avg
from coder_app.models import Offer, Review,Order,OfferDetail
from rest_framework.exceptions import ValidationError
from coder_app.serializers import UserProfileSerializer, BusinessProfileSerializer, CustomerProfileSerializer
from coder_app.models import Review
from django.contrib.auth.models import User
from rest_framework.exceptions import NotFound
from rest_framework.exceptions import PermissionDenied

# view.py
# reviewDetailList_logic.py
def get_review_or_404(pk):
    """
    Fetches a review by ID. Raises an exception if not found.
    """
    try:
        return Review.objects.get(pk=pk)
    except Review.DoesNotExist:
        raise NotFound({"error": "Review not found"})
    
def permission_error_response(message):
    """
    Returns an error response for unauthorized access to review.
    """
    return Response({"error": message}, status=status.HTTP_403_FORBIDDEN)
# End of reviewDetailList_logic.py

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

# profileView_logic.py
def get_profile_data(user):
    """Retrieve profile data based on the user type."""
    if hasattr(user, 'business_profile'):
        return 'business', BusinessProfileSerializer(user.business_profile).data
    elif hasattr(user, 'customer_profile'):
        return 'customer', CustomerProfileSerializer(user.customer_profile).data
    return 'unknown', {}

def build_profile_response(user, profile_type, profile_data, profile_image=None):
    """Construct a response structure for a user's profile."""
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "first_name": profile_data.get("first_name", user.first_name),
        "last_name": profile_data.get("last_name", user.last_name),
        "created_at": profile_data.get("created_at", user.date_joined),
        "file": profile_image,
        "type": profile_type,
        "profile_data": profile_data,
        "tel": profile_data.get("tel", None),
        "location": profile_data.get("location", None),
        "description": profile_data.get("description", None),
        "working_hours": profile_data.get("working_hours", None),
    }

def get_profile_serializer(user, request_data):
    """Returns the appropriate profile serializer for the user."""
    if hasattr(user, 'business_profile'):
        return BusinessProfileSerializer(user.business_profile, data=request_data, partial=True)
    elif hasattr(user, 'customer_profile'):
        return CustomerProfileSerializer(user.customer_profile, data=request_data, partial=True)
    return None

def save_user_profile_data(user, request_data):
    """Updates the user data and returns the serializer."""
    user_serializer = UserProfileSerializer(user, data=request_data, partial=True)
    if user_serializer.is_valid():
        user_serializer.save()
        return user_serializer
    else:
        # Fehlerdetails für Debugging oder API-Antwort bereitstellen
        raise ValidationError(user_serializer.errors)

def save_profile_serializer(profile_serializer):
    """Validates and saves the profile serializer, if provided."""
    if profile_serializer and profile_serializer.is_valid():
        profile_serializer.save()
        return True
    else:
        # Fehlerdetails bereitstellen
        raise ValidationError(profile_serializer.errors)

def update_profile_data(user, request_data):
    """Handle updating user profile data."""
    try:
        # User-Daten speichern
        user_serializer = save_user_profile_data(user, request_data)
        
        # Profilserializer abrufen und speichern
        profile_serializer = get_profile_serializer(user, request_data)
        if profile_serializer:
            save_profile_serializer(profile_serializer)

        # Erfolg: Benutzer-Daten zurückgeben
        profile_type, profile_data = get_profile_data(user)
        response_data = build_profile_response(user, profile_type, profile_data)
        return Response(response_data, status=status.HTTP_200_OK)

    except ValidationError as e:
        # Fehler zurückgeben
        return Response({"errors": e.detail}, status=status.HTTP_400_BAD_REQUEST)
# End of profileView_logic.py

# businessProfileView_logic.py
def get_business_profile_or_error(user):
    """
    Checks if a user has a business profile and returns it.
    Returns an error response if not found.
    """
    if hasattr(user, 'business_profile'):
        return user.business_profile
    return Response({"error": "Business profile not found."}, status=status.HTTP_404_NOT_FOUND)
# End of businessProfilView_logic.py

# offerListView_logic.py
def get_offers_for_user(user):
    """
    Returns offers created by the authenticated user.
    If the user is not a provider, returns all offers.
    """
    if hasattr(user, 'business_profile'):
        return Offer.objects.filter(user=user)
    return Offer.objects.all()
# End of offerListView_logic.py

# orderListView_logic.py
def get_orders_for_user(user):
    """
    Returns orders for the user.
    For providers: Orders related to their offers.
    For customers: Their own orders.
    """
    if hasattr(user, 'business_profile'):
        return Order.objects.filter(offer__user=user).select_related('user', 'offer', 'offer_detail_id')
    return Order.objects.filter(user=user).select_related('offer', 'offer_detail_id')

def user_can_create_order(user):
    """
    Checks if a user is allowed to create orders.
    Only non-business profiles are allowed to create orders.
    """
    return not hasattr(user, 'business_profile')

def prepare_order_data(request_data, user):
    """
    Prepares data for order creation.
    Assigns the authenticated user.
    """
    data = request_data.copy()
    data['user'] = user.id
    return data

def set_offer_detail_data(data):
    """
    Validates offer_detail_id and sets 'option'.
    Returns a response object in case of error, otherwise updated data.
    """
    if 'offer_detail_id' not in data:
        return Response({'error': 'The field "offer_detail_id" is missing in the request.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        offer_detail = OfferDetail.objects.get(id=data['offer_detail_id'])
        data['option'] = offer_detail.offer_type
        return data
    except OfferDetail.DoesNotExist:
        return Response({'error': 'OfferDetail not found.'}, status=status.HTTP_400_BAD_REQUEST)

def serialize_and_save_order(data):
    """
    Validates and saves the order using the serializer.
    Returns the order data if successful, otherwise errors.
    """
    serializer = OrderSerializer(data=data)
    if serializer.is_valid():
        order = serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def create_order(request_data, user):
    """
    Creates a new order if the user is not a business profile.
    Steps: Validate, prepare data, check offer_detail,
    serialize and save the order.
    """
    if not user_can_create_order(user):
        return Response(
            {'error': 'Business profile owners cannot create orders.'},
            status=status.HTTP_403_FORBIDDEN
        )

    data = prepare_order_data(request_data, user)
    data_or_error = set_offer_detail_data(data)
    if isinstance(data_or_error, Response):
        return data_or_error
    return serialize_and_save_order(data_or_error)
# End of orderListView_logic.py

# offerDetailView_logic.py
def get_offer_or_none(offer_id):
    """
    Attempts to fetch an offer by ID.
    Returns None if it does not exist.
    """
    try:
        return Offer.objects.get(id=offer_id)
    except Offer.DoesNotExist:
        return None

def get_offer_and_delete(offer_id, user):
    """
    Finds an offer by ID and deletes it if the user is the creator.
    """
    try:
        offer = Offer.objects.get(id=offer_id, user=user)  # Only the creator can delete
        offer.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Offer.DoesNotExist:
        return Response({"error": "Offer not found or you are not authorized"}, status=status.HTTP_404_NOT_FOUND)

def update_offer(offer_id, user, request):
    """
    Updates an offer if the user is its creator.
    """
    try:
        offer = Offer.objects.get(id=offer_id, user=user)  # Only the creator can update
        serializer = OfferSerializer(offer, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Offer.DoesNotExist:
        return Response({"error": "Offer not found or you are not authorized"}, status=status.HTTP_404_NOT_FOUND)
# End of offerDetailView_logic.py

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

# orderInProgressCountView.py 
def get_in_progress_count(user, offer):
    """
    Counts the number of in-progress orders for an offer based on user type.
    """
    if hasattr(user, 'customer_profile'):
        return Order.objects.filter(user=user, offer=offer, status='in_progress').count()
    elif hasattr(user, 'business_profile'):
        if offer.user != user:
            raise PermissionDenied("You are not authorized to view data for this offer.")
        return Order.objects.filter(offer=offer, status='in_progress').count()
    else:
        raise PermissionDenied("Unauthorized user.")
# End of orderInProgressCountView_logic.py

# orderCompletedCountView_logic.py
def get_user_or_error(user_id):
    """
    Fetches a user by ID or returns an error.
    """
    user = User.objects.filter(id=user_id).first()
    if not user:
        raise NotFound({'error': 'User not found.'})
    return user

def count_completed_orders_for_user(user):
    """
    Counts completed orders for a user based on their profile type.
    """
    if hasattr(user, 'business_profile'):
        return Order.objects.filter(business_user_id=user, status='completed').count()
    elif hasattr(user, 'customer_profile'):
        return Order.objects.filter(user=user, status='completed').count()
    else:
        raise ValidationError({'error': 'User does not have a valid profile (business or customer).'})
       
# End of orderCompletedCountView_logic.py

# orderDetailView_logic.py
def get_order_or_403(order_id, user):
    try:
        order = Order.objects.get(id=order_id)
        #if order.offer.user != user:  # Der Benutzer ist nicht der Ersteller
        if order.offer.user != user and order.user != user:
            raise PermissionDenied("You are not authorized to edit this order.")
        return order
    except Order.DoesNotExist:
        raise NotFound("Order not found")

# End of orderDetailView_logic.py






