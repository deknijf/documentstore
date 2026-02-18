import json
import re
from typing import Any

import requests

from app.config import settings


def _extract_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return json.loads(text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return {}
    return json.loads(match.group(0))


STRUCTURED_REF_PROMPT_RULES = """
- structured_reference (gestructureerde mededeling):
  - Herken expliciet Belgische vorm ###/####/##### (3-4-5 cijfers met '/').
  - Vaak omringd door +++...+++ of ***...***; strip die tekens, bewaar enkel ###/####/#####.
  - Bij documenten met "OVERSCHRIJVINGSOPDRACHT", "gestructureerde mededeling" of "mededeling":
    zoek actief naar dit patroon en geef exact dit formaat terug.
  - Als geen valide patroon gevonden: null.
"""


class OpenRouterExtractor:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.openrouter_api_key
        if not self.api_key:
            raise RuntimeError("OPENROUTER_API_KEY ontbreekt")
        self.model = model or settings.openrouter_model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def extract_metadata(
        self,
        ocr_text: str,
        filename: str,
        category_profiles: list[dict[str, Any]] | None = None,
        preferred_category: str | None = None,
    ) -> dict:
        profile_text = ""
        if category_profiles:
            profile_text = "\nCategorieprofielen (naam, prompt, velden, paid_default):\n" + json.dumps(
                category_profiles,
                ensure_ascii=False,
            )
        preferred_text = ""
        if preferred_category:
            preferred_text = (
                f"\nVoorkeurscategorie voor dit document: {preferred_category}\n"
                "Gebruik deze categorie als leidend profiel voor welke velden relevant zijn."
            )
        prompt = f"""
Je bent een document-catalogisering assistant.
Geef uitsluitend geldige JSON terug met deze velden:
category, issuer, subject, document_date, due_date, total_amount, currency, iban, structured_reference, paid, paid_on, items, summary, extra_fields.

Regels:
- category moet zoveel mogelijk overeenkomen met de opgegeven categorieprofielen.
- document_date en due_date als YYYY-MM-DD als mogelijk, anders null.
- total_amount enkel nummer, anders null.
- iban enkel als duidelijk aanwezig.
- structured_reference enkel als gestructureerde mededeling/referentie duidelijk aanwezig.
{STRUCTURED_REF_PROMPT_RULES}
- paid is boolean als duidelijk.
- paid_on als YYYY-MM-DD indien betaaldatum duidelijk.
- items is korte lijst (array van strings) voor kasticket indien mogelijk.
- extra_fields is een object met extra parameters uit het gekozen categorieprofiel die niet in de standaardvelden zitten.
{profile_text}
{preferred_text}

Bestandsnaam: {filename}
Tekst:
{ocr_text[:12000]}
"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Je retourneert alleen JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        try:
            data = _extract_json(content)
        except Exception:
            data = {}
        return data if isinstance(data, dict) else {}


class OpenAIExtractor:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.openai_api_key
        if not self.api_key:
            raise RuntimeError("OPENAI_API_KEY ontbreekt")
        self.model = model or settings.openai_model
        self.base_url = "https://api.openai.com/v1/chat/completions"

    def extract_metadata(
        self,
        ocr_text: str,
        filename: str,
        category_profiles: list[dict[str, Any]] | None = None,
        preferred_category: str | None = None,
    ) -> dict:
        profile_text = ""
        if category_profiles:
            profile_text = "\nCategorieprofielen (naam, prompt, velden, paid_default):\n" + json.dumps(
                category_profiles,
                ensure_ascii=False,
            )
        preferred_text = ""
        if preferred_category:
            preferred_text = (
                f"\nVoorkeurscategorie voor dit document: {preferred_category}\n"
                "Gebruik deze categorie als leidend profiel voor welke velden relevant zijn."
            )
        prompt = f"""
Je bent een document-catalogisering assistant.
Geef uitsluitend geldige JSON terug met deze velden:
category, issuer, subject, document_date, due_date, total_amount, currency, iban, structured_reference, paid, paid_on, items, summary, extra_fields.

Regels:
- category moet zoveel mogelijk overeenkomen met de opgegeven categorieprofielen.
- document_date en due_date als YYYY-MM-DD als mogelijk, anders null.
- total_amount enkel nummer, anders null.
- iban enkel als duidelijk aanwezig.
- structured_reference enkel als gestructureerde mededeling/referentie duidelijk aanwezig.
{STRUCTURED_REF_PROMPT_RULES}
- paid is boolean als duidelijk.
- paid_on als YYYY-MM-DD indien betaaldatum duidelijk.
- items is korte lijst (array van strings) voor kasticket indien mogelijk.
- extra_fields is een object met extra parameters uit het gekozen categorieprofiel die niet in de standaardvelden zitten.
{profile_text}
{preferred_text}

Bestandsnaam: {filename}
Tekst:
{ocr_text[:12000]}
"""
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Je retourneert alleen JSON."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        response = requests.post(self.base_url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        try:
            data = _extract_json(content)
        except Exception:
            data = {}
        return data if isinstance(data, dict) else {}


class GoogleExtractor:
    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.google_api_key
        if not self.api_key:
            raise RuntimeError("GOOGLE_API_KEY ontbreekt")
        self.model = model or settings.google_model
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def extract_metadata(
        self,
        ocr_text: str,
        filename: str,
        category_profiles: list[dict[str, Any]] | None = None,
        preferred_category: str | None = None,
    ) -> dict:
        profile_text = ""
        if category_profiles:
            profile_text = "\nCategorieprofielen (naam, prompt, velden, paid_default):\n" + json.dumps(
                category_profiles,
                ensure_ascii=False,
            )
        preferred_text = ""
        if preferred_category:
            preferred_text = (
                f"\nVoorkeurscategorie voor dit document: {preferred_category}\n"
                "Gebruik deze categorie als leidend profiel voor welke velden relevant zijn."
            )
        prompt = f"""
Je bent een document-catalogisering assistant.
Geef uitsluitend geldige JSON terug met deze velden:
category, issuer, subject, document_date, due_date, total_amount, currency, iban, structured_reference, paid, paid_on, items, summary, extra_fields.

Regels:
- category moet zoveel mogelijk overeenkomen met de opgegeven categorieprofielen.
- document_date en due_date als YYYY-MM-DD als mogelijk, anders null.
- total_amount enkel nummer, anders null.
- iban enkel als duidelijk aanwezig.
- structured_reference enkel als gestructureerde mededeling/referentie duidelijk aanwezig.
{STRUCTURED_REF_PROMPT_RULES}
- paid is boolean als duidelijk.
- paid_on als YYYY-MM-DD indien betaaldatum duidelijk.
- items is korte lijst (array van strings) voor kasticket indien mogelijk.
- extra_fields is een object met extra parameters uit het gekozen categorieprofiel die niet in de standaardvelden zitten.
{profile_text}
{preferred_text}

Bestandsnaam: {filename}
Tekst:
{ocr_text[:12000]}
"""
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1},
        }
        response = requests.post(
            self.base_url,
            params={"key": self.api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=90,
        )
        response.raise_for_status()
        data = response.json()
        text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )
        try:
            parsed = _extract_json(text)
        except Exception:
            parsed = {}
        return parsed if isinstance(parsed, dict) else {}


def get_ai_extractor(provider: str, *, runtime: dict[str, Any]) -> Any:
    p = (provider or settings.ai_provider or "openrouter").strip().lower()
    if p == "openai":
        return OpenAIExtractor(
            api_key=runtime.get("openai_api_key"),
            model=runtime.get("openai_model"),
        )
    if p in {"google", "gemini"}:
        return GoogleExtractor(
            api_key=runtime.get("google_api_key"),
            model=runtime.get("google_model"),
        )
    return OpenRouterExtractor(
        api_key=runtime.get("openrouter_api_key"),
        model=runtime.get("openrouter_model"),
    )
