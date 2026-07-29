import logging
import sys

from app.core.settings import ApplicationSettings


def configure_application_logging(settings: ApplicationSettings) -> None:
    """Simple console logging for the ticket system."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    logging.basicConfig(
        level=log_level,
        format=(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger(__name__).info(
        "Logging ready | app=%s | env=%s | level=%s",
        settings.application_name,
        settings.application_environment,
        settings.log_level.upper(),
    )
