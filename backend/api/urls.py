from django.urls import path
from .views import telegram_auth

urlpatterns = [
    path('api/auth/', telegram_auth),
]
