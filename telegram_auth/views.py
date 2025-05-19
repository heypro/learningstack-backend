# telegram_auth/views.py
import hmac
import hashlib
import time
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from urllib.parse import parse_qs
import os

# Your Telegram bot token here
BOT_TOKEN = os.getenv("BOT_TOKEN")

# testing csrf bullshit
@csrf_exempt
def test_view(request):
    if request.method == 'POST':
        return JsonResponse({"message": "Hit test view successfully"})
    return JsonResponse({"error": "Only POST allowed"}, status=405)

def check_signature(data: dict, token: str) -> bool:
    data_check_arr = [f"{k}={v}" for k, v in sorted(data.items()) if k != 'hash']
    data_check_string = '\n'.join(data_check_arr)
    secret_key = hashlib.sha256(token.encode('utf-8')).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    print(BOT_TOKEN)
    print("Data check string:", data_check_string)
    print("Calculated hash:", hmac_hash)
    print("Received hash:", data.get('hash'))
    return hmac_hash == data.get('hash')


def is_fresh(auth_date: int) -> bool:
    return (time.time() - auth_date) < 3600  # 1 hour validity

@csrf_exempt
@require_POST
def telegram_auth(request):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('tma '):
        return HttpResponseForbidden('Unauthorized')

    raw_init_data = auth_header[4:]
    # raw_init_data is URL query-like, parse it
    data = parse_qs(raw_init_data)
    # parse_qs gives list values, flatten to single value for each key
    data = {k: v[0] for k, v in data.items()}

    if not check_signature(data, BOT_TOKEN):
        return HttpResponseForbidden('Invalid signature')

    auth_date = int(data.get('auth_date', 0))
    if not is_fresh(auth_date):
        return HttpResponseForbidden('Init data expired')

    # Authorized, return user data as JSON (minus hash)
    user_data = {k: v for k, v in data.items() if k != 'hash'}
    return JsonResponse(user_data)
