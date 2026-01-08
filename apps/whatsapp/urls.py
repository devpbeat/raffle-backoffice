from django.urls import path
from apps.whatsapp import views

app_name = 'whatsapp'

urlpatterns = [
    path('webhook/', views.webhook_receive, name='webhook_receive'),
    path('webhook/verify/', views.webhook_verify, name='webhook_verify'),
]
