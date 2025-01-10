from rest_framework import serializers
from django.db.models import Min
from decimal import Decimal
from coder_app.models import Order,Review,OfferDetail
from django.db.models import Avg


# offerSerializer_logic.py
def calculate_min_price(offer):
    """Berechnet den minimalen Preis für ein Angebot."""
    min_price = offer.details.aggregate(min_price=Min("variant_price"))["min_price"]
    return float(Decimal(min_price).quantize(Decimal("0.00"))) if min_price else None

def calculate_min_delivery_time(offer):
    """Berechnet die minimale Lieferzeit für ein Angebot."""
    return offer.details.aggregate(min_delivery_time=Min("delivery_time_in_days"))["min_delivery_time"]

def extract_user_details(obj):
    """Extrahiert die Benutzerdetails für das Angebot."""
    user = obj.user
    return {
        "first_name": user.first_name,
        "last_name": user.last_name,
        "username": user.username,
    }

def create_offer_details(offer, details_data):
    """Erstellt die OfferDetails für ein Angebot."""
    from coder_app.models import OfferDetail
    if not details_data:
        raise ValueError("Details data cannot be empty.")
    
    for detail_data in details_data:
        required_fields = ["title", "price", "revisions", "delivery_time_in_days", "features", "offer_type"]
        for field in required_fields:
            if field not in detail_data:
                raise ValueError(f"Missing required field: {field}")
        
        OfferDetail.objects.create(
            offer=offer,
            variant_title=detail_data["title"],
            variant_price=detail_data["price"],
            revision_limit=detail_data["revisions"],
            delivery_time_in_days=detail_data["delivery_time_in_days"],
            features=detail_data["features"],
            offer_type=detail_data["offer_type"],
        )


def update_main_instance(instance, validated_data):
    """Aktualisiert die Hauptinstanz eines Angebots."""
    image = validated_data.pop("image", None)
    for attr, value in validated_data.items():
        if hasattr(instance, attr):
            setattr(instance, attr, value)
    if image:
        instance.image = image
    instance.save()


def update_offer_details(instance, details_data):
    """Aktualisiert die OfferDetails eines Angebots."""
    from coder_app.models import OfferDetail

    if not details_data:
        return

    existing_details = {detail.offer_type: detail for detail in instance.details.all()}
    updated_offer_types = set()

    for detail_data in details_data:
        offer_type = detail_data.get("offer_type")
        if offer_type in existing_details:
            detail_instance = existing_details[offer_type]
            for attr, value in detail_data.items():
                setattr(detail_instance, attr, value)
            detail_instance.save()
            updated_offer_types.add(offer_type)
        else:
            OfferDetail.objects.create(
                offer=instance,
                variant_title=detail_data["title"],
                variant_price=detail_data["price"],
                revision_limit=detail_data["revisions"],
                delivery_time_in_days=detail_data["delivery_time_in_days"],
                features=detail_data["features"],
                offer_type=offer_type,
            )
            updated_offer_types.add(offer_type)

    for offer_type, detail_instance in existing_details.items():
        if offer_type not in updated_offer_types:
            detail_instance.delete()
# End of offerSerializers_logic.py



# businessProfilSerializer_logic.py
def calculate_avg_rating(obj):
    avg = Review.objects.filter(business_user=obj.user).aggregate(Avg("rating"))[
        "rating__avg"
    ]
    return round(avg, 1) if avg else "-"

def count_pending_orders(obj):
    return Order.objects.filter(
        business_user=obj.user, status__in=["in_progress"]
    ).count()

def update_instance_fields(instance, validated_data):
    fields_to_update = [
        "company_name",
        "company_address",
        "description",
        "tel",
        "location",
        "working_hours",
    ]
    for field in fields_to_update:
        setattr(instance, field, validated_data.get(field, getattr(instance, field)))
    if "file" in validated_data:
        instance.file = validated_data["file"]
    instance.save()

def update_user_email(instance, user_data):
    if "email" in user_data:
        instance.user.email = user_data["email"]
        instance.user.save()
# End of businessProfilSerializer_logic.py



# orderSerializer_logic.py
def map_status_to_display(status):
    """
    Maps the order status to a user-friendly display name.
    """
    status_mapping = {
        "pending": "Pending",
        "in_progress": "In Progress",
        "completed": "Completed",
        "cancelled": "Cancelled",
    }
    return status_mapping.get(status, "Unknown Status")

def validate_order_data(user, data):
    """
    Validates the data to ensure only customers can create orders
    and that the provided OfferDetail is valid.
    """
    if hasattr(user, "business_profile"):
        raise serializers.ValidationError("Business profiles cannot create orders.")

    offer_detail = data.get("offer_detail")
    if not offer_detail:
        raise serializers.ValidationError("OfferDetail is required to create an order.")

    if not OfferDetail.objects.filter(id=offer_detail.id).exists():
        raise serializers.ValidationError("The specified OfferDetail does not exist.")

    data["customer_user"] = user
    return data


def create_order_with_details(validated_data):
    """
    Creates a new order with the validated data.
    """
    offer_detail = validated_data.get("offer_detail")
    validated_data["offer"] = offer_detail.offer
    validated_data["features"] = offer_detail.features or []
    validated_data["business_user"] = offer_detail.offer.user
    return Order.objects.create(**validated_data)


def update_order_instance(instance, validated_data):
    """
    Updates the order instance with the provided validated data.
    """
    for field, value in validated_data.items():
        setattr(instance, field, value)
    instance.save()
    return instance
# End of orderSerializer_logic.py