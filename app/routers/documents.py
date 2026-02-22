from fastapi import APIRouter

from app import legacy_main

router = APIRouter()

# Documents list/upload/trash
router.add_api_route("/api/documents", legacy_main.upload_document, methods=["POST"])
router.add_api_route("/api/documents", legacy_main.list_documents, methods=["GET"])
router.add_api_route("/api/documents/trash", legacy_main.list_deleted_documents, methods=["GET"])
router.add_api_route("/api/documents/delete", legacy_main.soft_delete_documents, methods=["POST"])
router.add_api_route("/api/documents/restore", legacy_main.restore_documents, methods=["POST"])
router.add_api_route("/api/documents/check-bank", legacy_main.check_documents_against_bank_csv, methods=["POST"])
router.add_api_route("/api/documents/check-bank/start", legacy_main.start_check_documents_against_bank_csv, methods=["POST"])

# Document detail
router.add_api_route("/api/documents/{document_id}", legacy_main.get_document, methods=["GET"])
router.add_api_route("/api/documents/{document_id}", legacy_main.update_document, methods=["PUT"])
router.add_api_route("/api/documents/{document_id}/reprocess", legacy_main.reprocess_document, methods=["POST"])
router.add_api_route("/api/documents/{document_id}/labels", legacy_main.set_document_labels, methods=["PUT"])

# Direct file download
router.add_api_route("/files/{document_id}", legacy_main.download_original, methods=["GET"])
