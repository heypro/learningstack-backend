from django.urls import path
from .views import telegram_auth  # import your auth view from api/views.py

urlpatterns = [
    path('auth/', telegram_auth),  # /api/auth/ route
]
