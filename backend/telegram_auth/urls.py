# telegram_auth/urls.py
from django.urls import path
from .views import telegram_auth, test_view

urlpatterns = [
    path('api/auth/', telegram_auth, name='telegram_auth'),
    path('api/test/', test_view, name='test_view'),
]
