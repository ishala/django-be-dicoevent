from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('users/', views.UserListCreateView.as_view(), name='user-list'),
    path('users/<uuid:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('groups/', views.GroupListCreateView.as_view(), name='group-list'),
    path('groups/<int:pk>/', views.GroupDetailView.as_view(), name='group-detail'),
    path('assign-roles/', views.AssignRoleView.as_view(), name='assign-roles'),
    path('login/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('token/', TokenRefreshView.as_view(), name='token-obtain-pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('users/assign-role/', views.AssignRoleView.as_view(), name='assign-user-role')
]