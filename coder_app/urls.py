from django.urls import path
from coder_app import views

urlpatterns = [
    path('registration/', views.RegistrationView.as_view(), name='registration'),  
    path('login/', views.LoginView.as_view(), name='login'),  
    
    path('profiles/business/<int:pk>/', views.BusinessProfileView.as_view(), name='business-profile'),
    path('profile/<int:pk>/', views.ProfileView.as_view(), name='profile-detail'),
    path('profiles/business/', views.BusinessProfileListView.as_view(), name='business-profiles'),
    path('profiles/customer/', views.CustomerProfileListView.as_view(), name='customer-profiles'),
    path('profiles/customer/<int:pk>/', views.CustomerProfileView.as_view(), name='customer-profile'),
    
    path('reviews/', views.ReviewListCreateView.as_view(), name='review-list-create'),
    path('reviews/<int:id>/', views.ReviewDetailView.as_view(), name='review-detail'),
    
    path('orders/', views.OrderListView.as_view(), name='order-list'),  
    path('orders/<int:order_id>/', views.OrderDetailView.as_view(), name='order-detail'),  
   
    path('order-count/<int:business_user_id>/', views.OrderCountView.as_view(), name='order-count'),
    path('completed-order-count/<int:business_user_id>/', views.CompletedOrderCountView.as_view(), name='completed-order-count'),

    path('offers/<int:id>/', views.OfferDetailView.as_view(), name='offer-detail'),
    path('offerdetails/<int:id>/', views.OfferDetailRetrieveView.as_view(), name='offer-detail-retrieve'),
    path('offers/', views.OfferListView.as_view(), name='offers'),  
  
    path('base-info/', views.BaseInfoView.as_view(), name='base-info'),  
]







