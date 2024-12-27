from django.db import models
from django.contrib.auth.models import User

class Offer(models.Model):
    # Represents an offer with details such as title, description, price, and delivery time.
    title = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_time_in_days = models.IntegerField(null=True, blank=True)
    image = models.ImageField(upload_to='offer_images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="offers")

    def min_price(self):
        # Returns the price of the offer.
        return self.price

    def min_delivery_time(self):
        # Returns the delivery time of the offer in days.
        return self.delivery_time_in_days

    def __str__(self):
        # Returns the string representation of the offer.
        return self.title

class Review(models.Model):
    # Represents a review for a specific offer or business user.
    rating = models.IntegerField()
    description = models.TextField()
    business_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='business_reviews'
    )
    reviewer = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='reviews_given'
    )
    offer = models.ForeignKey(
        Offer, on_delete=models.CASCADE, related_name='offer_reviews', default=1
    ) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Orders reviews by creation date in descending order.
        ordering = ['-created_at']

    def __str__(self):
        # Returns a string representation of the review, including reviewer and business user.
        return f'Review by {self.reviewer} for (Business: {self.business_user}, Offer: {self.offer})'

class OfferDetail(models.Model):
    # Represents additional details for an offer variant.
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name="details")
    variant_title = models.CharField(max_length=255)
    variant_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    delivery_time_in_days = models.IntegerField(null=True, blank=True)
    revision_limit = models.IntegerField(null=True, blank=True)
    additional_details = models.TextField(null=True, blank=True)
    offer_type = models.CharField(max_length=50, choices=[('basic', 'Basic'), ('standard', 'Standard'), ('premium', 'Premium')], null=True, blank=True)
    features = models.JSONField(default=list)
    

    def __str__(self):
        # Returns the string representation of the offer detail.
        return f"{self.offer_type} - {self.variant_title}"

class BusinessProfile(models.Model):
    # Represents a business profile associated with a user.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='business_profile')
    company_name = models.CharField(max_length=255)
    company_address = models.TextField()
    #company_website = models.URLField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    tel = models.CharField(max_length=20, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    working_hours = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    profile_image = models.ImageField(upload_to='profile_images/', blank=True, null=True)

    def __str__(self):
        # Returns the company name as the string representation.
        return self.company_name

class CustomerProfile(models.Model):
    # Represents a customer profile associated with a user.
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='customer_profile')
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.ImageField(upload_to='profile_images/', null=True, blank=True)

    def __str__(self):
        # Returns the full name of the customer.
        return f"{self.first_name} {self.last_name}"

class Order(models.Model):
    # Represents an order placed by a customer for an offer.
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_orders')
    business_user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='business_orders',
        null=True,
        blank=True
    )
    offer = models.ForeignKey("Offer", on_delete=models.CASCADE, related_name='orders')
    offer_detail_id = models.ForeignKey(OfferDetail, on_delete=models.CASCADE, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    option = models.CharField(max_length=20, choices=[('basic', 'Basic'), ('standard', 'Standard'), ('premium', 'Premium')], default='basic')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    features = models.JSONField(default=list, blank=True)

    def save(self, *args, **kwargs):
        # Sets default values for business_user and features before saving the order.
        self.set_business_user_if_missing()
        self.set_features_from_offer_detail_if_missing()
        super().save(*args, **kwargs)

    def set_business_user_if_missing(self):
        # Assigns the business user from the offer if not already set.
        if not self.business_user and self.offer:
        #if self.offer and not self.business_user:
            self.business_user = self.offer.user

    def set_features_from_offer_detail_if_missing(self):
        # Assigns features from the offer detail if not already set.
        if self.offer_detail_id and not self.features:
            self.features = self.offer_detail_id.features or []
