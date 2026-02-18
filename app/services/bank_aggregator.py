import hashlib
import json
from typing import Any

import requests


SUPPORTED_BANK_PROVIDERS = {"vdk", "kbc", "bnp"}


class BankAggregatorClient:
    """
    Generic read-only client for bank/aggregator APIs.

    This client is intentionally read-only and only performs GET calls.
    """

    def __init__(
        self,
        *,
        provider: str,
        base_url: str,
        client_id: str | None = None,
        api_key: str | None = None,
        password: str | None = None,
    ) -> None:
        self.provider = str(provider or "vdk").strip().lower()
        if self.provider not in SUPPORTED_BANK_PROVIDERS:
            raise RuntimeError("Ongekende bank provider")

        self.base_url = (base_url or "").strip().rstrip("/")
        self.client_id = (client_id or "").strip()
        self.api_key = (api_key or "").strip()
        self.password = (password or "").strip()

        if not self.base_url:
            raise RuntimeError(f"{self.provider.upper()} base URL ontbreekt")

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        if self.client_id:
            headers["X-Client-Id"] = self.client_id
        if self.password:
            if self.provider == "vdk":
                headers["X-VDK-Password"] = self.password
            elif self.provider == "kbc":
                headers["X-KBC-Password"] = self.password
            elif self.provider == "bnp":
                headers["X-BNP-Password"] = self.password
        return headers

    def _normalize_accounts(self, payload: Any) -> list[dict[str, str]]:
        rows: list[Any]
        if isinstance(payload, list):
            rows = payload
        elif isinstance(payload, dict):
            rows = payload.get("accounts") or payload.get("data") or []
        else:
            rows = []

        out: list[dict[str, str]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            raw_external_id = str(row.get("resourceId") or row.get("accountId") or row.get("id") or "").strip()
            if not raw_external_id:
                continue
            out.append(
                {
                    "provider": self.provider,
                    "raw_external_account_id": raw_external_id,
                    "external_account_id": f"{self.provider}:{raw_external_id}",
                    "name": str(row.get("name") or row.get("product") or raw_external_id).strip(),
                    "iban": str(row.get("iban") or "").strip() or None,
                }
            )
        return out

    def _normalize_transactions(self, payload: Any) -> list[dict[str, Any]]:
        rows: list[Any] = []
        if isinstance(payload, dict):
            tx = payload.get("transactions")
            if isinstance(tx, dict):
                rows = (tx.get("booked") or []) + (tx.get("pending") or [])
            elif isinstance(tx, list):
                rows = tx
            else:
                rows = payload.get("booked") or payload.get("data") or []
        elif isinstance(payload, list):
            rows = payload

        out: list[dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            amount_info = row.get("transactionAmount") if isinstance(row.get("transactionAmount"), dict) else {}
            amount = amount_info.get("amount")
            currency = amount_info.get("currency")
            booking_date = row.get("bookingDate")
            value_date = row.get("valueDate")
            remittance = (
                row.get("remittanceInformationStructured")
                or row.get("remittanceInformationUnstructured")
                or row.get("remittanceInformation")
                or ""
            )
            counterparty = row.get("debtorName") or row.get("creditorName") or row.get("counterpartyName") or ""
            external_tx_id = str(row.get("transactionId") or row.get("entryReference") or row.get("id") or "").strip()
            if not external_tx_id:
                fingerprint = f"{booking_date}|{amount}|{currency}|{counterparty}|{remittance}"
                external_tx_id = f"auto_{hashlib.sha256(fingerprint.encode('utf-8')).hexdigest()[:24]}"

            try:
                amount_float = float(str(amount).replace(",", ".")) if amount is not None else None
            except Exception:
                amount_float = None

            out.append(
                {
                    "external_transaction_id": external_tx_id,
                    "booking_date": str(booking_date).strip() if booking_date else None,
                    "value_date": str(value_date).strip() if value_date else None,
                    "amount": amount_float,
                    "currency": str(currency).strip() if currency else None,
                    "counterparty_name": str(counterparty).strip() or None,
                    "remittance_information": str(remittance).strip() or None,
                    "raw_json": json.dumps(row, ensure_ascii=False),
                }
            )
        return out

    def fetch_accounts(self) -> list[dict[str, str]]:
        resp = requests.get(f"{self.base_url}/accounts", headers=self._headers(), timeout=60)
        resp.raise_for_status()
        return self._normalize_accounts(resp.json())

    def fetch_transactions(
        self,
        raw_external_account_id: str,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, str] = {}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        resp = requests.get(
            f"{self.base_url}/accounts/{raw_external_account_id}/transactions",
            headers=self._headers(),
            params=params,
            timeout=60,
        )
        resp.raise_for_status()
        return self._normalize_transactions(resp.json())
