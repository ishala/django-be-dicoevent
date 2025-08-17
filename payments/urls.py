from django.urls import path
from .views import (
    PaymentListCreateView, PaymentDetailView,
    RegistrationListCreateView, RegistrationDetailView
)

urlpatterns = [
    # Payment endpoints
    path('payments/', PaymentListCreateView.as_view(), name='payment-list'),
    path('payments/<uuid:pk>/', PaymentDetailView.as_view(), name='payment-detail'),

    # Registration endpoints
    path('registrations/', RegistrationListCreateView.as_view(), name='registration-list'),
    path('registrations/<uuid:pk>/', RegistrationDetailView.as_view(), name='registration-detail'),
]