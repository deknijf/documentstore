from fastapi import APIRouter

from app import legacy_main

router = APIRouter()

# Admin endpoints: keep legacy handlers to avoid behavior changes.
router.add_api_route("/api/admin/users", legacy_main.list_users, methods=["GET"])
router.add_api_route("/api/admin/users", legacy_main.create_user, methods=["POST"])
router.add_api_route("/api/admin/users/{user_id}", legacy_main.update_user, methods=["PUT"])
router.add_api_route("/api/admin/users/{user_id}", legacy_main.delete_user, methods=["DELETE"])

router.add_api_route("/api/admin/groups", legacy_main.list_groups, methods=["GET"])
router.add_api_route("/api/admin/groups", legacy_main.create_group, methods=["POST"])
router.add_api_route("/api/admin/groups/{group_id}", legacy_main.delete_group, methods=["DELETE"])

router.add_api_route("/api/admin/integrations", legacy_main.get_integrations, methods=["GET"])
router.add_api_route("/api/admin/integrations", legacy_main.update_integrations, methods=["PUT"])
router.add_api_route("/api/admin/mail-ingest/run", legacy_main.run_mail_ingest, methods=["POST"])

router.add_api_route("/api/admin/tenants", legacy_main.list_tenants, methods=["GET"])
router.add_api_route("/api/admin/tenants", legacy_main.create_tenant, methods=["POST"])
router.add_api_route("/api/admin/tenants/{tenant_id}", legacy_main.update_tenant, methods=["PUT"])
router.add_api_route("/api/admin/tenants/{tenant_id}/users", legacy_main.list_tenant_users, methods=["GET"])
router.add_api_route("/api/admin/tenants/{tenant_id}/users/{user_id}", legacy_main.add_user_to_tenant, methods=["POST"])
router.add_api_route("/api/admin/tenants/{tenant_id}/users/{user_id}", legacy_main.remove_user_from_tenant, methods=["DELETE"])
