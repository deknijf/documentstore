__all__ = ["__version__", "__db_schema_version__"]

# App semantic version (aligned with git tags like v0.4.2).
__version__ = "0.4.2"

# Database schema version (integer, increment only when DB schema/migration logic changes).
# This is stored in the DB to support safe upgrades.
__db_schema_version__ = 1

