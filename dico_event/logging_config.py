from loguru import logger
import sys
import os

# Folder logs
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Hapus handler default
logger.remove()

# Format log sesuai pedoman
log_format = (
    "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | "
    "{name}:{function}:{line} - {message}"
)

# Console logging (tetap semua INFO ke atas)
logger.add(
    sys.stdout,
    level="INFO",
    colorize=True,
    format=log_format,
)

# File logging untuk INFO & WARNING saja (application.log)
logger.add(
    os.path.join(LOG_DIR, "application.log"),
    level="INFO",
    rotation="1 day",       # Rotate setiap 1 hari
    retention="7 days",     # Simpan max 7 hari
    encoding="utf-8",
    format=log_format,
    filter=lambda record: record["level"].name in ("INFO", "WARNING"),
)

# File logging khusus ERROR & CRITICAL (error.log)
logger.add(
    os.path.join(LOG_DIR, "error.log"),
    level="ERROR",
    rotation="1 day",
    retention="14 days",
    encoding="utf-8",
    format=log_format,
)