from fastapi import APIRouter

from app import legacy_main

router = APIRouter()


# Keep handler signature exactly as before (auth/tenant checks happen inside).
router.add_api_route(
    "/api/jobs/{job_id}",
    legacy_main.get_async_job_status,
    methods=["GET"],
)

