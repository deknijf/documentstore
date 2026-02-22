import json
import re
import time
from collections.abc import Callable
from typing import Any

import requests


def _extract_json(text: str) -> dict[str, Any]:
    value = (text or "").strip()
    if value.startswith("{") and value.endswith("}"):
        return json.loads(value)
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", value, re.DOTALL | re.IGNORECASE)
    if fenced:
        return json.loads(fenced.group(1))
    match = re.search(r"\{.*\}", value, re.DOTALL)
    if not match:
        return {}
    return json.loads(match.group(0))


def _provider_model(runtime: dict[str, Any]) -> tuple[str, str]:
    provider = str(runtime.get("ai_provider") or "openrouter").strip().lower()
    if provider == "gemini":
        provider = "google"
    if provider == "openai":
        return provider, str(runtime.get("openai_model") or "gpt-4o-mini")
    if provider == "google":
        return provider, str(runtime.get("google_model") or "gemini-1.5-flash")
    return "openrouter", str(runtime.get("openrouter_model") or "openai/gpt-4o-mini")


def _call_llm(runtime: dict[str, Any], prompt: str, *, max_retries: int = 3) -> dict[str, Any]:
    def _should_retry_status(code: int) -> bool:
        return code in {408, 409, 429} or code >= 500

    def _retry_delay(attempt: int) -> float:
        # 0.8s, 1.6s, 3.2s ...
        return min(6.0, 0.8 * (2 ** max(0, attempt - 1)))

    provider, model = _provider_model(runtime)
    if provider == "openai":
        api_key = runtime.get("openai_api_key")
        if not api_key:
            raise RuntimeError("OpenAI API key ontbreekt")
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Je geeft enkel JSON terug."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=120,
                )
                if _should_retry_status(response.status_code):
                    raise RuntimeError(f"OpenAI tijdelijk onbeschikbaar ({response.status_code})")
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return _extract_json(content)
            except Exception as ex:
                last_error = ex
                if attempt >= max_retries:
                    break
                time.sleep(_retry_delay(attempt))
        raise RuntimeError(f"OpenAI request mislukt na retries: {last_error}")

    if provider == "google":
        api_key = runtime.get("google_api_key")
        if not api_key:
            raise RuntimeError("Google API key ontbreekt")
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1},
        }
        last_error: Exception | None = None
        for attempt in range(1, max_retries + 1):
            try:
                response = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    params={"key": api_key},
                    headers={"Content-Type": "application/json"},
                    json=payload,
                    timeout=120,
                )
                if _should_retry_status(response.status_code):
                    raise RuntimeError(f"Google tijdelijk onbeschikbaar ({response.status_code})")
                response.raise_for_status()
                data = response.json()
                content = (
                    data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                )
                return _extract_json(content)
            except Exception as ex:
                last_error = ex
                if attempt >= max_retries:
                    break
                time.sleep(_retry_delay(attempt))
        raise RuntimeError(f"Google request mislukt na retries: {last_error}")

    api_key = runtime.get("openrouter_api_key")
    if not api_key:
        raise RuntimeError("OpenRouter API key ontbreekt")
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Je geeft enkel JSON terug."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.1,
    }
    last_error: Exception | None = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=120,
            )
            if _should_retry_status(response.status_code):
                raise RuntimeError(f"OpenRouter tijdelijk onbeschikbaar ({response.status_code})")
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return _extract_json(content)
        except Exception as ex:
            last_error = ex
            if attempt >= max_retries:
                break
            time.sleep(_retry_delay(attempt))
    raise RuntimeError(f"OpenRouter request mislukt na retries: {last_error}")


