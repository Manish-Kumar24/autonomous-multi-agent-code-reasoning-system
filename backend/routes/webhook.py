from fastapi import APIRouter, Request, Header, HTTPException
import os, json

from services.github_auth import generate_installation_token
from utils.security import verify_signature

router = APIRouter()

@router.post("/github-webhook")
async def github_webhook(
    request: Request,
    x_github_event: str = Header(None),
    x_hub_signature_256: str = Header(None)
):
    body = await request.body()

    # ✅ Verify Signature
    if not verify_signature(body, x_hub_signature_256):
        raise HTTPException(status_code=403, detail="Invalid signature")

    payload = json.loads(body)

    # ✅ Only handle pull_request events
    if x_github_event == "pull_request":
        action = payload.get("action")

        if action in ["opened", "reopened", "synchronize"]:
            installation_id = payload["installation"]["id"]
            repo = payload["repository"]["full_name"]
            pr_number = payload["pull_request"]["number"]

            print(f"PR Event Received for {repo} PR #{pr_number}")

            # ✅ Generate installation token
            token = generate_installation_token(installation_id)

            # 🔥 Later we connect risk engine here

            return {"status": "PR event processed"}

    return {"status": "ignored"}