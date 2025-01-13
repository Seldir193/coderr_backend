# Standard-Bibliothek
from decimal import Decimal, ROUND_DOWN
from rest_framework import serializers
from django.contrib.auth.models import User
from coder_app.models import (
    Offer,
    BusinessProfile,
    CustomerProfile,
    Order,
    Review,
    OfferDetail,
)
from utils.profile_helpers import (
    get_user_type,
    get_user_profile_image,
    create_new_user,
    create_user_profile,
    validate_password_match,
    validate_email_exists,
    validate_username_exists,
)
from django.core.validators import MinValueValidator
from utils.serializers_helpers import (
    calculate_min_price,
    calculate_min_delivery_time,
    extract_user_details,
    create_offer_details,
    update_main_instance,
    update_offer_details,
    calculate_avg_rating,
    count_pending_orders,
    update_instance_fields,
    update_user_email,
    map_status_to_display,
    validate_order_data,
    create_order_with_details,
    update_order_instance,
)


class UserProfileSerializer(serializers.ModelSerializer):
    tel = serializers.CharField(source="business_profile.tel", read_only=True)
    created_at = serializers.DateTimeField(
        source="customer_profile.created_at", read_only=True
    )
    file = serializers.SerializerMethodField()
    type = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "created_at",
            "file",
            "tel",
            "type",
        ]

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
    password = serializers.CharField(write_only=True)
    repeated_password = serializers.CharField(write_only=True)
    profile_type = serializers.ChoiceField(
        choices=[("customer", "Customer"), ("business", "Business")],
        write_only=True,
        required=False,
    )

    class Meta:
        model = User
        fields = ["username", "email", "password", "repeated_password", "profile_type"]

    def validate(self, data):
        """
        Validates the input data to ensure correctness.
        """
        errors = {}

        # Ausgelagerte Validierungen
        validate_username_exists(data["username"], errors)
        validate_email_exists(data["email"], errors)
        validate_password_match(data["password"], data["repeated_password"], errors)

        if "type" in self.initial_data:
            data["profile_type"] = self.initial_data["type"]

        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        """
        Creates a user and their profile using helper functions.
        """
        user = create_new_user(validated_data)
        profile_type = validated_data["profile_type"]
        create_user_profile(user, profile_type, validated_data)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class OfferDetailSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()

    class Meta:
        model = OfferDetail
        fields = ["id", "url"]

    def get_url(self, obj):
        return f"/offerdetails/{obj.id}/"


class OfferDetailFullSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source="variant_title")
    price = serializers.SerializerMethodField()
    revisions = serializers.IntegerField(source="revision_limit")
    features = serializers.ListField(
        child=serializers.CharField(),
        required=True,
    )
    offer_type = serializers.ChoiceField(
        choices=["basic", "standard", "premium"], required=True
    )
    delivery_time_in_days = serializers.IntegerField(
        required=True, validators=[MinValueValidator(1)]
    )

    class Meta:
        model = OfferDetail
        fields = [
            "id",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
        ]

    def validate_features(self, value):
        """Ensure at least one feature is provided."""
        if not value:
            raise serializers.ValidationError(
                "Each detail must have at least one feature."
            )
        return value

    def get_price(self, obj):
        """Format the price to two decimal places."""
        return float(Decimal(obj.variant_price).quantize(Decimal("0.00")))


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
            "id",
            "user",
            "title",
            "image",
            "description",
            "created_at",
            "updated_at",
            "details",
            "min_price",
            "min_delivery_time",
            "user_details",
        ]
        read_only_fields = [
            "id",
            "user",
            "min_price",
            "min_delivery_time",
            "created_at",
            "updated_at",
        ]

    def get_details(self, obj):
        request = self.context.get("request")
        if request and request.resolver_match.view_name == "offer-detail":
            return OfferDetailFullSerializer(obj.details.all(), many=True).data
        return OfferDetailSerializer(obj.details.all(), many=True).data

    def get_min_price(self, obj):
        return calculate_min_price(obj)

    def get_min_delivery_time(self, obj):
        return calculate_min_delivery_time(obj)

    def get_user_details(self, obj):
        return extract_user_details(obj)

    def create(self, validated_data):
        details_data = self.initial_data.get("details", [])
        user = self.context["request"].user
        image = validated_data.pop("image", None)
        offer = Offer.objects.create(user=user, image=image, **validated_data)
        create_offer_details(offer, details_data)
        return offer

    def update(self, instance, validated_data):
        details_data = self.initial_data.get("details", [])
        if details_data is None:
            details_data = []
        update_main_instance(instance, validated_data)
        update_offer_details(instance, details_data)
        return instance


class BusinessProfileSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    avg_rating = serializers.SerializerMethodField()
    pending_orders = serializers.SerializerMethodField()
    file = serializers.ImageField( required=False)
    location = serializers.CharField(required=False)
    working_hours = serializers.CharField(required=False)

    class Meta:
        model = BusinessProfile
        fields = [
            "id",
            "company_name",
            "company_address",
            "description",
            "tel",
            "location",
            "working_hours",
            "created_at",
            "user",
            "avg_rating",
            "pending_orders",
            "email",
            "username",
            "file",
        ]

    def get_avg_rating(self, obj):
        """
        Calculates the average rating for the business profile.
        """
        return calculate_avg_rating(obj)

    def get_pending_orders(self, obj):
        """
        Retrieves the count of pending orders for the business profile.
        """
        return count_pending_orders(obj)

    def update(self, instance, validated_data):
        """
        Updates the business profile with the provided validated data.
        """
        update_instance_fields(instance, validated_data)
        update_user_email(instance, validated_data.pop("user", {}))
        return instance


class OrderSerializer(serializers.ModelSerializer):
    customer_user = serializers.PrimaryKeyRelatedField(
        source="customer_user.id", read_only=True
    )
    business_user = serializers.PrimaryKeyRelatedField(
        source="business_user.id", read_only=True
    )
    title = serializers.CharField(source="offer_detail.offer.title", read_only=True)
    revisions = serializers.IntegerField(
        source="offer_detail.revision_limit", read_only=True
    )
    delivery_time_in_days = serializers.IntegerField(
        source="offer_detail.delivery_time_in_days", read_only=True
    )
    price = serializers.DecimalField(
        source="offer_detail.variant_price",
        max_digits=10,
        decimal_places=2,
        read_only=True,
    )
    features = serializers.ListField(
        source="offer_detail.features", child=serializers.CharField(), read_only=True
    )
    offer_type = serializers.CharField(source="offer_detail.offer_type", read_only=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "customer_user",
            "business_user",
            "title",
            "revisions",
            "delivery_time_in_days",
            "price",
            "features",
            "offer_type",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields

    def get_status_display(self, obj):
        return map_status_to_display(obj.status)

    def validate(self, data):
        return validate_order_data(self.context["request"].user, data)

    def create(self, validated_data):
        return create_order_with_details(validated_data)

    def update(self, instance, validated_data):
        return update_order_instance(instance, validated_data)


class CustomerProfileSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = CustomerProfile
        fields = "__all__"

    def get_file_url(self, obj):
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if obj.file else None


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            "id",
            "business_user",
            "reviewer",
            "rating",
            "description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "reviewer", "created_at", "updated_at"]
