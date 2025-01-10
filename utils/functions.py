from rest_framework.response import Response
from rest_framework import status
from django.db.models import Avg
from coder_app.models import  Review
from coder_app.models import Review
from django.contrib.auth.models import User
from rest_framework.exceptions import NotFound
from coder_app.models import Offer, OfferDetail, Review ,BusinessProfile,Order
from coder_app.serializers import ReviewSerializer
from django.shortcuts import get_object_or_404
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import  PermissionDenied

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

# customerProfileView_logic.py
def get_user_or_error(user_id):
    """
    Fetches a user by ID or returns an error.
    """
    user = User.objects.filter(id=user_id).first()
    if not user:
        raise NotFound({'error': 'User not found.'})
    return user
#End of customerProfileView_logic.py

# offerDetalView_logic.py
def get_offer_or_404(offer_id, user=None):
    """
    Retrieves an offer by ID and optionally filters by user.
    """
    try:
        if user:
            return Offer.objects.get(id=offer_id, user=user)
        return Offer.objects.get(id=offer_id)
    except Offer.DoesNotExist:
        return None

def create_or_update_details(offer, details_data):
    """
    Creates or updates offer details.
    """
    existing_details = {detail.id: detail for detail in offer.details.all()}
    updated_ids = set()

    for detail_data in details_data:
        detail_id = detail_data.get('id')
        if detail_id and detail_id in existing_details:
            update_offer_details(existing_details[detail_id], detail_data)
            updated_ids.add(detail_id)
        else:
            OfferDetail.objects.create(
                offer=offer,
                variant_title=detail_data['title'],
                variant_price=detail_data['price'],
                revision_limit=detail_data['revisions'],
                delivery_time_in_days=detail_data['delivery_time_in_days'],
                features=detail_data['features'],
                offer_type=detail_data['offer_type'],
            )

    for detail_id in existing_details.keys():
        if detail_id not in updated_ids:
            existing_details[detail_id].delete()

def update_offer_details(detail_instance, detail_data):
    """
    Updates an existing offer detail.
    """
    detail_instance.variant_title = detail_data.get('title', detail_instance.variant_title)
    detail_instance.variant_price = detail_data.get('price', detail_instance.variant_price)
    detail_instance.revision_limit = detail_data.get('revisions', detail_instance.revision_limit)
    detail_instance.delivery_time_in_days = detail_data.get('delivery_time_in_days', detail_instance.delivery_time_in_days)
    detail_instance.features = detail_data.get('features', detail_instance.features)
    detail_instance.offer_type = detail_data.get('offer_type', detail_instance.offer_type)
    detail_instance.save()
# End of offerDetailView_logic.py

# profilListView_logic.py
# businessProfilView_logic.py
def get_user_and_profile(pk):
    """
    Retrieve the user and associated profile by primary key.
    """
    try:
        user = User.objects.get(pk=pk)
        if hasattr(user, 'business_profile'):
            return user, user.business_profile, 'business'
        elif hasattr(user, 'customer_profile'):
            return user, user.customer_profile, 'customer'
    except User.DoesNotExist:
        return None, None, None
    return user, None, None

def update_user_data( user, data):
        """
        Update user-specific fields.
        """
        user_data = {
            key: value for key, value in data.items() if key in ["first_name", "last_name", "email"]
        }
        for field, value in user_data.items():
            setattr(user, field, value)
        user.save()

def update_profile_data( profile, data):
        """
        Update profile-specific fields.
        """
        profile_data = {
            key: value for key, value in data.items() if key in ["location", "tel", "description", "working_hours", "file"]
        }
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()
        
def handle_permission_denied( exception):
        """
        Handle PermissionDenied exception.
        """
        return Response({"error": str(exception)}, status=status.HTTP_403_FORBIDDEN)

def handle_parse_error():
        """
        Handle ParseError exception.
        """
        return Response(
            {"error": "Ungültige oder fehlende Felder."},
            status=status.HTTP_400_BAD_REQUEST,
        )

