import os, hmac, hashlib

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET")

def verify_signature(payload_body: bytes, signature_header: str):
    if not signature_header:
        return False

    sha_name, signature = signature_header.split("=")

    if sha_name != "sha256":
        return False

    mac = hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        msg=payload_body,
        digestmod=hashlib.sha256
    )

    return hmac.compare_digest(mac.hexdigest(), signature)