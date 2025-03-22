from fastapi import FastAPI, Request, Header
from fastapi.responses import JSONResponse
import hmac
import hashlib
import json
import os

app = FastAPI()

GITHUB_SECRET = os.getenv("GITHUB_SECRET")  # Set this in your env

def verify_signature(payload, signature, secret):
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha256)
    expected = f"sha256={mac.hexdigest()}"
    return hmac.compare_digest(expected, signature)

@app.post("/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str = Header(None),
    x_github_event: str = Header(None)
):
    body = await request.body()

    # Verify webhook signature
    if not verify_signature(body, x_hub_signature_256, GITHUB_SECRET):
        return JSONResponse(content={"error": "Invalid signature"}, status_code=403)

    payload = json.loads(body)

    if x_github_event == "pull_request":
        action = payload["action"]
        pr = payload["pull_request"]

        if action in ["opened", "synchronize"]:
            pr_url = pr["url"]
            pr_diff_url = pr["diff_url"]
            repo_full_name = payload["repository"]["full_name"]
            # 👇 Call your internal logic to analyze PR
            print(f"Trigger AI review for: {repo_full_name} @ {pr_url}")

    return {"message": "OK"}