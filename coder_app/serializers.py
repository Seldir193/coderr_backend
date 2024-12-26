from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from coder_app.models import Offer, BusinessProfile, CustomerProfile, Order, Review, OfferDetail
from django.db.models import Avg
from utils.profile_helpers import get_user_type, get_user_profile_image,create_new_user, create_user_profile
from django.core.validators import MinValueValidator

# serializers
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
    profile_type = serializers.ChoiceField(choices=[('customer', 'Customer'), ('business', 'Business')], write_only=True)
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'repeated_password', 'profile_type']
        
    def validate(self, data):
        """
        Validates input data, ensuring required fields are present and unique constraints are met.
        """
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({"email": "This email is already in use."})
        if data['password'] != data['repeated_password']:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return data
        
    def create(self, validated_data):
        """
        Creates a new user and their associated profile based on profile type.
        """
        user = create_new_user(validated_data)
        profile_type = validated_data['profile_type']
        create_user_profile(user, profile_type, validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class OfferDetailSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='variant_title')
    price = serializers.DecimalField(source='variant_price', max_digits=10, decimal_places=2)
    revisions = serializers.IntegerField(source='revision_limit')
    features = serializers.ListField(child=serializers.CharField(), default=list)
    offer_type = serializers.CharField(required=True)
    delivery_time_in_days = serializers.IntegerField(
        required=True, 
        validators=[MinValueValidator(1)]
    )

    class Meta:
        model = OfferDetail
        fields = [
            'id', 'title', 'price', 'delivery_time_in_days',
            'revisions', 'additional_details', 'offer_type', 'features'
        ]
        
class BusinessProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    avg_rating = serializers.SerializerMethodField()
    pending_orders = serializers.SerializerMethodField()
    profile_image = serializers.ImageField(required=False)
    location = serializers.CharField(required=False)
    working_hours = serializers.CharField(required=False)

    class Meta:
        model = BusinessProfile
        fields = [
            'id', 'company_name', 'company_address', 'company_website',
            'description', 'tel', 'location', 'working_hours', 'created_at',
            'user', 'avg_rating', 'pending_orders', 'email', 'username', 'profile_image'
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
        for field in ['company_name', 'company_address', 'company_website', 'description', 'tel', 'location', 'working_hours']:
            setattr(instance, field, validated_data.get(field, getattr(instance, field)))
        if 'profile_image' in validated_data:
            instance.profile_image = validated_data['profile_image']
        instance.save()

        if 'email' in validated_data:
            instance.user.email = validated_data['email']
            instance.user.save()

        return instance
    
class OfferSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    business_profile = serializers.SerializerMethodField()
    description = serializers.CharField(required=False, allow_blank=True)
    details = OfferDetailSerializer(many=True, required=False)

    class Meta:
        model = Offer
        fields = [
            'id', 'title', 'description', 'price', 'delivery_time_in_days',
            'min_price', 'min_delivery_time', 'image', 'created_at',
            'updated_at', 'details', 'user', 'business_profile'
        ]

    def get_business_profile(self, obj):
        """
        Retrieves the business profile associated with the offer's creator.
        """
        return BusinessProfileSerializer(obj.user.business_profile).data if hasattr(obj.user, 'business_profile') else None

    def create(self, validated_data):
        """
        Creates a new offer along with its associated details.
        """
        details_data = validated_data.pop('details', [])
        offer = Offer.objects.create(**validated_data)
        for detail_data in details_data:
            OfferDetail.objects.create(offer=offer, **detail_data)
        return offer

    def update(self, instance, validated_data):
        """
        Updates the offer and its associated details.
        """
        self._update_offer_fields(instance, validated_data)
        self._update_or_create_details(instance, validated_data.pop('details', []))
        return instance

    def _update_offer_fields(self, instance, validated_data):
        """
        Helper method to update the fields of the offer.
        """
        for field in ['title', 'description', 'price', 'delivery_time_in_days', 'image']:
            setattr(instance, field, validated_data.get(field, getattr(instance, field)))
        instance.save()

    def _update_or_create_details(self, instance, details_data):
        """
        Helper method to update existing OfferDetails or create new ones.
        """
        existing_details = {detail.id: detail for detail in instance.details.all()}
        for offer_type, detail_data in {detail.get('offer_type'): detail for detail in details_data}.items():
            existing_detail = next((detail for detail in existing_details.values() if detail.offer_type == offer_type), None)
            if existing_detail:
                self._update_existing_detail(existing_detail, detail_data)
            else:
                OfferDetail.objects.create(offer=instance, **detail_data)

    def _update_existing_detail(self, existing_detail, detail_data):
        """
        Helper method to update an existing OfferDetail.
        """
        for attr, value in detail_data.items():
            if attr != 'id':
                setattr(existing_detail, attr, value)
        existing_detail.save()

class OrderSerializer(serializers.ModelSerializer):
    offer_title = serializers.CharField(source='offer_detail_id.offer.title', read_only=True)
    offer_provider = serializers.CharField(source='offer.user.username', read_only=True)
    offer_price = serializers.DecimalField(source='offer_detail_id.variant_price', max_digits=10, decimal_places=2, read_only=True)
    offer_delivery_time = serializers.IntegerField(source='offer_detail_id.delivery_time_in_days', read_only=True)
    offer_revision_limit = serializers.IntegerField(source='offer_detail_id.revision_limit', read_only=True)
    offer_description = serializers.CharField(source='offer.description', read_only=True)

    status_display = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), write_only=True)
    user_details = UserProfileSerializer(source='user', read_only=True)
    business_user = UserProfileSerializer(source='offer.user', read_only=True)

    class Meta:
        model = Order
        fields = [
            'id', 'user', 'user_details', 'offer', 'offer_detail_id',
            'status', 'status_display', 'option', 'created_at', 'updated_at',
            'offer_title', 'offer_provider', 'offer_price',
            'offer_delivery_time', 'offer_revision_limit', 'offer_description',
            'features', 'business_user'
        ]

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
        return obj.offer_detail_id.features if obj.offer_detail_id and obj.offer_detail_id.features else []

    def validate_offer_detail_id(self, value):
        """
        Validates that the provided OfferDetail exists.
        """
        if not OfferDetail.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("The specified OfferDetail does not exist.")
        return value

    def create(self, validated_data):
        """
        Creates a new order with the validated data.
        """
        offer_detail = validated_data.get('offer_detail_id')
        return self._create_order(validated_data, offer_detail)

    def update(self, instance, validated_data):
        """
        Updates the order instance with the provided validated data.
        """
        previous_status = instance.status
        self._update_order_fields(instance, validated_data)
        self._check_status_change(instance, previous_status)
        return instance

    def _create_order(self, validated_data, offer_detail):
        """
        Helper method for creating an order.
        """
        validated_data['offer'] = offer_detail.offer
        validated_data['features'] = offer_detail.features or []
        return super().create(validated_data)

    def _update_order_fields(self, instance, validated_data):
        """
        Updates the fields of the order.
        """
        fields_to_update = ['status', 'offer_detail_id']
        for field in fields_to_update:
            setattr(instance, field, validated_data.get(field, getattr(instance, field)))
        instance.save()

    def _check_status_change(self, instance, previous_status):
        """
        Checks if the order status has changed to 'in_progress'.
        """
        if previous_status != 'in_progress' and instance.status == 'in_progress':
            print(f"Order {instance.id} status changed to 'in_progress'.")

class CustomerProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    class Meta:
        model = CustomerProfile
        fields = '__all__'
        
class ReviewSerializer(serializers.ModelSerializer):
    business_user = UserProfileSerializer(read_only=True)
    reviewer = UserProfileSerializer(read_only=True)
    average_rating = serializers.SerializerMethodField()

    business_user_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="business_user"
    )
    reviewer_id = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(), write_only=True, source="reviewer"
    )

    class Meta:
        model = Review
        fields = [
            'id', 'rating', 'description', 'business_user', 'business_user_id',
            'reviewer', 'reviewer_id', 'created_at', 'average_rating'
        ]

    def get_average_rating(self, obj):
        """
        Calculates the average rating for the associated business user.
        """
        return Review.objects.filter(business_user=obj.business_user).aggregate(
            avg=Avg('rating')
        )['avg'] or 0.0

    def validate(self, data):
        """
        Custom validation for reviews.
        """
        if self.instance is None:  # Validation for new reviews only
            business_user = data.get('business_user')
            reviewer = data.get('reviewer')

            if not hasattr(reviewer, 'customer_profile'):
                raise serializers.ValidationError({
                    "reviewer_id": "Only customers can write reviews."
                })

            if Review.objects.filter(business_user=business_user, reviewer=reviewer).exists():
                raise serializers.ValidationError({
                    "business_user_id": "You have already reviewed this provider."
                })
        return data

    def update(self, instance, validated_data):
        """
        Updates an existing review object with the provided validated data.
        """
        # Only update fields explicitly provided in validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

        





        
