import base64
import hashlib
import hmac
import json
import os
import secrets
import time


SESSION_COOKIE = "creator_os_session"

SESSION_TTL_SECONDS = 60 * 60 * 12

DEFAULT_WORKSPACE_ID = "default_workspace"
DEFAULT_CREATOR_ID = "default_creator"


def get_secret():

    secret = os.getenv(
        "CREATOR_OS_AUTH_SECRET"
    )

    if not secret:
        raise RuntimeError(
            "CREATOR_OS_AUTH_SECRET is not configured"
        )

    return secret.encode("utf-8")


def get_admin_credentials():

    email = os.getenv(
        "CREATOR_OS_ADMIN_EMAIL"
    )

    password = os.getenv(
        "CREATOR_OS_ADMIN_PASSWORD"
    )

    if not email or not password:

        raise RuntimeError(
            "CREATOR_OS_ADMIN_EMAIL and "
            "CREATOR_OS_ADMIN_PASSWORD "
            "must be configured"
        )

    return (
        email.strip().lower(),
        password,
    )


def encode_payload(payload):

    raw = json.dumps(
        payload,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")

    return base64.urlsafe_b64encode(
        raw
    ).decode("utf-8").rstrip("=")


def decode_payload(value):

    padding = "=" * (-len(value) % 4)

    return json.loads(
        base64.urlsafe_b64decode(
            value + padding
        ).decode("utf-8")
    )


def create_session(email):

    payload = {

        "email":
            email.lower(),

        "workspace_id":
            DEFAULT_WORKSPACE_ID,

        "creator_id":
            DEFAULT_CREATOR_ID,

        "exp":
            int(time.time())
            + SESSION_TTL_SECONDS,

        "nonce":
            secrets.token_urlsafe(12),
    }

    encoded = encode_payload(
        payload
    )

    signature = hmac.new(
        get_secret(),
        encoded.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return (
        f"{encoded}.{signature}"
    )


def verify_session(token):

    if not token or "." not in token:
        return None

    encoded, signature = token.rsplit(
        ".",
        1,
    )

    expected = hmac.new(
        get_secret(),
        encoded.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(
        signature,
        expected,
    ):
        return None

    try:

        payload = decode_payload(
            encoded
        )

    except Exception:

        return None

    if payload.get("exp", 0) < int(
        time.time()
    ):
        return None

    return payload


def authenticate(
    email,
    password,
):

    admin_email, admin_password = (
        get_admin_credentials()
    )

    if not hmac.compare_digest(
        email.strip().lower(),
        admin_email,
    ):
        return None

    if not hmac.compare_digest(
        password,
        admin_password,
    ):
        return None

    return {

        "email":
            admin_email,

        "workspace_id":
            DEFAULT_WORKSPACE_ID,

        "creator_id":
            DEFAULT_CREATOR_ID,
    }
