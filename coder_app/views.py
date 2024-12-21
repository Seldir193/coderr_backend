from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated 
from coder_app.serializers import (
    LoginSerializer, OrderSerializer, OfferSerializer, 
    BusinessProfileSerializer, CustomerProfileSerializer,
    ReviewSerializer, RegistrationSerializer,OrderSerializer
)
from coder_app.models import Offer, BusinessProfile, CustomerProfile, Review, OfferDetail
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListCreateAPIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from coder_app.models import Offer
from coder_app.filters import OfferFilter

#from utils.utils import error_response
from utils.functions import ( get_offer_or_none,update_offer,calculate_average_rating,
                             get_offer_and_delete,
                             get_orders_for_user, create_order,
                             get_offers_for_user,get_business_profile_or_error,
                             get_profile_data,build_profile_response,
                             update_profile_data,get_customer_profile_or_error,
                             get_user_orders,
                             get_in_progress_count,get_user_or_error,count_completed_orders_for_user,
                             get_order_or_403,validate_offer_detail,create_order_for_user,get_review_or_404, permission_error_response)

from utils.utils import (create_token_for_user, authenticate_user,
                         error_response,serialize_orders)

     
class CustomPagination(PageNumberPagination):
    # Default number of items per page
    page_size = 6
    
    # Query parameter to allow the client to customize the page size
    page_size_query_param = 'page_size'
    
    # Maximum number of items allowed per page
    max_page_size = 100
   
    def get_paginated_response(self, data):
        # Returns a custom paginated response including additional metadata
        return Response({
            'count': self.page.paginator.count,  # Total number of items
            'total_pages': self.page.paginator.num_pages,  # Total number of pages
            'current_page': self.page.number,  # Current page number
            'results': data  # Paginated data
        })
        

class RegistrationView(APIView):
    # Allows any user (authenticated or not) to access this view
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        # Deserialize and validate the incoming data
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            # Save the user instance if the data is valid
            user = serializer.save()
            # Create a token for the newly registered user
            token_key = create_token_for_user(user)
            return Response({
                'token': token_key,  # Return the authentication token
                'user_id': user.id,  # Return the user ID
                'username': user.username  # Return the username
            }, status=status.HTTP_201_CREATED)
        # Return an error response if the data is invalid
        return error_response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class LoginView(APIView):
    # Allows any user (authenticated or not) to access this view
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        # Deserialize and validate the incoming data
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            # Extract username and password from the validated data
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            try:
                # Authenticate the user using the provided credentials
                user = authenticate_user(username, password)
            except ValidationError as e:
                # Return an error response if authentication fails
                return error_response(str(e), status=status.HTTP_400_BAD_REQUEST)

            # Create a token for the authenticated user
            token_key = create_token_for_user(user)
            # Determine the profile type based on the user's associated profile
            profile_type = "business" if hasattr(user, 'business_profile') else "customer"

            return Response({
                'token': token_key,  # Return the authentication token
                'user_id': user.id,  # Return the user ID
                'username': user.username,  # Return the username
                'profile_type': profile_type  # Return the user's profile type (business or customer)
            }, status=status.HTTP_200_OK)

        # Return an error response if the data is invalid
        return error_response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
        
class OfferListView(ListCreateAPIView):
    """
    API endpoint for listing offers and creating new offers.
    """
    serializer_class = OfferSerializer
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['delivery_time_in_days']  # Fields available for filtering
    filterset_class = OfferFilter  # Custom filter class
    ordering_fields = ['created_at', 'updated_at', 'price']  # Fields available for ordering
    ordering = ['-created_at', 'price']  # Default ordering by creation date (descending) and price
    permission_classes = [AllowAny]  # Allows access to any user
    pagination_class = CustomPagination  # Custom pagination for offer lists
    
    def get_queryset(self):
        # Retrieves offers based on the 'creator_id' query parameter or for the logged-in user
        creator_id = self.request.query_params.get('creator_id')
        
        if creator_id:
            # Filter offers by the creator's user ID if provided
            return Offer.objects.filter(user_id=creator_id) 
        # Return offers accessible to the current user
        return get_offers_for_user(self.request.user)
    
    def perform_create(self, serializer):
        """
        Overrides the creation logic to set the user.
        """
        user = self.request.user
        # Ensure the user is authenticated and has a business profile
        if user.is_authenticated and hasattr(user, 'business_profile'):
            serializer.save(user=user)  # Save the offer with the associated user
        else:
            # Raise an error if the user is not a business provider
            raise ValidationError("Only providers can create offers.")
        
    
