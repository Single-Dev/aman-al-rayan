import hashlib
import hmac
from typing import Dict, Optional
from urllib.parse import parse_qs, unquote


def validate_init_data(init_data: str, bot_token: str) -> Optional[Dict]:
    """
    Validate Telegram WebApp initData signature.

    The initData is an HMAC-SHA256 signed string containing user data.
    This function verifies the signature using the bot token.

    Args:
        init_data: The WebApp initData string from Telegram
        bot_token: Bot token (used to derive the secret key)

    Returns:
        Dictionary with decoded user data if valid, None if invalid
    """
    try:
        # Parse the query string
        params = parse_qs(init_data)

        # Extract hash (it's a single value, not a list)
        if 'hash' not in params:
            return None

        hash_value = params['hash'][0]

        # Remove hash from params for verification
        params_copy = {k: v[0] if isinstance(v, list) and len(v) == 1 else v for k, v in params.items()}
        params_copy.pop('hash', None)

        # Sort parameters and create string for verification
        sorted_params = sorted(params_copy.items())
        data_check_string = '\n'.join(f"{k}={v}" for k, v in sorted_params)

        # Generate secret key from bot token
        secret_key = hashlib.sha256(bot_token.encode()).digest()

        # Compute HMAC-SHA256
        computed_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()

        # Verify hash
        if not hmac.compare_digest(computed_hash, hash_value):
            return None

        # Return validated data
        return params_copy

    except Exception as e:
        print(f"Error validating initData: {e}")
        return None


def parse_user_data(params: Dict) -> Optional[Dict]:
    """
    Parse user data from initData parameters.

    Args:
        params: Parsed init_data parameters

    Returns:
        Dictionary with user info (id, first_name, last_name, username)
    """
    try:
        import json

        if 'user' not in params:
            return None

        user_json = params.get('user', [{}])
        if isinstance(user_json, list):
            user_json = user_json[0]

        user_data = json.loads(unquote(user_json)) if isinstance(user_json, str) else user_json

        return {
            'id': user_data.get('id'),
            'first_name': user_data.get('first_name'),
            'last_name': user_data.get('last_name'),
            'username': user_data.get('username'),
            'language_code': user_data.get('language_code'),
            'is_premium': user_data.get('is_premium', False),
        }

    except Exception as e:
        print(f"Error parsing user data: {e}")
        return None
