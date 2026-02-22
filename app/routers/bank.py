from fastapi import APIRouter

from app import legacy_main

router = APIRouter()

# Accounts / XS2A (admin-only enforced inside legacy handlers)
router.add_api_route("/api/bank/accounts", legacy_main.list_bank_accounts, methods=["GET"])
router.add_api_route("/api/bank/accounts", legacy_main.create_bank_account, methods=["POST"])
router.add_api_route("/api/bank/accounts/{account_id}", legacy_main.delete_bank_account, methods=["DELETE"])
router.add_api_route("/api/bank/sync-accounts", legacy_main.sync_bank_accounts, methods=["POST"])
router.add_api_route("/api/bank/accounts/{account_id}/transactions", legacy_main.list_bank_transactions, methods=["GET"])
router.add_api_route("/api/bank/accounts/{account_id}/sync-transactions", legacy_main.sync_bank_transactions, methods=["POST"])
router.add_api_route("/api/bank/accounts/{account_id}/import-transactions", legacy_main.import_bank_transactions, methods=["POST"])

# CSV import (admin-only enforced inside legacy handlers)
router.add_api_route("/api/bank/import-csv", legacy_main.import_bank_csv, methods=["POST"])
router.add_api_route("/api/bank/import-csv/files", legacy_main.list_bank_csv_files, methods=["GET"])
router.add_api_route("/api/bank/import-csv/files/{import_id}", legacy_main.delete_bank_csv_file, methods=["DELETE"])
router.add_api_route("/api/bank/import-csv/mark-parsed", legacy_main.mark_bank_csv_as_parsed, methods=["POST"])
router.add_api_route("/api/bank/import-csv/transactions", legacy_main.list_bank_csv_transactions, methods=["GET"])

# Budget (view for all users; admin-only endpoints enforced inside legacy handlers where needed)
router.add_api_route("/api/bank/budget/analyze", legacy_main.analyze_bank_budget, methods=["POST"])
router.add_api_route("/api/bank/budget/analyze/start", legacy_main.start_analyze_bank_budget, methods=["POST"])
router.add_api_route("/api/bank/budget/analyze/progress", legacy_main.get_budget_analyze_progress, methods=["GET"])
router.add_api_route("/api/bank/budget/latest", legacy_main.get_latest_bank_budget_analysis, methods=["GET"])
router.add_api_route("/api/bank/budget/refresh", legacy_main.refresh_bank_budget_from_mappings, methods=["POST"])
router.add_api_route("/api/bank/budget/quick-map", legacy_main.quick_map_budget_category, methods=["POST"])
