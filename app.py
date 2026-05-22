import os
import json
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List
from dotenv import load_dotenv
from providers import PROVIDERS

load_dotenv()

app = FastAPI(title="ProspectKit")
templates = Jinja2Templates(directory="templates")


def get_provider_keys(request: Request) -> dict:
    """
    Read provider API keys from the X-Provider-Keys header (JSON)
    or fall back to individual env vars per provider.
    """
    header = request.headers.get("X-Provider-Keys", "")
    try:
        keys = json.loads(header) if header else {}
    except Exception:
        keys = {}

    # Merge with env vars (env vars act as fallback / team-wide defaults)
    env_defaults = {
        "apollo": os.getenv("APOLLO_API_KEY", ""),
        "hunter": os.getenv("HUNTER_API_KEY", ""),
        "prospeo": os.getenv("PROSPEO_API_KEY", ""),
    }
    for p, k in env_defaults.items():
        if k and not keys.get(p):
            keys[p] = k

    return keys


def get_ordered_providers(request: Request, keys: dict) -> list:
    """
    Respect the X-Provider-Order header (comma-separated provider names).
    Falls back to the order they were configured.
    """
    order_header = request.headers.get("X-Provider-Order", "")
    if order_header:
        order = [p.strip() for p in order_header.split(",") if p.strip()]
    else:
        order = list(keys.keys())

    return [p for p in order if p in PROVIDERS and keys.get(p)]


class EnrichRequest(BaseModel):
    linkedin_url: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    organization_name: Optional[str] = None
    domain: Optional[str] = None
    email: Optional[str] = None


def server_has_keys() -> dict:
    return {
        "apollo": bool(os.getenv("APOLLO_API_KEY")),
        "hunter": bool(os.getenv("HUNTER_API_KEY")),
        "prospeo": bool(os.getenv("PROSPEO_API_KEY")),
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {
        "request": request,
        "server_keys": server_has_keys(),
    })


@app.get("/providers")
async def list_providers():
    """Return metadata about each available provider."""
    return JSONResponse({
        name: {
            "label": cls.label,
            "supports_linkedin": cls.supports_linkedin,
            "supports_name": cls.supports_name,
            "requires_domain": cls.requires_domain,
        }
        for name, cls in PROVIDERS.items()
    })


@app.post("/enrich")
async def enrich_contact(payload: EnrichRequest, request: Request):
    keys = get_provider_keys(request)
    ordered = get_ordered_providers(request, keys)

    if not ordered:
        raise HTTPException(status_code=401,
            detail="No API keys configured. Add at least one provider key in Settings.")

    if not payload.linkedin_url and not (payload.first_name and payload.last_name):
        raise HTTPException(status_code=400,
            detail="Provide a LinkedIn URL or at least first name + last name.")

    errors = []
    for provider_name in ordered:
        provider = PROVIDERS[provider_name](keys[provider_name])

        # Skip providers that can't handle this input type
        if payload.linkedin_url and not provider.supports_linkedin:
            continue
        if not payload.linkedin_url and not provider.supports_name:
            continue

        try:
            result = await provider.enrich(
                linkedin_url=payload.linkedin_url,
                first_name=payload.first_name,
                last_name=payload.last_name,
                organization_name=payload.organization_name,
                domain=payload.domain,
                email=payload.email,
            )
            if result.get("found"):
                return JSONResponse(result)
            # Not found — try next provider
            errors.append(f"{provider.label}: not found")
        except ValueError as e:
            errors.append(f"{provider.label}: {e}")
        except Exception as e:
            errors.append(f"{provider.label}: unexpected error — {e}")

    # All providers exhausted
    return JSONResponse({
        "found": False,
        "message": "No contact found across all configured providers.",
        "tried": errors,
    })


@app.post("/bulk-enrich")
async def bulk_enrich(request: Request):
    keys = get_provider_keys(request)
    ordered = get_ordered_providers(request, keys)

    if not ordered:
        raise HTTPException(status_code=401, detail="No API keys configured.")

    body = await request.json()
    urls = [u.strip() for u in (body.get("urls") or "").splitlines() if u.strip()]

    if not urls:
        raise HTTPException(status_code=400, detail="No URLs provided.")
    if len(urls) > 20:
        raise HTTPException(status_code=400, detail="Max 20 URLs per bulk run.")

    results = []
    for url in urls:
        row = {"url": url, "name": "", "title": "", "company": "",
               "email": "", "email_status": "not found", "phone": "", "source": ""}
        for provider_name in ordered:
            provider = PROVIDERS[provider_name](keys[provider_name])
            if not provider.supports_linkedin:
                continue
            try:
                r = await provider.enrich(linkedin_url=url)
                if r.get("found"):
                    emails = r.get("emails") or []
                    row.update({
                        "name": r.get("name", ""),
                        "title": r.get("title", ""),
                        "company": r.get("company", ""),
                        "email": emails[0]["address"] if emails else "",
                        "email_status": r.get("email_label", ""),
                        "phone": r.get("phone") or "",
                        "source": r.get("source", ""),
                    })
                    break
            except Exception:
                pass
        results.append(row)

    return JSONResponse({"results": results})
