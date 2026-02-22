from fastapi import APIRouter

from app import legacy_main

router = APIRouter()

router.add_api_route("/api/search", legacy_main.search_documents, methods=["GET"])

