import hashlib
import hmac
from typing import Dict, Tuple
from urllib.parse import parse_qsl


def _build_data_check_string(init_data: str) -> Tuple[str, Dict[str, str], str]:
    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", "")
    pairs = [f"{k}={v}" for k, v in sorted(data.items())]
    data_check_string = "\n".join(pairs)
    return received_hash, data, data_check_string


def validate_init_data(init_data: str, bot_token: str) -> Dict[str, str]:
    if not init_data:
        raise ValueError("initData is empty")

    received_hash, data, data_check_string = _build_data_check_string(init_data)
    secret_key = hashlib.sha256(bot_token.encode()).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, received_hash):
        raise ValueError(
            "initData hash mismatch (recv=%s calc=%s)"
            % (received_hash[:8] if received_hash else "", calc_hash[:8])
        )

    return data
