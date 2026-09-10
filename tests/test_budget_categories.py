"""Categorisation rules the owner set: a hand-set category outranks every
automatic source and survives re-analysis, and the category list may not grow by
itself."""

import pytest

from app.legacy_main import (
    FALLBACK_BUDGET_CATEGORIES,
    _build_budget_analysis_payload,
    _sync_budget_categories_to_mapping_settings,
)

MAPPINGS = [{"keyword": "energieleverancier", "flow": "expense", "category": "Energie"}]
KNOWN = ["Energie", "Telecom", "Boodschappen"]


def _tx(ext_id="tx-1", *, amount=-42.0, counterparty="Energieleverancier BV", remittance=""):
    return {
        "external_transaction_id": ext_id,
        "booking_date": "2025-03-04",
        "amount": amount,
        "currency": "EUR",
        "counterparty_name": counterparty,
        "remittance_information": remittance,
        "raw_json": "",
    }


def _only(payload):
    assert len(payload["transactions"]) == 1
    return payload["transactions"][0]


def test_keyword_mapping_wins_when_nothing_was_set_by_hand():
    row = _only(_build_budget_analysis_payload([_tx()], {}, MAPPINGS, preferred_categories=KNOWN))
    assert (row["category"], row["source"]) == ("Energie", "mapping")
    assert row["auto_mapping"] is True and row["manual_mapping"] is False


def test_manual_category_beats_a_keyword_mapping():
    payload = _build_budget_analysis_payload(
        [_tx()], {}, MAPPINGS, preferred_categories=KNOWN,
        manual_categories={"tx-1": "Boodschappen"},
    )
    row = _only(payload)
    assert row["category"] == "Boodschappen"
    assert row["source"] == "manual"
    assert row["manual_mapping"] is True
    assert row["auto_mapping"] is False and row["llm_mapping"] is False


def test_manual_category_beats_the_llm():
    llm = {"transaction_categories": [{"external_transaction_id": "tx-1", "category": "Telecom"}]}
    row = _only(
        _build_budget_analysis_payload(
            [_tx(counterparty="Onbekend")], llm, [], preferred_categories=KNOWN,
            manual_categories={"tx-1": "Boodschappen"},
        )
    )
    assert row["category"] == "Boodschappen"
    assert row["source"] == "manual"


def test_manual_category_survives_when_no_automation_matches_at_all():
    row = _only(
        _build_budget_analysis_payload(
            [_tx(counterparty="Onbekend")], {}, [], preferred_categories=KNOWN,
            manual_categories={"tx-1": "Boodschappen"},
        )
    )
    assert row["category"] == "Boodschappen"
    assert "Handmatig" in str(row["reason"])


def test_manual_category_only_applies_to_its_own_transaction():
    payload = _build_budget_analysis_payload(
        [_tx("tx-1"), _tx("tx-2")], {}, MAPPINGS, preferred_categories=KNOWN,
        manual_categories={"tx-1": "Boodschappen"},
    )
    by_id = {r["external_transaction_id"]: r for r in payload["transactions"]}
    assert by_id["tx-1"]["category"] == "Boodschappen"
    assert by_id["tx-2"]["category"] == "Energie"


@pytest.mark.parametrize("returned", ["energie", "  Energie  ", "ENERGIE"])
def test_llm_category_snaps_to_the_tenants_own_spelling(returned):
    llm = {"transaction_categories": [{"external_transaction_id": "tx-1", "category": returned}]}
    row = _only(
        _build_budget_analysis_payload([_tx(counterparty="Onbekend")], llm, [], preferred_categories=KNOWN)
    )
    assert row["category"] == "Energie", "near-miss spellings must not become new categories"


def test_totals_group_a_snapped_category_only_once():
    llm = {
        "transaction_categories": [
            {"external_transaction_id": "tx-1", "category": "Energie"},
            {"external_transaction_id": "tx-2", "category": "energie"},
        ]
    }
    payload = _build_budget_analysis_payload(
        [_tx("tx-1", counterparty="X"), _tx("tx-2", counterparty="Y")], llm, [], preferred_categories=KNOWN
    )
    assert [c["category"] for c in payload["category_totals"]] == ["Energie"]


def test_invented_category_does_not_become_a_permanent_option(client, tenant_a):
    from app.db import SessionLocal
    from app.models import BankCategoryMapping

    db = SessionLocal()
    try:
        before = db.query(BankCategoryMapping).filter(
            BankCategoryMapping.tenant_id == tenant_a["tenant_id"]
        ).count()
        created = _sync_budget_categories_to_mapping_settings(
            db, tenant_a["tenant_id"], [{"category": "Zelfverzonnen Categorie", "flow": "expense"}]
        )
        after = db.query(BankCategoryMapping).filter(
            BankCategoryMapping.tenant_id == tenant_a["tenant_id"]
        ).count()
    finally:
        db.close()
    assert created == 0
    assert after == before


def test_rule_fallback_category_does_become_a_permanent_option(client, tenant_a):
    from app.db import SessionLocal
    from app.models import BankCategoryMapping

    category = sorted(FALLBACK_BUDGET_CATEGORIES)[0]
    db = SessionLocal()
    try:
        db.query(BankCategoryMapping).filter(
            BankCategoryMapping.tenant_id == tenant_a["tenant_id"],
            BankCategoryMapping.category == category,
        ).delete()
        db.commit()
        created = _sync_budget_categories_to_mapping_settings(
            db, tenant_a["tenant_id"], [{"category": category, "flow": "expense"}]
        )
    finally:
        db.close()
    assert created == 1


