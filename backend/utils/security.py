import os, hmac, hashlib

def verify_signature(payload_body: bytes, signature_header: str):
    if not signature_header:
        return False

    secret = os.getenv("GITHUB_WEBHOOK_SECRET")
    if not secret:
        return False

    try:
        sha_name, signature = signature_header.split("=")
    except ValueError:
        return False

    if sha_name != "sha256":
        return False

    mac = hmac.new(
        secret.encode(),
        msg=payload_body,
        digestmod=hashlib.sha256
    )

    return hmac.compare_digest(mac.hexdigest(), signature)