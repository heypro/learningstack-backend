import hmac
import hashlib
import os
import time
import logging
from urllib.parse import parse_qs

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

logger = logging.getLogger(__name__)

BOT_TOKEN: str | None = os.getenv("BOT_TOKEN")          # must be set in env
INIT_DATA_TTL = 3600                                   # seconds (1 h)
DEBUG_ECHO_SECRET = bool(int(os.getenv("DEBUG_BACKEND_ECHO_SECRET", 0)))

def _calc_hash(data: dict[str, str], token: str) -> str:
    """Return Telegram-style HMAC-SHA256 hash for given dict."""
    data_check_arr = [f"{k}={v}" for k, v in sorted(data.items()) if k != "hash"]
    data_check_string = "\n".join(data_check_arr)
    secret_key = hashlib.sha256(token.encode("utf-8")).digest()
    return hmac.new(secret_key, data_check_string.encode("utf-8"), hashlib.sha256).hexdigest()

def _is_fresh(auth_date: int) -> bool:
    """True if auth_date is within INIT_DATA_TTL."""
    return (time.time() - auth_date) < INIT_DATA_TTL

@csrf_exempt
@require_POST
def telegram_auth(request):
    """
    POST /
      headers:
        Authorization: tma <initDataRaw>
    Returns full debug payload no matter what, plus ok/error flag.
    """
    resp: dict[str, object] = {
        "ok": False,
        "raw_init_data": None,
        "parsed_init_data": None,
        "provided_hash": None,
        "calculated_hash": None,
        "hash_match": None,
        "auth_date_fresh": None,
        "error": None,
    }

    # 1. grab raw init data
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("tma "):
        resp["error"] = "Missing or malformed Authorization header"
        return JsonResponse(resp, status=401)

    raw_init_data = auth_header[4:].strip()
    resp["raw_init_data"] = raw_init_data

    # 2. parse query-string into dict[str, str]
    try:
        parsed_qs = {k: v[0] for k, v in parse_qs(raw_init_data, strict_parsing=True).items()}
    except ValueError as exc:
        resp["error"] = f"Query-string parse error: {exc}"
        return JsonResponse(resp, status=400)

    resp["parsed_init_data"] = parsed_qs
    resp["provided_hash"] = parsed_qs.get("hash")

    # 3. verify bot token env
    if not BOT_TOKEN:
        resp["error"] = "BOT_TOKEN not set on server"
        return JsonResponse(resp, status=500)

    # 4. recompute hash & compare
    calc_hash = _calc_hash(parsed_qs, BOT_TOKEN)
    resp["calculated_hash"] = calc_hash
    resp["hash_match"] = calc_hash == parsed_qs.get("hash")
    if not resp["hash_match"]:
        resp["error"] = "Signature mismatch"
        return JsonResponse(resp, status=403)

    # 5. freshness check
    try:
        auth_date = int(parsed_qs.get("auth_date", "0"))
    except ValueError:
        auth_date = 0
    resp["auth_date_fresh"] = _is_fresh(auth_date)
    if not resp["auth_date_fresh"]:
        resp["error"] = "Init data expired"
        return JsonResponse(resp, status=403)

    # 6. success – strip the hash and return user data
    user_data = {k: v for k, v in parsed_qs.items() if k != "hash"}
    resp["ok"] = True
    resp["user_data"] = user_data

    # 7. optionally echo secret key for hardcore debugging (dangerous!)
    if DEBUG_ECHO_SECRET:
        resp["secret_key_hex"] = hashlib.sha256(BOT_TOKEN.encode()).hexdigest()

    return JsonResponse(resp)
