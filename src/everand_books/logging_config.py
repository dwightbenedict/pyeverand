import json
import logging
from datetime import UTC, datetime
from typing import override

from everand_books.config import Settings


TEXT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


class JsonFormatter(logging.Formatter):
    @override
    def format(self, record: logging.LogRecord) -> str:
        created = datetime.fromtimestamp(record.created, tz=UTC)
        entry = {
            "time": created.isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry)


def configure_logging(settings: Settings) -> None:
    """Send every log record to stderr in one format. Call once, from an entry point."""
    handler = logging.StreamHandler()
    is_json = settings.log_format == "json"
    handler.setFormatter(JsonFormatter() if is_json else logging.Formatter(TEXT_FORMAT))
    logging.basicConfig(level=settings.log_level, handlers=[handler], force=True)
