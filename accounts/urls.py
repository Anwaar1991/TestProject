from django.urls import path
from .views import *
from rest_framework_simplejwt.views import TokenRefreshView
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('register/', SignupAPIView.as_view(), name='user-register'),
    path('verify-otp/', VerifyOTPAPIView.as_view(), name='verify-otp'),
    path('resend-otp/', ResendOTPAPIView.as_view(), name='resend-otp'),
    path('login/', LoginView.as_view(), name='login'),
    path('list-users/', ListUsers.as_view(), name='list-users'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

# USER PROFILE - EDIT PROFILE - VIEW BOOKS - VIEW LIKES ENDPOINTS
    path('profile/', MyProfileView.as_view(), name='my-profile'),
    path('profile/edit/', EditProfileView.as_view(), name='edit-profile'),
    path('profile/book/<int:book_id>/', UserBookDetailView.as_view(), name='user-book-detail'),

]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)