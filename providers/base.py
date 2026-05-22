"""
Base class for all enrichment providers.

To add a new provider:
  1. Create providers/yourprovider.py and subclass BaseProvider
  2. Implement enrich() — return a normalized ContactResult dict
  3. Register it in providers/__init__.py
"""
from abc import ABC, abstractmethod
from typing import Optional
import httpx


class BaseProvider(ABC):
    name: str = "unknown"
    label: str = "Unknown"
    supports_linkedin: bool = False   # can look up by LinkedIn URL
    supports_name: bool = False       # can look up by name + company/domain
    requires_domain: bool = False     # name lookup needs a domain, not just company name

    def __init__(self, api_key: str):
        self.api_key = api_key

    @abstractmethod
    async def enrich(
        self,
        linkedin_url: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        organization_name: Optional[str] = None,
        domain: Optional[str] = None,
        email: Optional[str] = None,
    ) -> dict:
        """
        Return a normalized ContactResult dict:
        {
            "found": bool,
            "name": str,
            "title": str,
            "company": str,
            "linkedin_url": str,
            "location": str,
            "emails": [{"address": str, "type": "work"|"personal", "status": str}],
            "email_confidence": "high"|"medium"|"none"|"unknown",
            "email_label": str,
            "phone": str | None,
            "phone_type": str | None,
            "photo_url": str,
            "source": str,   # provider name for attribution
        }
        Or on miss:
        { "found": False, "message": str }
        """
        ...

    def not_found(self, message: str = "No contact found.") -> dict:
        return {"found": False, "message": message, "source": self.label}

    def confidence(self, status: str):
        s = (status or "").lower()
        if s in ("verified", "valid", "confirmed"):
            return "high", "Verified"
        if s in ("guessed", "likely to engage", "accept_all", "webmail"):
            return "medium", "Likely Valid"
        if s in ("unavailable", "invalid", "disposable", "not found"):
            return "none", "Not Found"
        return "medium", s.title() or "Unknown"
