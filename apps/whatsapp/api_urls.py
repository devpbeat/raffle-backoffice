from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.whatsapp import api_views

router = DefaultRouter()
router.register(r'contacts', api_views.WhatsAppContactViewSet, basename='whatsapp-contact')

urlpatterns = [
    path('', include(router.urls)),
]