def analyze_budget_transactions_with_llm(
    *,
    transactions: list[dict[str, Any]],
    prompt_template: str,
    mappings: list[dict[str, str]],
    runtime: dict[str, Any],
    known_categories: list[str] | None = None,
    progress_callback: Callable[[int, int], None] | None = None,
) -> dict[str, Any]:
    compact_transactions = []
    for t in transactions:
        remittance = str(t.get("remittance_information") or "")
        counterparty = str(t.get("counterparty_name") or "")
        movement_type = str(t.get("movement_type") or "")
        linked_doc_ctx = str(t.get("linked_document_context") or "")
        compact_transactions.append(
            {
                "external_transaction_id": str(t.get("external_transaction_id") or ""),
                "booking_date": t.get("booking_date"),
                "amount": float(t.get("amount") or 0),
                "currency": t.get("currency") or "EUR",
                # Limit long text fields to keep payload compact and avoid LLM context overflow.
                "counterparty_name": counterparty[:120],
                "remittance_information": remittance[:240],
                "movement_type": movement_type[:80],
                "linked_document_context": linked_doc_ctx[:220],
            }
        )

    mapping_text = json.dumps(mappings or [], ensure_ascii=False)
    category_text = ", ".join([str(c).strip() for c in (known_categories or []) if str(c).strip()]) or "(geen opgegeven categorieën)"

    policy_block = """
Verplichte categorisatieregels:
- "Loon" is de standaardcategorie voor terugkerende inkomsten van werkgever.
- Gebruik primair "counterparty_name" (CSV kolom "Tegenpartij naam") en aanvullend "remittance_information" (CSV kolom "Mededeling") voor categorisatie.
- Gebruik "movement_type" (CSV kolom "Soort beweging") als extra sterk signaal.
- Als movement_type wijst op beheerskost/aanrekening beheerskost => categorie "Bankkosten".
- Als linked_document_context aanwezig is, gebruik die context als extra hint.
- Als flow=income en de mededeling/tegenpartij woorden bevat zoals "werkgever" of "werknemer", categoriseer als "Loon".
- Maak aparte uitgavencategorie "Bankkosten" voor bankgerelateerde kosten.
- Maak aparte uitgavencategorie "Kaartuitgaven (VISA/MASTERCARD)" voor kaartkosten met VISA/Mastercard/Maestro.
- Volgende categorieën zijn ALTIJD uitgaven en nooit inkomsten:
  Restaurants / horeca, Boodschappen, Ontspanning, Reizen / transport, Brandstof, Huur / lening, Energie, Telecom, Verzekeringen, Belastingen, Bankkosten, Kaartuitgaven (VISA/MASTERCARD), Overige uitgaven.
"""

    def _build_chunk_prompt(chunk: list[dict[str, Any]]) -> str:
        payload_text = json.dumps(chunk, ensure_ascii=False)
        return f"""
{prompt_template}
{policy_block}

Handmatige mappings (prioritair toepassen):
{mapping_text}

Voorkeurscategorieën (hergebruik maximaal):
{category_text}

Transacties (JSON chunk):
{payload_text}

Geef ENKEL geldige JSON terug met exact dit schema:
{{
  "transaction_categories": [
    {{
      "external_transaction_id": "string",
      "category": "string",
      "flow": "income|expense",
      "reason": "korte motivatie"
    }}
  ]
}}

Regels:
- Voor elke transaction id moet exact 1 categorisatie bestaan.
- flow=income bij positieve bedragen, flow=expense bij negatieve bedragen.
- category moet altijd ingevuld zijn.
- Gebruik bij voorkeur een categorie uit de voorkeurscategorieën-lijst.
"""

    def _build_summary_prompt(compact_rows: list[dict[str, Any]]) -> str:
        payload_text = json.dumps(compact_rows, ensure_ascii=False)
        return f"""
{prompt_template}
{policy_block}

Handmatige mappings (prioritair toepassen):
{mapping_text}

Hieronder staan geaggregeerde categorie-totalen per flow:
{payload_text}

Geef ENKEL geldige JSON terug met exact dit schema:
{{
  "summary_points": ["max 10 bullets"]
}}
"""

    # Chunking for large CSV datasets. This avoids 400 errors from overlong prompts.
    categories_all: list[dict[str, Any]] = []
    total = len(compact_transactions)
    if progress_callback:
        progress_callback(0, total)
    chunk_size = 80
    failed_chunks = 0
    for i in range(0, len(compact_transactions), chunk_size):
        chunk = compact_transactions[i : i + chunk_size]
        try:
            data = _call_llm(runtime, _build_chunk_prompt(chunk))
            chunk_categories = data.get("transaction_categories") if isinstance(data, dict) else []
            if isinstance(chunk_categories, list):
                categories_all.extend(chunk_categories)
        except Exception:
            failed_chunks += 1
        if progress_callback:
            progress_callback(min(i + len(chunk), total), total)

    # Build a small aggregated input for summary generation.
    per_category: dict[str, dict[str, float]] = {}
    category_by_id: dict[str, dict[str, Any]] = {}
    for row in categories_all:
        if not isinstance(row, dict):
            continue
        ext_id = str(row.get("external_transaction_id") or "").strip()
        if ext_id:
            category_by_id[ext_id] = row
    for tx in compact_transactions:
        ext_id = str(tx.get("external_transaction_id") or "").strip()
        amount = float(tx.get("amount") or 0)
        flow = "income" if amount >= 0 else "expense"
        row = category_by_id.get(ext_id) or {}
        category = str(row.get("category") or "Ongecategoriseerd").strip() or "Ongecategoriseerd"
        if category not in per_category:
            per_category[category] = {"income": 0.0, "expense": 0.0}
        if flow == "income":
            per_category[category]["income"] += abs(amount)
        else:
            per_category[category]["expense"] += abs(amount)
    summary_input = [
        {"category": cat, "income": vals["income"], "expense": vals["expense"]}
        for cat, vals in per_category.items()
    ]
    summary_points: list[str] = []
    if summary_input:
        try:
            summary_data = _call_llm(runtime, _build_summary_prompt(summary_input[:120]))
            parsed_points = summary_data.get("summary_points") if isinstance(summary_data, dict) else []
            if isinstance(parsed_points, list):
                summary_points = [str(p) for p in parsed_points if str(p).strip()]
        except Exception as ex:
            summary_points = [f"Samenvatting via LLM tijdelijk niet beschikbaar: {str(ex)}"]
    if failed_chunks:
        summary_points.insert(
            0,
            f"LLM chunk fallback actief: {failed_chunks} chunk(s) tijdelijk mislukt; categorieën aangevuld via fallbackregels.",
        )
    return {
        "summary_points": summary_points if isinstance(summary_points, list) else [],
        "transaction_categories": categories_all,
    }