class OfferDetailView(APIView):
    # Requires the user to be authenticated to access this view
    permission_classes = [IsAuthenticated]  
    
    def get(self, request, id, format=None):
        """
        Retrieve an offer based on its ID.
        """
        offer = get_offer_or_none(id)  # Fetch the offer or return None if not found
        if offer:
            serializer = OfferSerializer(offer)  # Serialize the offer data
            return Response(serializer.data, status=status.HTTP_200_OK)  # Return serialized data
        return Response({"error": "Offer not found"}, status=status.HTTP_404_NOT_FOUND)  # Return an error if not found
    
    def patch(self, request, id, format=None):
        # Update an offer with partial data (PATCH method)
        return update_offer(id, request.user, request)

    def delete(self, request, id, format=None):
        """
        Delete an offer. Only the creator of the offer can delete it.
        """
        return get_offer_and_delete(id, request.user)  # Perform delete operation and handle permissions

        
class BusinessProfileListView(APIView):
    # Requires the user to be authenticated to access this view
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            # Retrieve all business profiles from the database
            profiles = BusinessProfile.objects.all()  
            # Serialize the business profiles
            serializer = BusinessProfileSerializer(profiles, many=True)  
            # Return serialized data with a 200 OK status
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            # Handle any unexpected errors and return a 500 Internal Server Error
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CustomerProfileListView(APIView):
    # Requires the user to be authenticated to access this view
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Retrieve all customer profiles from the database
        profiles = CustomerProfile.objects.all()
        # Serialize the customer profiles
        serializer = CustomerProfileSerializer(profiles, many=True)
        # Return serialized data with a 200 OK status
        return Response(serializer.data, status=status.HTTP_200_OK)
    
        
class BusinessProfileView(APIView):
    # Requires the user to be authenticated to access this view
    permission_classes = [IsAuthenticated]
    # Supports parsing multipart form data (e.g., file uploads) and regular form data
    parser_classes = [MultiPartParser, FormParser] 
    
    def get(self, request, user_id, format=None):
        # Retrieve the user or return an error response if the user does not exist
        user = get_user_or_error(user_id)
        if isinstance(user, Response):  
            return user
        
        # Retrieve the business profile or return an error response if not found
        business_profile = get_business_profile_or_error(user)
        if isinstance(business_profile, Response):  
            return business_profile
        
        # Serialize the business profile and return the data
        serializer = BusinessProfileSerializer(user.business_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, user_id, format=None):
        # Retrieve the user or return an error response if the user does not exist
        user = get_user_or_error(user_id)  
        if isinstance(user, Response):  
            return user
        
        # Retrieve the business profile or return an error response if not found
        business_profile = get_business_profile_or_error(user)
        if isinstance(business_profile, Response):  
            return business_profile

        # Serialize and update the business profile with partial data
        serializer = BusinessProfileSerializer(
            business_profile,
            data=request.data,
            partial=True  # Allows partial updates
        )
        if serializer.is_valid():
            # Save the updated business profile and return the serialized data
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Return an error response if the data is invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

 
class ProfileView(APIView):
    # Requires the user to be authenticated to access this view
    permission_classes = [IsAuthenticated]
    # Supports parsing multipart form data (e.g., file uploads) and regular form data
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, user_id, format=None):
        """
        Retrieve the profile data for a specific user.
        """
        # Retrieve the user or return an error response if the user does not exist
        user = get_user_or_error(user_id)
        if isinstance(user, Response):  
            return user

        # Determine the profile type and retrieve the associated profile data
        profile_type, profile_data = get_profile_data(user)
        profile_image = profile_data.get("profile_image") if profile_type == 'business' else profile_data.get("file")
        
        # Build the response data for the user's profile
        response_data = build_profile_response(user, profile_type, profile_data, profile_image)
        return Response(response_data, status=status.HTTP_200_OK)

    def patch(self, request, user_id, format=None):
        """
        Update the profile data for a specific user.
        """
        # Retrieve the user or return an error response if the user does not exist
        user = get_user_or_error(user_id)
        if isinstance(user, Response):  
            return user

        # Update the profile data with the provided input
        return update_profile_data(user, request.data)
    
        
