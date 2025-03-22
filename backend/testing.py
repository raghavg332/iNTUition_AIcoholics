from fastapi import FastAPI, Request, Header

app = FastAPI()

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
