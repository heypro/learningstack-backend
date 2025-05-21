# api/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import F
from backend.api.models import TelegramUser
from .serializers import LeaderboardRowSerializer
from .utils.telegram_auth import verify_init_data as parse_init_data
import json


@api_view(['POST'])
@permission_classes([AllowAny])   # mini-apps can’t send CSRF; keep it open
def click(request):
    """
    Body: { "increment": 1, "initData": "<raw string>" }
    """
    init_data = request.data.get("initData")
    increment = int(request.data.get("increment", 1))

    try:
        payload = parse_init_data(init_data)
        user_field = payload["user"]
        if isinstance(user_field, str) and user_field.startswith("{"):
            user_obj = json.loads(user_field)
            user_id = user_obj.get("id")
            first_name = user_obj.get("first_name", "")
            username = user_obj.get("username", "")
        else:
            user_id = int(user_field)
            first_name = payload.get("first_name", "")
            username = payload.get("username", "")

    except ValueError as err:
        return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

    user, _ = TelegramUser.objects.get_or_create(

        user_id=user_id,

        defaults={
            "first_name": first_name,
            "username": username
        }
    )

    # atomic increment
    TelegramUser.objects.filter(pk=user.pk).update(score=F('score') + increment)
    user.refresh_from_db()

    return Response({"score": user.score})


@api_view(['GET'])
@permission_classes([AllowAny])
def leaderboard(request):
    """
    Return top 50 players ordered by score desc.
    """
    top = TelegramUser.objects.order_by('-score')[:50]
    return Response(LeaderboardRowSerializer(top, many=True).data)