def handle_generic_error():
        """
        Handle any unexpected errors.
        """
        return Response(
            {"error": "Ein unerwarteter Fehler ist aufgetreten."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

def check_permissions( request, user):
        """
        Check if the request user has permission to update the profile.
        """
        if request.user != user and not request.user.is_staff:
            raise PermissionDenied("Sie haben keine Berechtigung, dieses Profil zu ändern.")

def check_user_and_profile( user, profile):
        """
        Check if the user and profile exist. Returns a Response if either is missing.
        """
        if not user:
            return Response({"error": "Benutzer nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        if not profile:
            return Response({"error": "Profil nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        return None

def format_profile_response(user, profile, profile_type):
    """
    Format the profile data for response.
    """
    file_url = profile.file.url if getattr(profile, 'file', None) else None
    return {
        "user": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "file": file_url,
        "location": getattr(profile, 'location', None),
        "tel": getattr(profile, 'tel', None),
        "description": getattr(profile, 'description', None),
        "working_hours": getattr(profile, 'working_hours', None),
        "type": profile_type,
        "email": user.email,
        "created_at": user.date_joined.strftime('%Y-%m-%dT%H:%M:%SZ'),
    }
# End of profilListView_logic.py

# reviewListCreateView_logic.py
def get_filtered_reviews(user, query_params):
    """
    Filters reviews based on query parameters.
    """
    business_user_id = query_params.get('business_user_id')
    ordering = query_params.get('ordering', 'updated_at')

    if hasattr(user, 'customer_profile') and not business_user_id:
        return Review.objects.filter(reviewer=user).order_by(ordering)
    
    reviews = Review.objects.all()
    if business_user_id:
        reviews = reviews.filter(business_user_id=business_user_id)
    return reviews.order_by(ordering)

def is_customer(user):
    """
    Checks if the user has a customer profile.
    """
    return hasattr(user, 'customer_profile')

def get_business_user(data):
    """
    Retrieves the business user based on the request data.
    """
    business_user_id = data.get('business_user')
    return get_object_or_404(User, id=business_user_id)

def is_business_user(user):
    """
    Checks if the user has a business profile.
    """
    return hasattr(user, 'business_profile')

def has_existing_review(reviewer, business_user):
    """
    Checks if a review already exists for the given reviewer and business user.
    """
    return Review.objects.filter(reviewer=reviewer, business_user=business_user).exists()

def create_review(data, reviewer, business_user, context):
    """
    Creates and saves a new review.
    """
    serializer = ReviewSerializer(data=data, context=context)
    if serializer.is_valid():
        serializer.save(reviewer=reviewer, business_user=business_user)
        return serializer.data, status.HTTP_201_CREATED
    return serializer.errors, status.HTTP_400_BAD_REQUEST
# End of reviewListCreateView_logic.py


# baseInfoView_logic.py
def calculate_average_rating(business_user=None):
    """
    Calculates the average rating. Optionally, can specify a business user.
    """
    queryset = Review.objects.all()
    if business_user:
        queryset = queryset.filter(business_user=business_user)
    return queryset.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0.0

def collect_statistics():
    """
    Collects and calculates the app's basic statistics.
    """
    offer_count = Offer.objects.count()
    review_count = Review.objects.count()
    business_profile_count = BusinessProfile.objects.count()
    average_rating = calculate_average_rating()

    return {
        "review_count": review_count,
        "average_rating": round(average_rating, 1),
        "business_profile_count": business_profile_count,
        "offer_count": offer_count,
    }

def handle_exception(exception):
    """
    Handles unexpected exceptions and returns a 500 response.
    """
    return Response({"error": str(exception)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# End of baseInfoView_logic.py


# orderListView_logic.py
def get_orders_for_user(user):
    """
    Returns orders for the authenticated user.
    """
    if hasattr(user, 'business_profile'):
        return Order.objects.filter(business_user=user)
    return Order.objects.filter(customer_user=user)


def get_offer_detail(offer_detail_id):
    """
    Retrieves the offer detail by ID or raises a 404 error.
    """
    return get_object_or_404(OfferDetail, id=offer_detail_id)

def create_order(customer_user, offer_detail):
    """
    Creates a new order based on the offer detail and customer user.
    """
    return Order.objects.create(
        customer_user=customer_user,
        business_user=offer_detail.offer.user,
        offer=offer_detail.offer,
        offer_detail=offer_detail,
        title=offer_detail.variant_title,
        revisions=offer_detail.revision_limit,
        delivery_time_in_days=offer_detail.delivery_time_in_days,
        price=offer_detail.variant_price,
        features=offer_detail.features,
        offer_type=offer_detail.offer_type,
        status='in_progress',
    )
# End of orderListView_logic.de

# orderDetailView_logic.py
def update_order_status(order, new_status):
    """
    Updates the status of an order if the new status is valid.
    """
    valid_statuses = ['pending', 'in_progress', 'completed', 'cancelled']
    if new_status not in valid_statuses:
        raise ValueError("Invalid status value.")
    order.status = new_status
    order.save()
# End of orderDetailView_logic.py

# orderCountView_logic.de
# completedOrderCountView_logic.de
def fetch_business_user_by_id(business_user_id):
    """
    Fetches a business user by their ID, returning None if not found.
    """
    try:
        return User.objects.get(id=business_user_id)
    except User.DoesNotExist:
        return None

def get_order_count(business_user, status):
    """
    Retrieves the order count for a specific business user and status.
    """
    return Order.objects.filter(business_user=business_user, status=status).count()

# End of orderCountView_logic.de
# End of completedOrderCountView_logic.py

# businessProfileListView_logic.py
# customerProfileListView_logic.py
def format_common_profile_data(profile, request):
    """
    Formats the common data for any profile type.
    """
    user = profile.user
    file_url = request.build_absolute_uri(profile.file.url) if profile.file else None
    return {
        "user": {
            "pk": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        },
        "file": file_url,
    }
# End of businessProfileListView_logic.py
# End of customerProfileListView_logic.py

# ooferListView_logic.py
def apply_ordering(queryset, ordering):
    """
    Applies the specified ordering to the queryset.
    
    Args:
        queryset (QuerySet): The queryset to order.
        ordering (str): The ordering parameter, e.g., "updated_at" or "min_price".
    
    Returns:
        QuerySet: The ordered queryset.
    """
    if ordering == "updated_at":
        return queryset.order_by("-updated_at")
    elif ordering == "-updated_at":
        return queryset.order_by("updated_at")
    elif ordering in ["min_price", "-min_price"]:
        return queryset.order_by(ordering)
    return queryset.order_by("-updated_at")


def get_paginated_response(queryset, request, serializer_class, paginator_class):
    """
    Paginates the queryset and returns a serialized response.
    
    Args:
        queryset (QuerySet): The queryset to paginate.
        request (HttpRequest): The request object.
        serializer_class (Serializer): The serializer class to use.
        paginator_class (Paginator): The paginator class to use.
    
    Returns:
        Response: The paginated and serialized response.
    """
    paginator = paginator_class()
    paginated_queryset = paginator.paginate_queryset(queryset, request)
    serializer = serializer_class(
        paginated_queryset, many=True, context={"request": request}
    )
    return paginator.get_paginated_response(serializer.data)


def validate_details(details):
    """
    Validates the details provided in the request data.
    
    Args:
        details (list): A list of detail dictionaries to validate.
    
    Returns:
        bool: True if the details are valid, otherwise False.
    """
    return len(details) == 3 and all(
        d["offer_type"] in ["basic", "standard", "premium"] for d in details
    )


def create_offer_response(offer, serializer_class):
    """
    Creates a response dictionary for a newly created offer.
    
    Args:
        offer (Offer): The offer object.
        serializer_class (Serializer): The serializer class to serialize the offer details.
    
    Returns:
        dict: The response data for the offer.
    """
    response_data = {
        "id": offer.id,
        "title": offer.title,
        "image": offer.image.url if offer.image else None,
        "description": offer.description,
        "details": serializer_class(offer.details.all(), many=True).data,
    }
    return response_data
# End of offerListView_logic.py


def check_user_and_profile(user, profile):
    """
    Checks if the user and profile exist. Returns a Response if either is missing.
    """
    if not user:
        return Response({"error": "Benutzer nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
    if not profile:
        return Response({"error": "Profil nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
    return None


class CustomPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "count": self.page.paginator.count,
                "total_pages": self.page.paginator.num_pages,
                "current_page": self.page.number,
                "results": data,
            }
        )