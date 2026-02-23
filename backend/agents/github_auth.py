import os, jwt, time

def generate_app_jwt():
    app_id = os.getenv("GITHUB_APP_ID")
    private_key = os.getenv("GITHUB_PRIVATE_KEY")

    payload = {
        "iat": int(time.time()) - 60,
        "exp": int(time.time()) + (10 * 60),
        "iss": app_id,
    }

    encoded_jwt = jwt.encode(payload, private_key, algorithm="RS256")
    return encoded_jwt