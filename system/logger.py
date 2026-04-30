import logging
import os
import sys
import threading
import traceback
from logging.handlers import TimedRotatingFileHandler
from system.constants import LOG_DIR

_configured = False

logger = logging.getLogger("groveagent")

class TracebackFormatter(logging.Formatter):
    """Formátuje exception traceback přes stdlib `traceback`. Pokud byla
    `logger.exception()` zavolána mimo `except` blok (exc_info je
    `(None, None, None)`), vrátí prázdný string místo nesmyslného
    `NoneType: None`."""

    def formatException(self, exc_info):
        if not exc_info or exc_info[0] is None:
            return ""
        return "".join(traceback.format_exception(*exc_info))


def setup_logging() -> logging.Logger:
    """Konfiguruje stdlib logging (konzole + denní rotace souboru) a globální
    exception hooky pro hlavní thread i background thready. Idempotentní —
    opakovaná volání jsou no-op."""
    global _configured
    if _configured:
        return logging.getLogger()

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = TracebackFormatter(
        fmt="%(asctime)s %(levelname)s %(filename)s:%(lineno)d — %(message)s",
    )

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)

    file_handler = TimedRotatingFileHandler(
        LOG_DIR / "app.log",
        when="midnight",
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setFormatter(formatter)

    root = logging.getLogger()
    root.setLevel(os.environ.get("LOG_LEVEL", "INFO").upper())
    root.addHandler(stream_handler)
    root.addHandler(file_handler)

    def _log_uncaught(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        root.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_tb))

    def _log_thread_exc(args):
        if issubclass(args.exc_type, SystemExit):
            return
        root.critical(
            "Thread crash in %s",
            args.thread.name,
            exc_info=(args.exc_type, args.exc_value, args.exc_traceback),
        )

    sys.excepthook = _log_uncaught
    threading.excepthook = _log_thread_exc

    _configured = True
    return root
