from django.urls import path
from .views import generate_trip, health_check


urlpatterns = [
    path('api/trip/', generate_trip, name='generate_trip'),
    path('health/', health_check, name='health_check'),

]