def test_an_existing_category_is_not_duplicated_by_spelling(client, tenant_a):
    from app.db import SessionLocal
    from app.models import BankCategoryMapping

    db = SessionLocal()
    try:
        db.add(
            BankCategoryMapping(
                tenant_id=tenant_a["tenant_id"], keyword="x", flow="expense",
                category="Energie", priority=1, is_active=True,
            )
        )
        db.commit()
        created = _sync_budget_categories_to_mapping_settings(
            db, tenant_a["tenant_id"], [{"category": "  energie ", "flow": "expense"}]
        )
    finally:
        db.close()
    assert created == 0


def test_prompt_forces_a_choice_from_the_existing_categories(monkeypatch):
    import app.services.bank_budget_ai as ai

    prompts = []
    monkeypatch.setattr(ai, "_call_llm", lambda runtime, prompt, **kw: prompts.append(prompt) or {})
    ai.analyze_budget_transactions_with_llm(
        transactions=[_tx()], prompt_template="p", mappings=[], runtime={},
        known_categories=KNOWN,
    )
    assert prompts, "no prompt was built"
    assert "MOET exact overeenkomen" in prompts[0]
    assert "Verzin geen nieuwe categorie" in prompts[0]


def test_prompt_stays_open_when_no_categories_exist_yet(monkeypatch):
    import app.services.bank_budget_ai as ai

    prompts = []
    monkeypatch.setattr(ai, "_call_llm", lambda runtime, prompt, **kw: prompts.append(prompt) or {})
    ai.analyze_budget_transactions_with_llm(
        transactions=[_tx()], prompt_template="p", mappings=[], runtime={}, known_categories=[],
    )
    assert "MOET exact overeenkomen" not in prompts[0]


def test_manual_transactions_are_never_sent_to_the_llm(client, tenant_a, monkeypatch):
    """Skipping them is both the rule and a cost saving."""
    import app.legacy_main as legacy_main
    from app.db import SessionLocal
    from app.models import BankTransaction, User

    seen: dict[str, list[str]] = {}

    def _fake_llm(**kwargs):
        seen["ids"] = [t["external_transaction_id"] for t in kwargs["transactions"]]
        return {"summary_points": [], "transaction_categories": []}

    monkeypatch.setattr(legacy_main, "analyze_budget_transactions_with_llm", _fake_llm)

    db = SessionLocal()
    try:
        account = legacy_main._get_or_create_csv_import_account(db, tenant_a["tenant_id"])
        for ext_id, is_manual in (("man-1", True), ("auto-1", False)):
            db.add(
                BankTransaction(
                    tenant_id=tenant_a["tenant_id"],
                    bank_account_id=account.id,
                    external_transaction_id=ext_id,
                    booking_date="2025-04-01",
                    amount=-10.0,
                    currency="EUR",
                    counterparty_name="Onbekende partij",
                    remittance_information="",
                    category="Boodschappen" if is_manual else None,
                    source="manual" if is_manual else None,
                    manual_mapping=is_manual,
                )
            )
        db.commit()
        user = db.query(User).filter(User.id == tenant_a["user_id"]).first()
        result = legacy_main.analyze_bank_budget(db=db, current_user=user)
    finally:
        db.close()

    assert "man-1" not in seen.get("ids", []), "a hand-set transaction was sent to the LLM"
    assert "auto-1" in seen.get("ids", [])

    by_id = {r["external_transaction_id"]: r for r in result["transactions"]}
    assert by_id["man-1"]["category"] == "Boodschappen"
    assert by_id["man-1"]["source"] == "manual"


def test_reanalysis_does_not_clear_the_manual_flag_in_the_database(client, tenant_a, monkeypatch):
    import app.legacy_main as legacy_main
    from app.db import SessionLocal
    from app.models import BankTransaction, User

    monkeypatch.setattr(
        legacy_main,
        "analyze_budget_transactions_with_llm",
        lambda **kw: {"summary_points": [], "transaction_categories": []},
    )
    db = SessionLocal()
    try:
        account = legacy_main._get_or_create_csv_import_account(db, tenant_a["tenant_id"])
        db.add(
            BankTransaction(
                tenant_id=tenant_a["tenant_id"],
                bank_account_id=account.id,
                external_transaction_id="man-2",
                booking_date="2025-05-02",
                amount=-77.0,
                currency="EUR",
                counterparty_name="Energieleverancier BV",
                remittance_information="",
                category="Boodschappen",
                source="manual",
                manual_mapping=True,
            )
        )
        db.add(
            legacy_main.BankCategoryMapping(
                tenant_id=tenant_a["tenant_id"],
                keyword="Energieleverancier",
                flow="expense",
                category="Energie",
                priority=1,
                is_active=True,
            )
        )
        db.commit()
        user = db.query(User).filter(User.id == tenant_a["user_id"]).first()
        legacy_main.analyze_bank_budget(db=db, current_user=user)

        row = (
            db.query(BankTransaction)
            .filter(
                BankTransaction.tenant_id == tenant_a["tenant_id"],
                BankTransaction.external_transaction_id == "man-2",
            )
            .first()
        )
        # A keyword mapping matches this counterparty; it must not win.
        assert row.category == "Boodschappen"
        assert row.manual_mapping is True
        assert row.auto_mapping is False
    finally:
        db.close()
