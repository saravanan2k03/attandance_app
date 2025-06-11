from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from demo import AddEmployeeView
from .views import LogoutView, RegisterView, ForgotPasswordView,LoginView, ResetPasswordView

urlpatterns = [
    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'), 
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('api/login/', LoginView.as_view(), name='login-user'),
    path('api/reset-password/<int:user_id>/', ResetPasswordView.as_view(), name='reset-password'),
    path('api/logout/', LogoutView.as_view(), name='logout'),
    path('add-employee/', AddEmployeeView.as_view(), name='add-employee'),
]
