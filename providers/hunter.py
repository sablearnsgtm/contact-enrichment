import httpx
from typing import Optional
from .base import BaseProvider


class HunterProvider(BaseProvider):
    name = "hunter"
    label = "Hunter.io"
    supports_linkedin = False   # Hunter doesn't accept LinkedIn URLs
    supports_name = True
    requires_domain = True      # needs domain (e.g. acme.com), not just company name

    async def enrich(self, linkedin_url=None, first_name=None, last_name=None,
                     organization_name=None, domain=None, email=None) -> dict:
        # Hunter needs a domain — try domain first, fall back to guessing from org name
        target_domain = domain or organization_name
        if not target_domain:
            return self.not_found("Hunter.io requires a company domain (e.g. acme.com).")
        if not first_name or not last_name:
            return self.not_found("Hunter.io requires a first and last name.")

        params = {
            "first_name": first_name,
            "last_name": last_name,
            "domain": target_domain,
            "api_key": self.api_key,
        }
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get("https://api.hunter.io/v2/email-finder", params=params)

        if resp.status_code == 401:
            raise ValueError("Invalid Hunter.io API key.")
        if resp.status_code == 429:
            raise ValueError("Hunter.io rate limit hit.")
        if resp.status_code not in (200, 404):
            raise ValueError(f"Hunter.io error {resp.status_code}: {resp.text}")

        data = resp.json().get("data") or {}
        found_email = data.get("email")

        if not found_email:
            return self.not_found(f"No email found via Hunter.io for {first_name} {last_name} at {target_domain}.")

        score = data.get("score", 0)
        # Hunter score: 0-100. ≥80 = high, 40-79 = medium, <40 = low
        if score >= 80:
            confidence, label = "high", "Verified"
        elif score >= 40:
            confidence, label = "medium", f"Likely Valid ({score}%)"
        else:
            confidence, label = "none", f"Low Confidence ({score}%)"

        sources = data.get("sources") or []

        return {
            "found": True,
            "name": f"{first_name} {last_name}",
            "title": data.get("position", ""),
            "company": data.get("company", organization_name or ""),
            "linkedin_url": data.get("linkedin", ""),
            "location": "",
            "emails": [{"address": found_email, "type": "work", "status": data.get("verification", {}).get("status", "unknown")}],
            "email_confidence": confidence,
            "email_label": label,
            "phone": data.get("phone_number"),
            "phone_type": "Work" if data.get("phone_number") else None,
            "photo_url": "",
            "source": self.label,
        }
