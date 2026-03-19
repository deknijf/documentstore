import os

__all__ = ["__version__", "__db_schema_version__"]

# App semantic version. Prefer runtime env so containers, git tags and the Android
# APK can all derive from the same release version, with a safe fallback for local
# development and source distribution.
__version__ = str(os.getenv("APP_VERSION") or os.getenv("VERSION") or "0.6.6").strip() or "0.6.6"

# Database schema version (integer, increment only when DB schema/migration logic changes).
# This is stored in the DB to support safe upgrades.
__db_schema_version__ = 3
