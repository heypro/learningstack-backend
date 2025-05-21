from django.urls import path
from .views import TelegramAuthView  # import your auth view from api/views.py

urlpatterns = [
    path("telegram-auth/", TelegramAuthView.as_view()),
]
