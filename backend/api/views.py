# api/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.db.models import F
from .models import TelegramUser
from .serializers import LeaderboardRowSerializer
from .utils import telegram_auth as parse_init_data

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
    except ValueError as err:
        return Response({"detail": str(err)}, status=status.HTTP_400_BAD_REQUEST)

    user, _ = TelegramUser.objects.get_or_create(
        user_id   = payload["user"],
        defaults  = {
            "first_name": payload.get("first_name", ""),
            "username"  : payload.get("username", "")
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
