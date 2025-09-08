"""Utility script to run migrations on startup (used by Docker entrypoint)."""
from alembic import command
from alembic.config import Config
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger(__name__)

def run_migrations():
    cfg = Config(str(Path(__file__).parent / "alembic.ini"))
    command.upgrade(cfg, "head")

if __name__ == "__main__":
    run_migrations()
    logger.info("Migrations applied.")
