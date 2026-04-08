"""Configuracion centralizada de logging para powerCaldera."""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

DEFAULT_LOG_DIR = Path.home() / ".powercaldera"
DEFAULT_LOG_FILE = "powercaldera.log"
MAX_BYTES = 5 * 1024 * 1024  # 5 MB
BACKUP_COUNT = 3
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"


def setup_logging(
    level: str = "INFO",
    log_dir: Path | None = None,
) -> None:
    """Configura logging con archivo rotativo y stderr.

    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR).
        log_dir: Directorio para el archivo de log.
                 Default: ~/.powercaldera/
    """
    log_dir = log_dir or DEFAULT_LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / DEFAULT_LOG_FILE

    numeric_level = getattr(logging, level.upper(), logging.INFO)

    root = logging.getLogger("powercaldera")
    root.handlers.clear()
    root.setLevel(numeric_level)

    # Archivo rotativo
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(file_handler)

    # stderr solo para WARNING+ (errores pre-TUI)
    stderr_handler = logging.StreamHandler()
    stderr_handler.setLevel(logging.WARNING)
    stderr_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    root.addHandler(stderr_handler)
