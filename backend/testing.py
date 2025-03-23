from fastapi import FastAPI, Request, Header
from prReview import process_pull_request, authenticate_github

app = FastAPI()

def handle_pull_request_event(payload):
    action = payload.get("action")
    pr_number = payload["number"]
    repo = payload["repository"]["full_name"]
    sender = payload["sender"]["login"]
    installation_id = payload["installation"]["id"]

    if action in ["opened", "synchronize", "reopened"]:
        with open("/Users/raghavgupta/Projects/AIcoholics/backend/pulloutrequest.2025-03-22.private-key.pem", "r") as f:
            private_key = f.read()
        g = authenticate_github(app_id=1188098, installation_id=installation_id, private_key=private_key)
        process_pull_request(g, repo, pr_number, sender)
        return {"status": "pull request processed"}
        # print(f"ℹ️ Processing pull request #{pr_number} on {repo} by {sender}")

    return {"status": f"Unhandled pull request action: {action}"}

@app.post("/installation")
async def github_webhook(request: Request, x_github_event: str = Header(None)):
    payload = await request.json()

    if x_github_event == "installation" and payload["action"] == "created":
        installation_id = payload["installation"]["id"]
        org_or_user = payload["installation"]["account"]["login"]
        repos = payload.get("repositories", [])

        print(f"✅ App installed on {org_or_user}, installation_id: {installation_id}")
        for repo in repos:
            print(f"→ {repo['full_name']}")

    elif x_github_event == "pull_request":
        handle_pull_request_event(payload)
    else:
        # Optionally handle or ignore other events
        return {"status": f"Unhandled event type: {x_github_event}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
