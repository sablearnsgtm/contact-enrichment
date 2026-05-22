import httpx
from typing import Optional
from .base import BaseProvider


class ApolloProvider(BaseProvider):
    name = "apollo"
    label = "Apollo"
    supports_linkedin = True
    supports_name = True
    requires_domain = False

    async def enrich(self, linkedin_url=None, first_name=None, last_name=None,
                     organization_name=None, domain=None, email=None) -> dict:
        body = {"reveal_personal_emails": True}
        if linkedin_url:
            body["linkedin_url"] = linkedin_url
        if first_name:
            body["first_name"] = first_name
        if last_name:
            body["last_name"] = last_name
        if organization_name:
            body["organization_name"] = organization_name
        if email:
            body["email"] = email

        headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post("https://api.apollo.io/v1/people/match",
                                     json=body, headers=headers)

        if resp.status_code == 401:
            raise ValueError("Invalid Apollo API key.")
        if resp.status_code == 429:
            raise ValueError("Apollo rate limit hit. Try again shortly.")
        if resp.status_code != 200:
            raise ValueError(f"Apollo error {resp.status_code}: {resp.text}")

        person = resp.json().get("person")
        if not person:
            return self.not_found()

        phones = person.get("phone_numbers") or []
        mobile = next((p for p in phones if p.get("type") == "mobile"), None)
        any_phone = mobile or (phones[0] if phones else None)

        raw_status = person.get("email_status") or "unknown"
        confidence, label = self.confidence(raw_status)

        emails = []
        if person.get("email"):
            emails.append({"address": person["email"], "type": "work", "status": raw_status})
        for e in person.get("personal_emails") or []:
            emails.append({"address": e, "type": "personal", "status": "unknown"})

        location = ", ".join(filter(None, [person.get("city"), person.get("state"), person.get("country")]))

        return {
            "found": True,
            "name": person.get("name", ""),
            "title": person.get("title", ""),
            "company": (person.get("organization") or {}).get("name", ""),
            "linkedin_url": person.get("linkedin_url", ""),
            "location": location,
            "emails": emails,
            "email_confidence": confidence,
            "email_label": label,
            "phone": any_phone.get("sanitized_number") if any_phone else None,
            "phone_type": any_phone.get("type", "").replace("_", " ").title() if any_phone else None,
            "photo_url": person.get("photo_url", ""),
            "source": self.label,
        }
