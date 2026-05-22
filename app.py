import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="ProspectKit")
templates = Jinja2Templates(directory="templates")

APOLLO_BASE = "https://api.apollo.io/v1"


def get_api_key(request: Request) -> str:
    """
    API key resolution order:
    1. X-Apollo-Key header (sent by the browser UI — user entered it in settings)
    2. APOLLO_API_KEY env var (set by team admin for shared deployments)
    """
    key = request.headers.get("X-Apollo-Key") or os.getenv("APOLLO_API_KEY", "")
    if not key:
        raise HTTPException(
            status_code=401,
            detail="No Apollo API key found. Enter your key in Settings (top right)."
        )
    return key


class EnrichRequest(BaseModel):
    linkedin_url: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_name: Optional[str] = None
    email: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # Tell the frontend whether a server-side key is configured
    has_server_key = bool(os.getenv("APOLLO_API_KEY", ""))
    return templates.TemplateResponse("index.html", {
        "request": request,
        "has_server_key": has_server_key,
    })


@app.post("/enrich")
async def enrich_contact(payload: EnrichRequest, request: Request):
    api_key = get_api_key(request)

    if not payload.linkedin_url and not (payload.first_name and payload.last_name):
        raise HTTPException(
            status_code=400,
            detail="Provide a LinkedIn URL or at least first name + last name.",
        )

    body = {"reveal_personal_emails": True}
    if payload.linkedin_url:
        body["linkedin_url"] = payload.linkedin_url.strip()
    if payload.first_name:
        body["first_name"] = payload.first_name.strip()
    if payload.last_name:
        body["last_name"] = payload.last_name.strip()
    if payload.organization_name:
        body["organization_name"] = payload.organization_name.strip()
    if payload.email:
        body["email"] = payload.email.strip()

    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.post(f"{APOLLO_BASE}/people/match", json=body, headers=headers)

    if resp.status_code == 401:
        raise HTTPException(status_code=401, detail="Invalid Apollo API key. Check your key in Settings.")
    if resp.status_code == 429:
        raise HTTPException(status_code=429, detail="Apollo rate limit hit. Try again shortly.")
    if resp.status_code != 200:
        raise HTTPException(status_code=resp.status_code, detail=f"Apollo error: {resp.text}")

    data = resp.json()
    person = data.get("person")

    if not person:
        return JSONResponse({"found": False, "message": "No contact found. Try adding a company name."})

    phones = person.get("phone_numbers") or []
    mobile = next((p for p in phones if p.get("type") == "mobile"), None)
    any_phone = mobile or (phones[0] if phones else None)

    email_status = (person.get("email_status") or "unknown").lower()
    if email_status == "verified":
        email_confidence, email_label = "high", "Verified"
    elif email_status in ("likely to engage", "guessed"):
        email_confidence, email_label = "medium", "Likely Valid"
    elif email_status == "unavailable":
        email_confidence, email_label = "none", "Not Found"
    else:
        email_confidence, email_label = "medium", email_status.title()

    emails = []
    if person.get("email"):
        emails.append({"address": person["email"], "type": "work", "status": email_status})
    for e in person.get("personal_emails") or []:
        emails.append({"address": e, "type": "personal", "status": "unknown"})

    location = person.get("city", "")
    if person.get("state"):
        location += f", {person['state']}"
    if person.get("country"):
        location += f", {person['country']}"

    return JSONResponse({
        "found": True,
        "name": person.get("name", ""),
        "title": person.get("title", ""),
        "company": (person.get("organization") or {}).get("name", ""),
        "linkedin_url": person.get("linkedin_url", ""),
        "location": location.strip(", "),
        "emails": emails,
        "email_confidence": email_confidence,
        "email_label": email_label,
        "phone": any_phone.get("sanitized_number") if any_phone else None,
        "phone_type": any_phone.get("type", "").replace("_", " ").title() if any_phone else None,
        "photo_url": person.get("photo_url", ""),
    })


@app.post("/bulk-enrich")
async def bulk_enrich(request: Request):
    api_key = get_api_key(request)
    body = await request.json()
    urls = [u.strip() for u in (body.get("urls") or "").splitlines() if u.strip()]

    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided.")
    if len(urls) > 20:
        raise HTTPException(status_code=400, detail="Max 20 URLs per bulk run.")

    headers = {"X-Api-Key": api_key, "Content-Type": "application/json"}
    results = []
    async with httpx.AsyncClient(timeout=20) as client:
        for url in urls:
            try:
                resp = await client.post(
                    f"{APOLLO_BASE}/people/match",
                    json={"linkedin_url": url, "reveal_personal_emails": True},
                    headers=headers,
                )
                person = resp.json().get("person") if resp.status_code == 200 else None
                if person:
                    phones = person.get("phone_numbers") or []
                    mobile = next((p for p in phones if p.get("type") == "mobile"), phones[0] if phones else None)
                    results.append({
                        "url": url,
                        "name": person.get("name", ""),
                        "title": person.get("title", ""),
                        "company": (person.get("organization") or {}).get("name", ""),
                        "email": person.get("email", ""),
                        "email_status": person.get("email_status", ""),
                        "phone": mobile.get("sanitized_number", "") if mobile else "",
                    })
                else:
                    results.append({"url": url, "name": "", "title": "", "company": "",
                                    "email": "", "email_status": "not found", "phone": ""})
            except Exception as e:
                results.append({"url": url, "error": str(e)})

    return JSONResponse({"results": results})
