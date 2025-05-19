import hmac
import hashlib
import time
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from urllib.parse import parse_qs
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")  # Set your bot token in env

def check_signature(data: dict, token: str) -> bool:
    data_check_arr = [f"{k}={v}" for k, v in sorted(data.items()) if k != 'hash']
    data_check_string = '\n'.join(data_check_arr)
    secret_key = hashlib.sha256(token.encode('utf-8')).digest()
    hmac_hash = hmac.new(secret_key, data_check_string.encode('utf-8'), hashlib.sha256).hexdigest()
    return hmac_hash == data.get('hash')

def is_fresh(auth_date: int) -> bool:
    return (time.time() - auth_date) < 3600  # 1 hour validity

@csrf_exempt
@require_POST
def telegram_auth(request):
    print("HIT!")
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('tma '):
        return JsonResponse({'error': 'Missing or malformed Authorization header'}, status=401)

    print("Authorized!")
    raw_init_data = auth_header[4:].strip()
    print(raw_init_data)
    data = parse_qs(raw_init_data)
    data = {k: v[0] for k, v in data.items()}

    if not check_signature(data, BOT_TOKEN):
        print ("kys0")
        return JsonResponse({'error': data}, status=403)
    auth_date = int(data.get('auth_date', 0))
    if not is_fresh(auth_date):
        return JsonResponse({'error': 'Init data expired'}, status=403)

    user_data = {k: v for k, v in data.items() if k != 'hash'}
    return JsonResponse(user_data)
