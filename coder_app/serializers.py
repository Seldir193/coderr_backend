from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from coder_app.models import Offer, BusinessProfile, CustomerProfile, Order, Review, OfferDetail
from django.db.models import Avg
from utils.profile_helpers import get_user_type, get_user_profile_image,create_new_user, create_user_profile
from django.urls import reverse
from django.db.models import Min
from django.core.validators import MinValueValidator
from decimal import Decimal, ROUND_DOWN


class UserProfileSerializer(serializers.ModelSerializer):
    tel = serializers.CharField(source='business_profile.tel', read_only=True)
    created_at = serializers.DateTimeField(
        source='customer_profile.created_at', 
        read_only=True
    )
    file = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'created_at', 'file', 'tel', 'type']

    def get_type(self, obj):
        """
        Retrieves the type of user: superuser, business, or customer.
        """
        return get_user_type(obj)  

    def get_file(self, obj):
        """
        Retrieves the profile image URL based on the user profile type.
        """
        return get_user_profile_image(obj) 
    
class RegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, validators=[validate_password])
    repeated_password = serializers.CharField(write_only=True)
    profile_type = serializers.ChoiceField(
        choices=[('customer', 'Customer'), ('business', 'Business')],
        write_only=True,
        required=False 
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'profile_type']

    def validate(self, data):
        """
        Validates the input data to ensure correctness.
        """
        errors = {}

        if User.objects.filter(username=data['username']).exists():
            errors.setdefault('username', []).append("Dieser Benutzername ist bereits vergeben.")

        if User.objects.filter(email=data['email']).exists():
            errors.setdefault('email', []).append("Diese E-Mail-Adresse wird bereits verwendet.")

        if data['password'] != data['repeated_password']:
            errors.setdefault('password', []).append("Das Passwort ist nicht gleich mit dem wiederholten Passwort.")
        
        try:
            validate_password(data['password'])
        except serializers.ValidationError as e:
            errors.setdefault('password', []).extend(e.messages)

        if 'type' in self.initial_data:
            data['profile_type'] = self.initial_data['type']
        
        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """
        Creates a user and their profile using helper functions.
        """
        user = create_new_user(validated_data)
        profile_type = validated_data['profile_type']
        create_user_profile(user, profile_type, validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    
class OfferDetailSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ['id', 'url']

    def get_url(self, obj):
        return f"/offerdetails/{obj.id}/"
    

class OfferDetailFullSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='variant_title')
    #price = serializers.DecimalField(source='variant_price', max_digits=10, decimal_places=2)
    price = serializers.SerializerMethodField()
    revisions = serializers.IntegerField(source='revision_limit')
    features = serializers.ListField(
        child=serializers.CharField(),
        required=True,  
    )
    offer_type = serializers.ChoiceField(choices=['basic', 'standard', 'premium'], required=True)
    delivery_time_in_days = serializers.IntegerField(
        required=True,
        validators=[MinValueValidator(1)]  
    )

    class Meta:
        model = OfferDetail
        fields = [
            'id', 'title', 'revisions', 'delivery_time_in_days', 'price',
            'features', 'offer_type'
        ]

    def validate_features(self, value):
        """
        Validiert, dass mindestens ein Feature angegeben ist.
        """
        if not value:
            raise serializers.ValidationError("Each detail must have at least one feature.")
        return value
    
    def get_price(self, obj):
        return float(Decimal(obj.variant_price).quantize(Decimal('0.00')))
    
  
class OfferSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    details = serializers.SerializerMethodField()
    min_price = serializers.SerializerMethodField()
    min_delivery_time = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    
    class Meta:
        model = Offer
        fields = [
            'id', 'user', 'title', 'image', 'description', 'created_at',
            'updated_at', 'details', 'min_price', 'min_delivery_time',
            'user_details'
        ]
        read_only_fields = ['id', 'user', 'min_price', 'min_delivery_time', 'created_at', 'updated_at']
        
    
    def get_details(self, obj):
        request = self.context.get('request')
        print("View Name:", request.resolver_match.view_name)
        if request and request.resolver_match.view_name == 'offer-detail':
            return OfferDetailFullSerializer(obj.details.all(), many=True).data
        return OfferDetailSerializer(obj.details.all(), many=True).data


    def get_min_price(self, obj):
        min_price = obj.details.aggregate(min_price=Min('variant_price'))['min_price']
        if min_price is not None:
          return float(Decimal(min_price).quantize(Decimal('0.00')))
        return None

    def get_min_delivery_time(self, obj):
        return obj.details.aggregate(min_delivery_time=Min('delivery_time_in_days'))['min_delivery_time']

    def get_user_details(self, obj):
        user = obj.user
        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
        }
        
    def create(self, validated_data):
        details_data = self.initial_data.get('details', [])
        print("Details received in serializer:", details_data)
        user = self.context['request'].user
        #offer = Offer.objects.create(user=user, **validated_data)
        
        #offer = Offer.objects.create(user=self.context['request'].user, **validated_data)
        
        image = validated_data.pop('image', None)
        offer = Offer.objects.create(user=user, image=image, **validated_data)
        
        for detail_data in details_data:
            OfferDetail.objects.create(
                offer=offer,
                variant_title=detail_data['title'], 
                variant_price=detail_data['price'],
                revision_limit=detail_data['revisions'], 
                delivery_time_in_days=detail_data['delivery_time_in_days'],
                features=detail_data['features'],
                offer_type=detail_data['offer_type']
            )
        return offer

    def update(self, instance, validated_data):
        details_data = self.initial_data.get('details', [])
        
        image = validated_data.pop('image', None) 
        print("Update Image:", image)
    
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        if image:
            instance.image = image
        instance.save()

        if details_data:
            existing_details = {detail.offer_type: detail for detail in instance.details.all()}
            updated_offer_types = set()

            for detail_data in details_data:
                offer_type = detail_data.get('offer_type')
                if offer_type in existing_details:
                    
                    detail_instance = existing_details[offer_type]
                    for attr, value in detail_data.items():
                        setattr(detail_instance, attr, value)
                    detail_instance.save()
                    updated_offer_types.add(offer_type)
                else:
                    OfferDetail.objects.create(
                        offer=instance,
                        variant_title=detail_data['title'],
                        variant_price=detail_data['price'],
                        revision_limit=detail_data['revisions'],
                        delivery_time_in_days=detail_data['delivery_time_in_days'],
                        features=detail_data['features'],
                        offer_type=offer_type,
                    )
                    updated_offer_types.add(offer_type)

            for offer_type, detail_instance in existing_details.items():
                if offer_type not in updated_offer_types:
                    detail_instance.delete()

        return instance


class BusinessProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    avg_rating = serializers.SerializerMethodField()
    pending_orders = serializers.SerializerMethodField()
    file = serializers.ImageField(source='file', required=False)  
    location = serializers.CharField(required=False)
    working_hours = serializers.CharField(required=False)

    class Meta:
        model = BusinessProfile
        fields = [
            'id', 'company_name', 'company_address', 
            'description', 'tel', 'location', 'working_hours', 'created_at',
            'user', 'avg_rating', 'pending_orders', 'email', 'username', 'file'
        ]

    def get_avg_rating(self, obj):
        """
        Calculates the average rating for the business profile.
        """
        avg = Review.objects.filter(business_user=obj.user).aggregate(Avg('rating'))['rating__avg']
        return round(avg, 1) if avg else '-'

    def get_pending_orders(self, obj):
        """
        Retrieves the count of pending orders for the business profile.
        """
        return Order.objects.filter(business_user=obj.user, status__in=['in_progress']).count()

    def update(self, instance, validated_data):
        """
        Updates the business profile with the provided validated data.
        """
        user_data = validated_data.pop('user', {})
        for field in ['company_name', 'company_address', 'description', 'tel', 'location', 'working_hours']:
            setattr(instance, field, validated_data.get(field, getattr(instance, field)))

        if 'file' in validated_data:
            instance.file = validated_data['file']
        instance.save()

        if 'email' in user_data:
            instance.user.email = user_data['email']
            instance.user.save()
        return instance
    

class OrderSerializer(serializers.ModelSerializer):
    customer_user = serializers.PrimaryKeyRelatedField(source='customer_user.id', read_only=True)
    business_user = serializers.PrimaryKeyRelatedField(source='business_user.id', read_only=True)
    title = serializers.CharField(source='offer_detail.offer.title', read_only=True)
    revisions = serializers.IntegerField(source='offer_detail.revision_limit', read_only=True)
    delivery_time_in_days = serializers.IntegerField(source='offer_detail.delivery_time_in_days', read_only=True)
    price = serializers.DecimalField(source='offer_detail.variant_price', max_digits=10, decimal_places=2, read_only=True)
    features = serializers.ListField(source='offer_detail.features', child=serializers.CharField(), read_only=True)
    offer_type = serializers.CharField(source='offer_detail.offer_type', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'customer_user', 'business_user', 'title',
            'revisions', 'delivery_time_in_days', 'price',
            'features', 'offer_type', 'status', 'created_at', 'updated_at',
        ]
        read_only_fields = fields

    def get_status_display(self, obj):
        """
        Maps the order status to a user-friendly display name.
        """
        status_mapping = {
            'pending': 'Pending',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'cancelled': 'Cancelled'
        }
        return status_mapping.get(obj.status, 'Unknown Status')

    def get_features(self, obj):
        """
        Retrieves the features of the order from the associated OfferDetail.
        """
        return obj.offer_detail.features if obj.offer_detail and obj.offer_detail.features else []

    def validate(self, data):
        """
        Validates the data to ensure only customers can create orders
        and that the provided OfferDetail is valid.
        """
        user = self.context['request'].user

        if hasattr(user, 'business_profile'):
            raise serializers.ValidationError("Business profiles cannot create orders.")

        offer_detail = data.get('offer_detail')
        if not offer_detail:
            raise serializers.ValidationError("OfferDetail is required to create an order.")
        if not OfferDetail.objects.filter(id=offer_detail.id).exists():
            raise serializers.ValidationError("The specified OfferDetail does not exist.")

        data['customer_user'] = user
        return data

    def create(self, validated_data):
        """
        Creates a new order with the validated data.
        """
        offer_detail = validated_data.get('offer_detail')
        validated_data['offer'] = offer_detail.offer
        validated_data['features'] = offer_detail.features or []
        validated_data['business_user'] = offer_detail.offer.user
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """
        Updates the order instance with the provided validated data.
        """
        for field, value in validated_data.items():
            setattr(instance, field, value)
        instance.save()
        return instance



class CustomerProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = CustomerProfile
        fields = '__all__'
        
    def get_file_url(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if obj.file else None

        
class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['id', 'business_user', 'reviewer', 'rating', 'description', 'created_at', 'updated_at']
        read_only_fields = ['id', 'reviewer', 'created_at', 'updated_at']
        