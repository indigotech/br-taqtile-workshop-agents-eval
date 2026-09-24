import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.data.database import reset_database

logger = logging.getLogger(__name__)


def main() -> None:
    setup_logging()
    reset_database(settings.DATABASE_PATH)
    logger.info("Database recreated and seeded at %s", settings.DATABASE_PATH)


if __name__ == "__main__":
    main()
