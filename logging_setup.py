import logging
import os


def configure_logging() -> None:
    """Configure root logger for structured, concise output.

    Uses INFO by default; DEBUG if JI_DEBUG env var is set.
    """
    level = logging.DEBUG if os.getenv("JI_DEBUG") else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(levelname)s %(name)s: %(message)s",
    )


