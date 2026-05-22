import httpx
from typing import Optional
from .base import BaseProvider


class ProspeoProvider(BaseProvider):
    name = "prospeo"
    label = "Prospeo"
    supports_linkedin = True
    supports_name = False   # Prospeo is LinkedIn URL focused

    async def enrich(self, linkedin_url=None, first_name=None, last_name=None,
                     organization_name=None, domain=None, email=None) -> dict:
        if not linkedin_url:
            return self.not_found("Prospeo requires a LinkedIn URL.")

        headers = {"X-KEY": self.api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                "https://api.prospeo.io/linkedin-email-finder",
                json={"url": linkedin_url},
                headers=headers,
            )

        if resp.status_code == 401:
            raise ValueError("Invalid Prospeo API key.")
        if resp.status_code == 429:
            raise ValueError("Prospeo rate limit hit.")
        if resp.status_code != 200:
            raise ValueError(f"Prospeo error {resp.status_code}: {resp.text}")

        data = resp.json()
        if not data.get("error") is False and not data.get("response"):
            return self.not_found()

        r = data.get("response") or {}
        found_email = r.get("email") or (r.get("email_list") or [{}])[0].get("email")

        if not found_email:
            return self.not_found()

        verified = r.get("verified", False)
        confidence = "high" if verified else "medium"
        label = "Verified" if verified else "Likely Valid"

        emails = []
        for e in r.get("email_list") or []:
            if e.get("email"):
                emails.append({
                    "address": e["email"],
                    "type": "work",
                    "status": "verified" if e.get("verified") else "guessed",
                })
        if not emails and found_email:
            emails = [{"address": found_email, "type": "work", "status": "verified" if verified else "guessed"}]

        name_parts = [r.get("first_name", ""), r.get("last_name", "")]
        name = " ".join(p for p in name_parts if p)

        return {
            "found": True,
            "name": name,
            "title": r.get("job_title", ""),
            "company": r.get("company", ""),
            "linkedin_url": linkedin_url,
            "location": r.get("location", ""),
            "emails": emails,
            "email_confidence": confidence,
            "email_label": label,
            "phone": r.get("phone"),
            "phone_type": "Mobile" if r.get("phone") else None,
            "photo_url": "",
            "source": self.label,
        }
