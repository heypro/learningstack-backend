# telegram_auth/views.py
import hmac
import hashlib
import time
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json
from urllib.parse import parse_qs

# Your Telegram bot token here
BOT_TOKEN = '1234567890:ABC'

def check_signature(data: dict, token: str) -> bool:
    # Sort keys, create data check string
    data_check_arr = [f"{k}={v}" for k, v in sorted(data.items()) if k != 'hash']
    data_check_string = '\n'.join(data_check_arr)
    secret_key = hashlib.sha256(token.encode()).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
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
