from rest_framework import serializers
from .models import TelegramUser

class LeaderboardRowSerializer(serializers.ModelSerializer):
    class Meta:
        model  = TelegramUser
        fields = ('user_id', 'username', 'first_name', 'score')