class CustomerProfileView(APIView):
    # Requires the user to be authenticated to access this view
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, format=None):
        """
        Retrieve the customer profile data for a specific user.
        """
        # Retrieve the user or return an error response if the user does not exist
        user = get_user_or_error(user_id)
        if isinstance(user, Response):  
            return user
        
        # Retrieve the customer profile or return an error response if not found
        customer_profile = get_customer_profile_or_error(user)
        if isinstance(customer_profile, Response):  
            return customer_profile
        
        # Serialize the customer profile and return the data
        serializer = CustomerProfileSerializer(user.customer_profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, user_id, format=None):
        """
        Update the customer profile data for a specific user.
        """
        # Retrieve the user or return an error response if the user does not exist
        user = get_user_or_error(user_id)
        if isinstance(user, Response):  
            return user
        
        # Retrieve the customer profile or return an error response if not found
        customer_profile = get_customer_profile_or_error(user)
        if isinstance(customer_profile, Response):  
            return customer_profile
        
        # Serialize and update the customer profile with partial data
        serializer = CustomerProfileSerializer(
            user.customer_profile, 
            data=request.data, 
            partial=True  # Allows partial updates
        )
        if serializer.is_valid():
            # Save the updated customer profile and return the serialized data
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        # Return an error response if the data is invalid
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class OrderListView(APIView):
    # Requires the user to be authenticated to access this view
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve orders based on the user type (provider or customer).
        """
        user = request.user
        # Get orders relevant to the current user
        orders = get_orders_for_user(user)
        # Serialize the list of orders
        serializer = OrderSerializer(orders, many=True)
        # Return the serialized data with a 200 OK status
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new order.
        """
        # Pass the incoming data and the user to the order creation logic
        return create_order(request.data, request.user)

    
