from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
import json


from .utils.telegram_auth import verify_init_data

User = get_user_model()

class TelegramAuthView(APIView):
    """
    POST { "initData": "<the raw query string>" }
    ->  { "access": "<jwt>", "refresh": "<jwt>", "user": { ... } }
    """
    authentication_classes = []   # public
    permission_classes = []

    def post(self, request):
        raw = request.data.get("initData") or ""
        try:
            payload = verify_init_data(raw)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        tg_user = payload.get("user")
        if not tg_user:
            return Response({"detail": "user field missing"}, status=status.HTTP_400_BAD_REQUEST)

        if isinstance(tg_user, str):
            tg_user = json.loads(tg_user)


        tg_id = tg_user["id"]
        username = tg_user.get("username") or tg_user.get("first_name", "tg_user")

        user, _ = User.objects.get_or_create(
            username=f"tg_{tg_id}",
            defaults={"first_name": tg_user.get("first_name", ""), "last_name": tg_user.get("last_name", "")},
        )

        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "tg_id": tg_id,
                    "username": username,
                },
            }
        )
