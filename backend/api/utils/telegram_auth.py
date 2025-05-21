import hmac
import hashlib
import urllib.parse
import time
from django.conf import settings

BOT_TOKEN = settings.TELEGRAM_BOT_TOKEN
if not BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment")

# secret key = HMAC_SHA256(bot_token, "WebAppData")
_SECRET_KEY = hmac.new(
    key=b"WebAppData",
    msg=BOT_TOKEN.encode(),
    digestmod=hashlib.sha256
).digest()

def _make_data_check_string(params: dict) -> str:
    """
    Sort keys alphabetically, join as key=value with '\n' per Telegram spec.
    Don't include 'hash' itself.
    """
    pairs = [f"{k}={params[k]}" for k in sorted(params.keys()) if k != "hash"]
    return "\n".join(pairs)

def verify_init_data(raw_query_string: str, max_age_seconds: int = 24 * 3600) -> dict:
    """
    Return the parsed dict if valid, else raise ValueError.
    """
    parsed = dict(urllib.parse.parse_qsl(raw_query_string, keep_blank_values=True))
    given_hash = parsed.get("hash")
    if not given_hash:
        raise ValueError("hash param missing")

    # build the data-check-string and compute our own hash
    data_check_string = _make_data_check_string(parsed)
    calculated_hash = hmac.new(
        key=_SECRET_KEY,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, given_hash):
        raise ValueError("initData hash mismatch – possible forgery")  # :contentReference[oaicite:0]{index=0}

    # freshness check (optional but recommended)
    auth_date = int(parsed.get("auth_date", "0"))
    if abs(time.time() - auth_date) > max_age_seconds:
        raise ValueError("initData too old")

    return parsed
