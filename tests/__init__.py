# Marks tests as a package so pytest imports conftest once, as tests.conftest.
# Without this, "from tests.conftest import ..." loads a second copy of the
# module with its own temporary data directory.