def match_document_payment_with_llm(
    *,
    document: dict[str, Any],
    candidates: list[dict[str, Any]],
    runtime: dict[str, Any],
) -> dict[str, Any]:
    if not candidates:
        return {"matched": False}
    doc_payload = {
        "id": document.get("id"),
        "category": document.get("category"),
        "issuer": document.get("issuer"),
        "subject": document.get("subject"),
        "document_date": document.get("document_date"),
        "due_date": document.get("due_date"),
        "total_amount": document.get("total_amount"),
        "currency": document.get("currency"),
        "iban": document.get("iban"),
        "structured_reference": document.get("structured_reference"),
    }
    compact_candidates = []
    for c in candidates[:8]:
        compact_candidates.append(
            {
                "external_transaction_id": c.get("external_transaction_id"),
                "booking_date": c.get("booking_date"),
                "amount": c.get("amount"),
                "currency": c.get("currency"),
                "counterparty_name": str(c.get("counterparty_name") or "")[:140],
                "remittance_information": str(c.get("remittance_information") or "")[:320],
                "raw_json": str(c.get("raw_json") or "")[:320],
            }
        )

    prompt = f"""
Je controleert of een banktransactie overeenkomt met een documentbetaling.
Geef ENKEL geldige JSON terug.

Document:
{json.dumps(doc_payload, ensure_ascii=False)}

Kandidaten:
{json.dumps(compact_candidates, ensure_ascii=False)}

Matchregels (prioriteit):
1) Sterk: bedrag exact + IBAN match + mededeling/gestructureerde mededeling match.
2) Fallback: bedrag exact + IBAN match + document_date binnen 3 maanden van booking_date.
3) Fallback: bedrag exact + document_date binnen 3 maanden + naamdeel (afzender/instantie, >=4 chars) in mededeling/tegenpartij.

Antwoordschema:
{{
  "matched": true|false,
  "external_transaction_id": "string|null",
  "confidence": "high|medium|low",
  "reason": "korte reden in het Nederlands"
}}

Regels:
- Als geen kandidaat duidelijk voldoet: matched=false.
- Kies maximaal 1 kandidaat.
- confidence=high voor regel 1, medium voor regel 2, low voor regel 3.
"""
    try:
        data = _call_llm(runtime, prompt)
    except Exception:
        return {"matched": False}
    if not isinstance(data, dict):
        return {"matched": False}
    matched = bool(data.get("matched"))
    ext_id = str(data.get("external_transaction_id") or "").strip() or None
    confidence = str(data.get("confidence") or "").strip().lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"
    reason = str(data.get("reason") or "").strip()
    return {
        "matched": matched,
        "external_transaction_id": ext_id,
        "confidence": confidence,
        "reason": reason,
    }
