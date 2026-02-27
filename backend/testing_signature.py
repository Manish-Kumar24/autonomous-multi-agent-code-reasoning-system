import hmac, hashlib
secret = b"pr_sentinel_super_secret_123"
payload = b'{"action":"opened","pull_request":{"number":5}}'
signature = "sha256=" + hmac.new(secret, payload, hashlib.sha256).hexdigest()
print(signature)