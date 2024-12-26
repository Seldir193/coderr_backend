from django.urls import path
from coder_app import views

urlpatterns = [
    path('registration/', views.RegistrationView.as_view(), name='registration'),  
    path('login/', views.LoginView.as_view(), name='login'),  
    path('profiles/business/<int:user_id>/', views.BusinessProfileView.as_view(), name='business-profile'),
    path('profile/<int:user_id>/', views.ProfileView.as_view(), name='profile'),  
    path('profiles/business/', views.BusinessProfileListView.as_view(), name='business-profiles'),  
    path('profiles/customer/', views.CustomerProfileListView.as_view(), name='customer-profiles'),  
    path('profiles/customer/<int:user_id>/', views.CustomerProfileView.as_view(), name='customer-profile'),  
    path('reviews/', views.ReviewListView.as_view(), name='reviews'),  
    path('reviews/<int:pk>/', views.ReviewDetailView.as_view(), name='review-detail'),
    path('orders/', views.OrderListView.as_view(), name='order-list'),  
    path('orders/<int:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),  
    path('order-count/<int:offer_id>/', views.OrderInProgressCountView.as_view(), name='order-count'),
    path('offers/', views.OfferListView.as_view(), name='offers'),  
    path('offers/<int:id>/', views.OfferDetailView.as_view(), name='offer-detail'),  
    path('base-info/', views.BaseInfoView.as_view(), name='base-info'),  
    path('completed-order-count/<int:user_id>/', views.OrderCompletedCountView.as_view(), name='completed-order-count'),  
]







