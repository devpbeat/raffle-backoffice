from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.raffles import api_views

app_name = 'raffles'

router = DefaultRouter()
router.register(r'raffles', api_views.RaffleViewSet, basename='raffle')
router.register(r'orders', api_views.OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
]
