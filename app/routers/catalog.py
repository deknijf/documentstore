from fastapi import APIRouter

from app import legacy_main

router = APIRouter()

router.add_api_route("/api/groups", legacy_main.my_groups, methods=["GET"])

router.add_api_route("/api/categories", legacy_main.list_categories, methods=["GET"])
router.add_api_route("/api/categories", legacy_main.create_category, methods=["POST"])
router.add_api_route("/api/categories/{category_name}", legacy_main.update_category, methods=["PUT"])
router.add_api_route("/api/categories/{category_name}", legacy_main.delete_category, methods=["DELETE"])

router.add_api_route("/api/labels", legacy_main.list_labels, methods=["GET"])
router.add_api_route("/api/labels", legacy_main.create_label, methods=["POST"])
