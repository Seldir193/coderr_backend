from django.db import models
from django.contrib.auth.models import User
from utils.utils import set_order_defaults


class Offer(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_time_in_days = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to="offer_images/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name="offers"
    )
    
    class Meta:
        ordering = ["-updated_at"]

    def min_price(self):
        return self.price

    def min_delivery_time(self):
        return self.delivery_time_in_days

    def __str__(self):
        return self.title


class OfferDetail(models.Model):
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="details")
    variant_title = models.CharField(max_length=255)
    variant_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    delivery_time_in_days = models.IntegerField(null=True, blank=True)
    revision_limit = models.IntegerField(null=True, blank=True)
    offer_type = models.CharField(
        max_length=50,
        choices=[("basic", "Basic"), ("standard", "Standard"), ("premium", "Premium")],
        null=True,
        blank=True,
    )
    features = models.JSONField(default=list)

    def __str__(self):
        return f"{self.offer_type} - {self.variant_title}"


class Review(models.Model):
    rating = models.IntegerField()
    description = models.TextField()
    business_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="business_reviews"
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="reviews_given"
    )
    offer = models.ForeignKey(
        Offer,
        on_delete=models.CASCADE,
        related_name="offer_reviews",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Review by {self.reviewer} for (Business: {self.business_user}, Offer: {self.offer})"


class BusinessProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="business_profile"
    )
    company_name = models.CharField(max_length=255)
    company_address = models.TextField()
    description = models.TextField(blank=True, null=True)
    tel = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    working_hours = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.ImageField(upload_to="profile_images/", null=True, blank=True)

    def __str__(self):
        return self.company_name


class CustomerProfile(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="customer_profile"
    )
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.ImageField(upload_to="profile_images/", null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    OPTION_CHOICES = [
        ("basic", "Basic"),
        ("standard", "Standard"),
        ("premium", "Premium"),
    ]

    customer_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="customer_orders", default=1
    )

    business_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="business_orders",
        null=True,
        blank=True,
    )

    offer = models.ForeignKey("Offer", on_delete=models.CASCADE, related_name="orders")
    offer_detail = models.ForeignKey(
        "OfferDetail",
        on_delete=models.CASCADE,
        related_name="order_details",
        null=True,
        blank=True,
    )

    title = models.CharField(max_length=255, blank=True)
    revisions = models.IntegerField(default=0)
    delivery_time_in_days = models.IntegerField(default=7)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    features = models.JSONField(default=list, blank=True)
    offer_type = models.CharField(
        max_length=50,
        choices=[("basic", "Basic"), ("standard", "Standard"), ("premium", "Premium")],
        default="basic",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        """
        Override save method to set default values before saving.
        """
        set_order_defaults(self)
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"Order {self.id} - {self.title}"
