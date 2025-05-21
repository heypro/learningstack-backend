# api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('click/', views.click),
    path('leaderboard/', views.leaderboard),
]