class UserOrdersView(APIView):
    # Requires the user to be authenticated to access this view
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Retrieve orders specific to the authenticated user.
        """
        # Fetch orders associated with the current user
        orders = get_user_orders(request.user)
        # Serialize the orders using a custom serialization function
        serialized_data = serialize_orders(orders)
        # Return the serialized data with a 200 OK status
        return Response(serialized_data, status=status.HTTP_200_OK)


class ReviewPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
    

class ReviewListView(ListCreateAPIView):
    """
    API view for retrieving and creating reviews.
    """
    # Define the queryset to retrieve all reviews
    queryset = Review.objects.all()
    # Use the ReviewSerializer to handle serialization and deserialization
    serializer_class = ReviewSerializer
    # Add filtering and ordering capabilities
    filter_backends = [OrderingFilter, DjangoFilterBackend]
    # Allow ordering by creation date, update date, or rating
    ordering_fields = ['created_at', 'updated_at', 'rating']
    # Default ordering by most recently updated first
    ordering = ['-updated_at']
    # Require the user to be authenticated to access this view
    permission_classes = [IsAuthenticated] 

    def get_queryset(self):
        """
        Customize the queryset based on query parameters.
        """
        # Get the base queryset
        queryset = super().get_queryset()
        
        # Filter by reviewer ID if provided in the query parameters
        reviewer_id = self.request.query_params.get('reviewer_id')
        if reviewer_id:
            queryset = queryset.filter(reviewer_id=reviewer_id)

        # Filter by offer ID if provided in the query parameters
        offer_id = self.request.query_params.get('offer_id')
        if offer_id:
            queryset = queryset.filter(offer_id=offer_id)

        # Filter by business user ID if provided in the query parameters
        business_user_id = self.request.query_params.get('business_user_id')
        if business_user_id:
            queryset = queryset.filter(business_user_id=business_user_id)
        
        return queryset
    
    def perform_create(self, serializer):
        """
        Handle the creation of a new review.
        """
        user = self.request.user

        # Ensure only customers can write reviews
        if not hasattr(user, 'customer_profile'):
            raise ValidationError("Only customers can write reviews.")

        # Ensure the same reviewer cannot review the same business user more than once
        business_user = serializer.validated_data['business_user']
        if Review.objects.filter(business_user=business_user, reviewer=user).exists():
            raise ValidationError("You have already reviewed this provider.")

        # Save the review with the current user as the reviewer
        serializer.save(reviewer=user)


class ReviewDetailView(APIView):
    def patch(self, request, pk):
        # Get the review or return a 404 if not found
        review = get_review_or_404(pk)

        # Ensure that only the reviewer can edit their own review
        if review.reviewer != request.user:
            return permission_error_response("You can only edit your own reviews.")

        # Partially update the review
        serializer = ReviewSerializer(review, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # Get the review or return a 404 if not found
        review = get_review_or_404(pk)

        # Ensure that only the reviewer can delete their own review
        if review.reviewer != request.user:
            return permission_error_response("You can only delete your own reviews.")

        # Delete the review
        review.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
    

class OrderInProgressCountView(APIView):
    def get(self, request, offer_id, *args, **kwargs):
        """
        Get the count of orders in progress for a specific offer.
        """
        try:
            offer = get_offer_or_none(offer_id)
            if not offer:
                return error_response("Offer not found.", status.HTTP_404_NOT_FOUND)

            try:
                # Calculate the count of in-progress orders for the user and offer
                in_progress_count = get_in_progress_count(request.user, offer)
            except ValidationError as e:
                return error_response(str(e), status.HTTP_403_FORBIDDEN)

            return Response({'in_progress_count': in_progress_count}, status=status.HTTP_200_OK)

        except Exception as e:
            return error_response(f"Unexpected error: {str(e)}", status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class OrderCompletedCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, user_id, *args, **kwargs):
        """
        Get the count of completed orders for a specific user.
        """
        try:
            user = get_user_or_error(user_id)
            # Calculate the count of completed orders for the user
            completed_count = count_completed_orders_for_user(user)
            return Response({'completed_order_count': completed_count}, status=status.HTTP_200_OK)

        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f"Unexpected error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request, order_id, format=None):
        """
        Update an order's details.
        """
        try:
            # Get the order and ensure the user has permission to modify it
            order = get_order_or_403(order_id, request.user)
            # Partially update the order
            serializer = OrderSerializer(order, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_403_FORBIDDEN)
        

class CreateOrderView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """
        Create a new order for a specific offer detail.
        """
        offer_detail_id = request.data.get("offer_detail_id")
        user = request.user

        # Superusers are not allowed to create orders
        if user.is_superuser:
            return Response(
                {"error": "Superusers cannot create orders."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Validate the provided offer detail ID
        validation_error = validate_offer_detail(offer_detail_id)
        if validation_error:
            return validation_error

        try:
            # Retrieve the offer detail and create the order
            offer_detail = OfferDetail.objects.get(id=offer_detail_id)
            order = create_order_for_user(user, offer_detail)
            return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response(
                {"error": f"Error creating the order: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            

class BaseInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Retrieve basic statistics about the app.
        """
        try:
            # Fetch counts and statistics
            offer_count = Offer.objects.count()
            review_count = Review.objects.count()
            business_profile_count = BusinessProfile.objects.count()
            average_rating = calculate_average_rating()

            # Compile the data into a response
            data = {
                "offer_count": offer_count,  # Total number of offers
                "review_count": review_count,  # Total number of reviews
                "business_profile_count": business_profile_count,  # Total number of business profiles
                "average_rating": round(average_rating, 1)  # Average rating rounded to one decimal place
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        
        
        


        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        

        
