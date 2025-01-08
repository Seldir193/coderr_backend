from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import AllowAny, IsAuthenticated ,IsAuthenticatedOrReadOnly
from coder_app.serializers import (
    LoginSerializer, OrderSerializer, OfferSerializer, 
    CustomerProfileSerializer,
    ReviewSerializer, RegistrationSerializer,OrderSerializer,Order,User,OfferDetailFullSerializer
)
from coder_app.models import Offer, BusinessProfile, CustomerProfile, Review
#from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.parsers import JSONParser, MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from coder_app.models import Offer,OfferDetail,Order
from coder_app.filters import OfferFilter
from rest_framework.generics import RetrieveAPIView
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from django.shortcuts import get_object_or_404
from utils.functions import ( calculate_average_rating,
                             get_customer_profile_or_error,get_user_or_error
                             )
from utils.utils import (create_token_for_user, authenticate_user)
from django.db.models import Min
from rest_framework.permissions import BasePermission
from django_filters.rest_framework import DjangoFilterBackend


class IsOwnerOrAdmin(BasePermission):
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


class CustomPagination(PageNumberPagination):
    page_size = 6
    page_size_query_param = 'page_size'
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'results': data,
        })
        

class OfferListView(APIView):
    permission_classes = [IsAuthenticatedOrReadOnly]
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    filter_backends = [DjangoFilterBackend]
    filterset_class = OfferFilter
    pagination_class = CustomPagination
  
    def get_queryset(self):
        """
        Gibt die Basis-QuerySet mit Annotationen zurück.
        """
        return Offer.objects.annotate(
            min_price=Min('details__variant_price'),
            min_delivery_time=Min('details__delivery_time_in_days')
        )

    def get(self, request, *args, **kwargs):
        """
        Verarbeitet GET-Anfragen und gibt die gefilterten und paginierten Angebote zurück.
        """
        queryset = self.get_queryset()

        filterset = OfferFilter(request.query_params, queryset=queryset)
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)
        queryset = filterset.qs

        ordering = request.query_params.get('ordering', '-updated_at')
        if ordering in ["min_price", "-min_price", "updated_at", "-updated_at"]:
            queryset = queryset.order_by(ordering)

        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(queryset, request)
        serializer = OfferSerializer(paginated_queryset, many=True, context={"request": request})
        return paginator.get_paginated_response(serializer.data)
    
    def post(self, request, *args, **kwargs):
        if not hasattr(request.user, "business_profile"):
            return Response(
                {"error": "Only business users can create offers."},
                status=status.HTTP_403_FORBIDDEN,
            )

        details = request.data.get("details", [])
        
        if len(details) != 3 or not all(d["offer_type"] in ["basic", "standard", "premium"] for d in details):
            return Response(
                {"error": "You must provide exactly three details with offer_type: basic, standard, and premium."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = OfferSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            offer = serializer.save()
        
            response_data = {
                "id": offer.id,
                "title": offer.title,
                "image": offer.image.url if offer.image else None,
                "description": offer.description,
                "details": OfferDetailFullSerializer(offer.details.all(), many=True).data,
            }
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class OfferDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self, id):
        try:
            return Offer.objects.get(id=id)
        except Offer.DoesNotExist:
            return None

    def get(self, request, id, format=None):
        offer = self.get_object(id)
        if not offer:
            return Response({"error": "Offer not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = OfferSerializer(offer, context={"request": request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request, id, format=None):
        try:
            offer = Offer.objects.get(id=id, user=request.user)
        except Offer.DoesNotExist:
            return Response({"error": "Offer not found or you do not own this offer."}, status=status.HTTP_404_NOT_FOUND)

        details_data = request.data.pop('details', None)
        serializer = OfferSerializer(offer, data=request.data, partial=True, context={'request': request})

        if serializer.is_valid():
            offer = serializer.save()

            if details_data:
                existing_details = {detail.id: detail for detail in offer.details.all()}
                updated_ids = set()

                for detail_data in details_data:
                    detail_id = detail_data.get('id')
                    if detail_id and detail_id in existing_details:
                        
                        detail_instance = existing_details[detail_id]
                        detail_instance.variant_title = detail_data.get('title', detail_instance.variant_title)
                        detail_instance.variant_price = detail_data.get('price', detail_instance.variant_price)
                        detail_instance.revision_limit = detail_data.get('revisions', detail_instance.revision_limit)
                        detail_instance.delivery_time_in_days = detail_data.get('delivery_time_in_days', detail_instance.delivery_time_in_days)
                        detail_instance.features = detail_data.get('features', detail_instance.features)
                        detail_instance.offer_type = detail_data.get('offer_type', detail_instance.offer_type)
                        detail_instance.save()
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

            response_data = {
                "id": offer.id,
                "title": offer.title,
                "details": OfferDetailFullSerializer(offer.details.all(), many=True).data,
            }
            return Response(response_data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id, format=None):
        try:
            offer = Offer.objects.get(id=id, user=request.user)
            offer.delete()
            return Response({}, status=status.HTTP_200_OK)
        except Offer.DoesNotExist:
            return Response(
                {"error": "Offer not found or you do not have permission to delete this offer."},
                status=status.HTTP_404_NOT_FOUND
            )

 
    
class OfferDetailRetrieveView(RetrieveAPIView):
    """
    Gibt die vollständigen Details eines spezifischen Angebotsdetails zurück.
    """
    queryset = OfferDetail.objects.all()
    serializer_class = OfferDetailFullSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    lookup_field = 'id'
    


class RegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = RegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token_key = create_token_for_user(user)
            return Response({
                'token': token_key,  
                'user_id': user.id,  
                'username': user.username ,
                'email': user.email,
            }, status=status.HTTP_201_CREATED)
        errors = serializer.errors
        return Response(errors, status=status.HTTP_400_BAD_REQUEST)
       
        
class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            try:
                user = authenticate_user(username, password)
                if not user:
                    return Response({"detail": ["Falsche Anmeldedaten."]}, status=status.HTTP_400_BAD_REQUEST)
            except ValidationError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
            token_key = create_token_for_user(user)
            profile_type = "business" if hasattr(user, 'business_profile') else "customer"
            return Response({
                'token': token_key, 
                'user_id': user.id,  
                'username': user.username,  
                'profile_type': profile_type  
            }, status=status.HTTP_200_OK)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BusinessProfileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns a list of all business profiles on the platform in the required format.
        """
        try:
            profiles = BusinessProfile.objects.all()
            response_data = []

            for profile in profiles:
                user = profile.user
                file_url = request.build_absolute_uri(profile.file.url) if profile.file else None

                response_data.append({
                    "user": {
                        "pk": user.id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "file": file_url,  
                    "location": profile.location if profile.location else None,
                    "tel": profile.tel if profile.tel else None,
                    "description": profile.description if profile.description else None,
                    "working_hours": profile.working_hours if profile.working_hours else None,
                    "type": "business",
                })
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class CustomerProfileListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Returns a list of all customer profiles on the platform.
        """
        try:
            profiles = CustomerProfile.objects.all()
            response_data = []
            for profile in profiles:
                user = profile.user
                file_url = request.build_absolute_uri(profile.file.url) if profile.file else None

                response_data.append({
                    "user": {
                        "pk": user.id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                    },
                    "file": file_url,  
                    "uploaded_at": profile.created_at.strftime('%Y-%m-%dT%H:%M:%SZ'),
                    "type": "customer",
                })
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
   
class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request, pk, format=None):
        """
        Retrieve the profile data for a specific user in a flat structure.
    
        """
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "Benutzer nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        if hasattr(user, 'business_profile'):
            profile = user.business_profile
            profile_type = 'business'
        elif hasattr(user, 'customer_profile'):
            profile = user.customer_profile
            profile_type = 'customer'
        else:
            return Response({"error": "Profil nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        file_url = profile.file.url if getattr(profile, 'file', None) else None

        response_data = {
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
        return Response(response_data, status=status.HTTP_200_OK)
    
    
    def patch(self, request, pk, format=None):
        """
        Update the profile data for a specific user.
        """
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "Benutzer nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        if hasattr(user, 'business_profile'):
            profile = user.business_profile
        elif hasattr(user, 'customer_profile'):
            profile = user.customer_profile
        else:
            return Response({"error": "Profil nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        user_data = {key: value for key, value in request.data.items() if key in ['first_name', 'last_name', 'email']}
        for field, value in user_data.items():
            setattr(user, field, value)
        user.save()

        profile_data = {key: value for key, value in request.data.items() if key in ['location', 'tel', 'description', 'working_hours', 'file']}
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()
        file_url = profile.file.url if getattr(profile, 'file', None) else None

        response_data = {
            "user": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "file": file_url,  
            "location": getattr(profile, 'location', None),
            "tel": getattr(profile, 'tel', None),
            "description": getattr(profile, 'description', None),
            "working_hours": getattr(profile, 'working_hours', None),
            "type": 'business' if hasattr(user, 'business_profile') else 'customer',
            "email": user.email,
            "created_at": user.date_joined.strftime('%Y-%m-%dT%H:%M:%SZ'),
        }
        return Response(response_data, status=status.HTTP_200_OK)
    
class BusinessProfileView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser] 

    def get(self, request, pk, format=None):
        """
        Retrieve the profile data for a specific business user in a flat structure.
        """
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "Benutzer nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        if hasattr(user, 'business_profile'):
            profile = user.business_profile
            profile_type = 'business'
        elif hasattr(user, 'customer_profile'):
            profile = user.customer_profile
            profile_type = 'customer'
        else:
            return Response({"error": "Profil nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        file_url = profile.file.url if getattr(profile, 'file', None) else None
   
        response_data = {
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
        return Response(response_data, status=status.HTTP_200_OK)

    def patch(self, request, pk, format=None):
        """
        Update the profile data for a specific business user.
        """
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({"error": "Benutzer nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)
        if hasattr(user, 'business_profile'):
            profile = user.business_profile
            profile_type = 'business'
        elif hasattr(user, 'customer_profile'):
            profile = user.customer_profile
            profile_type = 'customer'
        else:
            return Response({"error": "Profil nicht gefunden."}, status=status.HTTP_404_NOT_FOUND)

        user_data = {key: value for key, value in request.data.items() if key in ['first_name', 'last_name', 'email']}
        for field, value in user_data.items():
            setattr(user, field, value)
        user.save()

        profile_data = {key: value for key, value in request.data.items() if key in ['location', 'tel', 'description', 'working_hours', 'file']}
        for field, value in profile_data.items():
            setattr(profile, field, value)
        profile.save()
        file_url = profile.file.url if getattr(profile, 'file', None) else None
        response_data = {
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
            user.customer_profile, 
            data=request.data, 
            partial=True  
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class ReviewPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
    
    

class ReviewListCreateView(APIView):
    """
    GET: Listet alle Bewertungen basierend auf Filtern und Sortierung auf.
    POST: Erstellt eine neue Bewertung.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business_user_id = request.query_params.get('business_user_id')
        ordering = request.query_params.get('ordering', 'updated_at')

        if hasattr(request.user, 'customer_profile') and not business_user_id:
           
            reviews = Review.objects.filter(reviewer=request.user)
        else:
            reviews = Review.objects.all()
            if business_user_id:
                reviews = reviews.filter(business_user_id=business_user_id)
        
        reviews = reviews.order_by(ordering)
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        try:
            if not hasattr(request.user, 'customer_profile'):
                return Response({"error": "Only customers can create reviews."}, status=status.HTTP_403_FORBIDDEN)
            business_user = get_object_or_404(User, id=request.data.get('business_user'))
            if not hasattr(business_user, 'business_profile'):
                return Response({"error": "The specified user is not a business user."}, status=status.HTTP_400_BAD_REQUEST)

            existing_review = Review.objects.filter(reviewer=request.user, business_user=business_user).first()
            if existing_review:
               return Response({"error": "You have already reviewed this business user."}, status=status.HTTP_400_BAD_REQUEST)

            serializer = ReviewSerializer(data=request.data, context={'request': request})
            if serializer.is_valid():
                serializer.save(reviewer=request.user)
                return Response(serializer.data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        review = get_object_or_404(Review, id=id)
        serializer = ReviewSerializer(review)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    def patch(self, request, id):
        try:
            review = get_object_or_404(Review, id=id)
            if not hasattr(request.user, 'customer_profile'):
                return Response({"error": "Only customers can edit reviews."}, status=status.HTTP_403_FORBIDDEN)

            if review.reviewer != request.user:
                return Response({"error": "You are not authorized to edit this review."}, status=status.HTTP_403_FORBIDDEN)

            serializer = ReviewSerializer(review, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    def delete(self, request, id):
        try:
            review = get_object_or_404(Review, id=id)
            if review.reviewer != request.user and not request.user.is_staff:
               return Response({"error": "You are not authorized to delete this review."}, status=status.HTTP_403_FORBIDDEN)
            review.delete()
            return Response({}, status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class BaseInfoView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        """
        Retrieve basic statistics about the app.
        """
        try:
            offer_count = Offer.objects.count()
            review_count = Review.objects.count()
            business_profile_count = BusinessProfile.objects.count()
            average_rating = calculate_average_rating()

            data = {
                "review_count": review_count,
                "average_rating": round(average_rating, 1) ,
                "business_profile_count": business_profile_count, 
                "offer_count": offer_count,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
  

class OrderListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user
            if hasattr(user, 'business_profile'):
                orders = Order.objects.filter(business_user=user)
            else:
                orders = Order.objects.filter(customer_user=user)
            serializer = OrderSerializer(orders, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        if not hasattr(request.user, 'customer_profile'):
            return Response({"error": "Only customers can create orders."}, status=status.HTTP_403_FORBIDDEN)

        offer_detail_id = request.data.get('offer_detail_id')
        offer_detail = get_object_or_404(OfferDetail, id=offer_detail_id)

        order = Order.objects.create(
            customer_user=request.user,
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
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, order_id):  
        order = get_object_or_404(Order, id=order_id)
        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, business_user=request.user)
            if "status" in request.data:
                new_status = request.data.get("status")
                if new_status not in ['pending', 'in_progress', 'completed', 'cancelled']:
                    return Response({"error": "Invalid status value."}, status=status.HTTP_400_BAD_REQUEST)
                order.status = new_status
                order.save()
            serializer = OrderSerializer(order)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Order.DoesNotExist:
            return Response({"error": "Order not found or not authorized."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, order_id):
        try:
            order = Order.objects.get(id=order_id, business_user=request.user)
            order.delete()
            return Response({}, status=status.HTTP_200_OK)
        except Order.DoesNotExist:
            return Response({"error": "Order not found or not authorized."}, status=status.HTTP_404_NOT_FOUND)
        
class OrderCountView(APIView):
    def get(self, request, business_user_id):
        try:
            business_user = User.objects.get(id=business_user_id)
        except User.DoesNotExist:
            return Response({"error": "Business user not found."}, status=status.HTTP_404_NOT_FOUND)
        
        order_count = Order.objects.filter(business_user=business_user, status='in_progress').count()
        return Response({"order_count": order_count}, status=status.HTTP_200_OK)


class CompletedOrderCountView(APIView):
    def get(self, request, business_user_id):
        try:
            business_user = User.objects.get(id=business_user_id)
        except User.DoesNotExist:
            return Response({"error": "Business user not found."}, status=status.HTTP_404_NOT_FOUND)
        
        completed_order_count = Order.objects.filter(business_user=business_user, status='completed').count()
        return Response({"completed_order_count": completed_order_count}, status=status.HTTP_200_OK)