"""An analysis whose provider failed must not break every later analysis.

source_hash is unique, and a run that recorded a provider failure is
deliberately not reused as a cache. Recomputing then used to insert a second row
for the same inputs, which the unique index rejected with a 500 that persisted
until the transaction set changed.
"""

FAILED_SUMMARY = {
    "summary_points": ["LLM chunk fallback actief: 1 chunk(s) tijdelijk mislukt"],
    "transaction_categories": [],
}


def _run_ids(db, tenant_id) -> set[str]:
    from app.models import BankBudgetAnalysisRun

    return {
        str(r.id)
        for r in db.query(BankBudgetAnalysisRun).filter(
            BankBudgetAnalysisRun.tenant_id == tenant_id
        )
    }


def test_a_failed_analysis_does_not_poison_later_ones(client, tenant_a, monkeypatch):
    import app.legacy_main as legacy_main
    from app.db import SessionLocal
    from app.models import BankBudgetAnalysisRun, BankBudgetAnalysisTx, BankTransaction, User

    monkeypatch.setattr(
        legacy_main, "analyze_budget_transactions_with_llm", lambda **kw: FAILED_SUMMARY
    )

    db = SessionLocal()
    try:
        account = legacy_main._get_or_create_csv_import_account(db, tenant_a["tenant_id"])
        db.add(
            BankTransaction(
                tenant_id=tenant_a["tenant_id"],
                bank_account_id=account.id,
                external_transaction_id="poison-1",
                booking_date="2025-06-03",
                amount=-12.5,
                currency="EUR",
                counterparty_name="Onbekende partij",
                remittance_information="",
            )
        )
        db.commit()
        user = db.query(User).filter(User.id == tenant_a["user_id"]).first()

        # The first analysis registers rule-fallback categories, which changes
        # the mapping set and therefore the source_hash. Only once that has
        # settled do two analyses share a hash, which is what triggers the bug.
        legacy_main.analyze_bank_budget(db=db, current_user=user)
        legacy_main.analyze_bank_budget(db=db, current_user=user)
        settled = _run_ids(db, tenant_a["tenant_id"])

        # Same inputs as the previous run. The poisoned run is not served as a
        # cache, so this recomputes and previously collided on source_hash.
        result = legacy_main.analyze_bank_budget(db=db, current_user=user)
        after_repeat = _run_ids(db, tenant_a["tenant_id"])

        replaced = (
            db.query(BankBudgetAnalysisRun)
            .filter(BankBudgetAnalysisRun.tenant_id == tenant_a["tenant_id"])
            .order_by(BankBudgetAnalysisRun.updated_at.desc())
            .first()
        )
        tx_rows = (
            db.query(BankBudgetAnalysisTx)
            .filter(BankBudgetAnalysisTx.run_id == replaced.id)
            .count()
        )
    finally:
        db.close()

    assert result["transactions"], "the repeated analysis returned nothing"
    assert after_repeat == settled, "a duplicate run row was inserted"
    assert tx_rows == len(result["transactions"]), "run rows were duplicated instead of replaced"


def test_a_healthy_analysis_is_served_from_cache_without_a_new_run(client, tenant_a, monkeypatch):
    import app.legacy_main as legacy_main
    from app.db import SessionLocal
    from app.models import BankTransaction, User

    monkeypatch.setattr(
        legacy_main,
        "analyze_budget_transactions_with_llm",
        lambda **kw: {"summary_points": ["alles ok"], "transaction_categories": []},
    )

    db = SessionLocal()
    try:
        account = legacy_main._get_or_create_csv_import_account(db, tenant_a["tenant_id"])
        db.add(
            BankTransaction(
                tenant_id=tenant_a["tenant_id"],
                bank_account_id=account.id,
                external_transaction_id="healthy-1",
                booking_date="2025-07-04",
                amount=-9.0,
                currency="EUR",
                counterparty_name="Onbekende partij",
                remittance_information="",
            )
        )
        db.commit()
        user = db.query(User).filter(User.id == tenant_a["user_id"]).first()

        legacy_main.analyze_bank_budget(db=db, current_user=user)
        after_first = _run_ids(db, tenant_a["tenant_id"])
        legacy_main.analyze_bank_budget(db=db, current_user=user)
        after_second = _run_ids(db, tenant_a["tenant_id"])
    finally:
        db.close()

    assert after_second == after_first


def test_a_poisoned_run_heals_once_the_provider_works_again(client, tenant_a, monkeypatch):
    import app.legacy_main as legacy_main
    from app.db import SessionLocal
    from app.models import BankBudgetAnalysisRun, BankTransaction, User

    db = SessionLocal()
    try:
        account = legacy_main._get_or_create_csv_import_account(db, tenant_a["tenant_id"])
        db.add(
            BankTransaction(
                tenant_id=tenant_a["tenant_id"],
                bank_account_id=account.id,
                external_transaction_id="healing-1",
                booking_date="2025-08-05",
                amount=-3.5,
                currency="EUR",
                counterparty_name="Onbekende partij",
                remittance_information="",
            )
        )
        db.commit()
        user = db.query(User).filter(User.id == tenant_a["user_id"]).first()

        monkeypatch.setattr(
            legacy_main, "analyze_budget_transactions_with_llm", lambda **kw: FAILED_SUMMARY
        )
        legacy_main.analyze_bank_budget(db=db, current_user=user)

        monkeypatch.setattr(
            legacy_main,
            "analyze_budget_transactions_with_llm",
            lambda **kw: {"summary_points": ["provider is terug"], "transaction_categories": []},
        )
        legacy_main.analyze_bank_budget(db=db, current_user=user)

        healed = (
            db.query(BankBudgetAnalysisRun)
            .filter(BankBudgetAnalysisRun.tenant_id == tenant_a["tenant_id"])
            .order_by(BankBudgetAnalysisRun.updated_at.desc())
            .first()
        )
    finally:
        db.close()

    assert "fallback actief" not in str(healed.summary_json).lower()
