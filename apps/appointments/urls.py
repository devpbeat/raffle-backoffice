from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.appointments import api_views

app_name = 'appointments'

router = DefaultRouter()
router.register(r'services', api_views.ServiceViewSet, basename='service')
router.register(r'customers', api_views.CustomerViewSet, basename='customer')
router.register(r'appointments', api_views.AppointmentViewSet, basename='appointment')

urlpatterns = [
    path('', include(router.urls)),
]
