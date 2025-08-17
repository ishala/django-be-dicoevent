from django.urls import path
from . import views

urlpatterns = [
    path('events/', views.EventListCreateView.as_view(), name='event-list'),
    path('events/<uuid:pk>/', views.EventDetailView.as_view(), name='event-detail')
]