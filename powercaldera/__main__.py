"""Entry point: python -m powercaldera"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from .config import Config, DEFAULT_CONFIG_PATH
from .logging import setup_logging
from .app import PowerCalderaApp

logger = logging.getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="powerCaldera — TUI para MITRE Caldera"
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help=f"Ruta al archivo de configuración (default: {DEFAULT_CONFIG_PATH})",
    )
    parser.add_argument(
        "--server", "-s",
        type=str,
        default=None,
        help="URL del servidor Caldera (override)",
    )
    parser.add_argument(
        "--key", "-k",
        type=str,
        default=None,
        help="API key de Caldera (override)",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default=None,
        help="Nivel de logging (default: INFO)",
    )
    args = parser.parse_args()

    config = Config.load(args.config)
    if args.server:
        config.server_url = args.server
    if args.key:
        config.api_key = args.key
    if args.log_level:
        config.log_level = args.log_level

    setup_logging(level=config.log_level)
    logger.info("powerCaldera v0.1.0 — server=%s", config.server_url)

    app = PowerCalderaApp(config=config)
    app.run()


if __name__ == "__main__":
    main()
