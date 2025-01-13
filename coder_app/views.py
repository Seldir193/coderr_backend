from django.db.models import Min
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.exceptions import ParseError, PermissionDenied, ValidationError
from rest_framework.generics import RetrieveAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import (
    AllowAny,
    BasePermission,
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.views import APIView

from coder_app.filters import OfferFilter
from coder_app.models import (
    BusinessProfile,
    CustomerProfile,
    Offer,
    OfferDetail,
    Order,
    Review,
)
from coder_app.serializers import (
    CustomerProfileSerializer,
    LoginSerializer,
    OfferDetailFullSerializer,
    OfferSerializer,
)
from coder_app.serializers import Order as OrderSerializer
from coder_app.serializers import (
    OrderSerializer,
    RegistrationSerializer,
    ReviewSerializer,
)
from utils.functions import (
    check_user_and_profile,
    collect_statistics,
    create_or_update_details,
    create_order,
    create_review,
    fetch_business_user_by_id,
    format_common_profile_data,
    format_profile_response,
    get_business_user,
    get_customer_profile_or_error,
    get_filtered_reviews,
    get_offer_detail,
    get_offer_or_404,
    get_order_count,
    get_orders_for_user,
    get_user_and_profile,
    get_user_or_error,
    handle_exception,
    has_existing_review,
    is_business_user,
    is_customer,
    update_order_status,
    apply_ordering,
    validate_details,
    create_offer_response,
    get_paginated_response,
    check_user_and_profile,
    check_permissions,
    handle_generic_error,
    handle_parse_error,
    handle_permission_denied,
    update_profile_data,
    update_user_data,
    CustomPagination,
)
from utils.utils import authenticate_user, create_token_for_user


class IsOwnerOrAdmin(BasePermission):
    """
    Allows access to admins or the object's owner.
    """

    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user


class IsBusinessProfile(BasePermission):
    """
    Permission, die überprüft, ob der Benutzer ein Anbieter (Business Profile) ist.
    """

    def has_permission(self, request, view):
        return hasattr(request.user, "business_profile")


class OfferListView(APIView):
    """
    Handles operations related to listing and creating offers.
    """

    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OfferFilter
    pagination_class = CustomPagination

    def get_queryset(self):
        """
        Returns the base QuerySet with annotations for minimum price and delivery time.

        Returns:
            QuerySet: Annotated queryset for offers.
        """
        return Offer.objects.annotate(
            min_price=Min("details__variant_price"),
            min_delivery_time=Min("details__delivery_time_in_days"),
        )

    def get(self, request, *args, **kwargs):
        """
        Handles GET requests to retrieve and filter offers.

        Args:
            request (HttpRequest): The incoming request.

        Returns:
            Response: Paginated and serialized offers.
        """
        queryset = self.get_queryset()
        filterset = OfferFilter(request.query_params, queryset=queryset)

        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = apply_ordering(
            filterset.qs, request.query_params.get("ordering", "-updated_at")
        )
        return get_paginated_response(
            queryset, request, OfferSerializer, CustomPagination
        )

    def post(self, request, *args, **kwargs):
        """
        Handles POST requests to create a new offer.

        Args:
            request (HttpRequest): The incoming request.

        Returns:
            Response: The created offer data or detail message.
        """
        if not hasattr(request.user, "business_profile"):
            return Response(
                {"detail": "Only business users can create offers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if not validate_details(request.data.get("details", [])):
            return Response(
                {
                    "detail": "You must provide exactly three details with offer_type: basic, standard, and premium."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OfferSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            offer = serializer.save()
            response_data = create_offer_response(offer, OfferDetailFullSerializer)
            return Response(response_data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class OfferDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get(self, request, id, format=None):
        """
        Retrieves the details of a specific offer.
        """
        offer = get_offer_or_404(id)
        if not offer:
            return Response(
                {"detail": "Offer not found."}, status=status.HTTP_404_NOT_FOUND
            )

        serializer = OfferSerializer(offer, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id, format=None):
        """
        Updates an offer's data, including details.
        """
        offer = get_offer_or_404(id, user=request.user)
        if not offer:
            return Response(
                {"detail": "Offer not found or you do not own this offer."},
                status=status.HTTP_404_NOT_FOUND,
            )

        details_data = request.data.pop("details", None)
        serializer = OfferSerializer(
            offer, data=request.data, partial=True, context={"request": request}
        )

        if serializer.is_valid():
            offer = serializer.save()
            if details_data:
                create_or_update_details(offer, details_data)

            response_data = {
                "id": offer.id,
                "title": offer.title,
                "details": OfferDetailFullSerializer(
                    offer.details.all(), many=True
                ).data,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        """
        Deletes a specific offer.
        """
        offer = get_offer_or_404(id, user=request.user)
        if not offer:
            return Response(
                {
                    "detail": "Offer not found or you do not have permission to delete this offer."
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        offer.delete()
        return Response({}, status=status.HTTP_200_OK)


class OfferDetailRetrieveView(RetrieveAPIView):
    """
    Gibt die vollständigen Details eines spezifischen Angebotsdetails zurück.
    """

    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = "id"


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token_key = create_token_for_user(user)
            return Response(
                {
                    "token": token_key,
                    "user_id": user.id,
                    "username": user.username,
                    "email": user.email,
                },
                status=status.HTTP_201_CREATED,
            )
        errors = serializer.errors
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return self.handle_invalid_serializer(serializer)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        try:
            user = authenticate_user(username, password)
            if not user:
                return Response(
                    {"detail": "Falsche Anmeldeinformationen."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except ValidationError:
            return Response(
                {"detail": "Falsche Anmeldeinformationen oder ungültige Eingabe."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return self.create_successful_response(user)

    def create_successful_response(self, user):
        token_key = create_token_for_user(user)
        return Response(
            {
                "token": token_key,
                "username": user.username,
                "email": user.email,
                "user_id": user.id,
            },
            status=status.HTTP_200_OK,
        )


class BusinessProfileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns a list of all business profiles on the platform in the required format.
        """
        try:
            profiles = BusinessProfile.objects.all()
            response_data = [
                self.format_profile_data(profile, request) for profile in profiles
            ]
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e)

    def format_profile_data(self, profile, request):
        """
        Formats the data for a single business profile.
        """
        data = format_common_profile_data(profile, request)
        data.update(
            {
                "location": profile.location or None,
                "tel": profile.tel or None,
                "description": profile.description or None,
                "working_hours": profile.working_hours or None,
                "type": "business",
            }
        )
        return data


class CustomerProfileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns a list of all customer profiles on the platform.
        """
        try:
            profiles = CustomerProfile.objects.all()
            response_data = [
                self.format_profile_data(profile, request) for profile in profiles
            ]
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e)

    def format_profile_data(self, profile, request):
        """
        Formats the data for a single customer profile.
        """
        data = format_common_profile_data(profile, request)
        data.update(
            {
                "uploaded_at": profile.created_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "type": "customer",
            }
        )
        return data


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request, pk, format=None):
        """
        Retrieve the profile data for a specific user in a flat structure.
        """
        user, profile, profile_type = get_user_and_profile(pk)
        response = check_user_and_profile(user, profile)
        if response:
            return response

        response_data = format_profile_response(user, profile, profile_type)
        return Response(response_data, status=status.HTTP_200_OK)

    def patch(self, request, pk, format=None):
        """
        Update the profile data for a specific user.
        """
        try:
            user, profile, profile_type = get_user_and_profile(pk)
            response = check_user_and_profile(user, profile)
            if response:
                return response

            check_permissions(request, user)
            update_user_data(user, request.data)
            update_profile_data(profile, request.data)

            response_data = format_profile_response(user, profile, profile_type)
            return Response(response_data, status=status.HTTP_200_OK)

        except PermissionDenied as e:
            return handle_permission_denied(e)

        except ParseError:
            return handle_parse_error()

        except Exception:
            return handle_generic_error()


class BusinessProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk, format=None):
        """
        Retrieve the profile data for a specific business user in a flat structure.
        """
        user, profile, profile_type = get_user_and_profile(pk)

        response = check_user_and_profile(user, profile)
        if response:
            return response

        response_data = format_profile_response(user, profile, profile_type)
        return Response(response_data, status=status.HTTP_200_OK)

    def patch(self, request, pk, format=None):
        """
        Update the profile data for a specific business user.
        """
        user, profile, profile_type = get_user_and_profile(pk)
        response = check_user_and_profile(user, profile)
        if response:
            return response

        user_data = {
            key: value
            for key, value in request.data.items()
            if key in ["first_name", "last_name", "email"]
        }
        for field, value in user_data.items():
            setattr(user, field, value)
        user.save()

        profile_data = {
            key: value
            for key, value in request.data.items()
            if key in ["location", "tel", "description", "working_hours", "file"]
        }
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()

        response_data = format_profile_response(user, profile, profile_type)
        return Response(response_data, status=status.HTTP_200_OK)


class CustomerProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk, format=None):
        """
        Retrieve the customer profile data for a specific user.
        """
        user = get_user_or_error(pk)
        if isinstance(user, Response):
            return user

        customer_profile = get_customer_profile_or_error(user)
        if isinstance(customer_profile, Response):
            return customer_profile

        serializer = CustomerProfileSerializer(user.customer_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, pk, format=None):
        """
        Update the customer profile data for a specific user.
        """
        user = get_user_or_error(pk)
        if isinstance(user, Response):
            return user

        customer_profile = get_customer_profile_or_error(user)
        if isinstance(customer_profile, Response):
            return customer_profile

        serializer = CustomerProfileSerializer(
            user.customer_profile, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ReviewPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 50


class ReviewListCreateView(APIView):
    """
    GET: Lists all reviews based on filters and sorting.
    POST: Creates a new review.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Handles GET requests to retrieve reviews.
        """
        reviews = get_filtered_reviews(request.user, request.query_params)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Handles POST requests to create a new review.
        """
        if not is_customer(request.user):
            return Response(
                {"detail": "Only customers can create reviews."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            business_user = get_business_user(request.data)
            if not is_business_user(business_user):
                return Response(
                    {"detail": "The specified user is not a business user."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            if has_existing_review(request.user, business_user):
                return Response(
                    {"detail": "You have already reviewed this business user."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            review_data, status_code = create_review(
                request.data, request.user, business_user, {"request": request}
            )
            return Response(review_data, status=status_code)
        except Exception as e:
            return handle_exception(e)


class ReviewDetailView(APIView):
    """
    Handles operations on a specific review.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        """
        Retrieves a review by its ID.
        """
        review = get_object_or_404(Review, id=id)
        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id):
        """
        Partially updates a review.
        """
        try:
            review = get_object_or_404(Review, id=id)
            if not hasattr(request.user, "customer_profile"):
                return Response(
                    {"detail": "Only customers can edit reviews."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            if review.reviewer != request.user:
                return Response(
                    {"detail": "You are not authorized to edit this review."},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = ReviewSerializer(review, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e)

    def delete(self, request, id):
        """
        Deletes a review by its ID.
        """
        try:
            review = get_object_or_404(Review, id=id)
            if review.reviewer != request.user and not request.user.is_staff:
                return Response(
                    {"detail": "You are not authorized to delete this review."},
                    status=status.HTTP_403_FORBIDDEN,
                )
            review.delete()
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return handle_exception(e)


class BaseInfoView(APIView):
    """
    Handles requests for basic app statistics such as total offers, reviews, business profiles, and average rating.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """
        Returns basic statistics about the app.
        """
        try:
            data = collect_statistics()
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e)


class OrderListView(APIView):
    """
    GET: Lists all orders for the logged-in user.
    POST: Creates a new order for a specific offer detail.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieves orders for the authenticated user.
        """
        try:
            orders = get_orders_for_user(request.user)
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return handle_exception(e)

    def post(self, request):
        """
        Creates a new order for a given offer detail.
        """
        if not hasattr(request.user, "customer_profile"):
            return Response(
                {"detail": "Only customers can create orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            offer_detail = get_offer_detail(request.data.get("offer_detail_id"))
            order_data = create_order(request.user, offer_detail)
            serializer = OrderSerializer(order_data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return handle_exception(e)


class OrderDetailView(APIView):
    """
    Handles operations on a specific order such as retrieving, updating status, and deleting.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, order_id):
        """
        Retrieves the details of a specific order.
        """
        order = get_object_or_404(Order, id=order_id)
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, order_id):
        """
        Updates the status of a specific order.
        """
        if not hasattr(request.user, "business_profile"):
            return Response(
                {"detail": "Only business can update orders."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            order = Order.objects.get(id=order_id, business_user=request.user)
            update_order_status(order, request.data.get("status"))
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found or not authorized."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return handle_exception(e)

    def delete(self, request, order_id):
        """
        Deletes a specific order.
        """
        try:
            order = Order.objects.get(id=order_id, business_user=request.user)
            order.delete()
            return Response({}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found or not authorized."},
                status=status.HTTP_404_NOT_FOUND,
            )


class OrderCountView(APIView):
    """
    Retrieves the count of in-progress orders for a specific business user.
    """

    def get(self, request, business_user_id):
        business_user = fetch_business_user_by_id(business_user_id)
        if not business_user:
            return Response(
                {"error": "Business user not found."}, status=status.HTTP_404_NOT_FOUND
            )

        order_count = get_order_count(business_user, "in_progress")
        return Response({"order_count": order_count}, status=status.HTTP_200_OK)


class CompletedOrderCountView(APIView):
    """
    Retrieves the count of completed orders for a specific business user.
    """

    def get(self, request, business_user_id):
        business_user = fetch_business_user_by_id(business_user_id)
        if not business_user:
            return Response(
                {"error": "Business user not found."}, status=status.HTTP_404_NOT_FOUND
            )

        completed_order_count = get_order_count(business_user, "completed")
        return Response(
            {"completed_order_count": completed_order_count}, status=status.HTTP_200_OK
        )
