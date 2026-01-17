import sys
from pathlib import Path

from loguru import logger

from app.config.config import CFG

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level:^8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def _setup_logger(cfg, filter_func):
    if cfg.to_console:
        logger.add(
            sink=sys.stdout,
            level=cfg.level,
            format=LOG_FORMAT,
            colorize=True,
            catch=False,
            filter=filter_func,
            enqueue=True,
        )
    if cfg.to_file:
        (LOG_DIR / cfg.log_dir).mkdir(parents=True, exist_ok=True)
        logger.add(
            sink=LOG_DIR / cfg.log_dir / "{time:YYYY-MM-DD}.log",
            level=cfg.level,
            format=LOG_FORMAT,
            rotation=cfg.max_file_size,
            encoding="utf-8",
            catch=False,
            filter=filter_func,
            enqueue=True,
        )


logger_configured = False


def setup_logger():
    global logger_configured
    if logger_configured:
        return
    logger.remove()
    _setup_logger(CFG.log.app, lambda record: record["extra"].get("tag") is None)
    _setup_logger(CFG.log.auth, lambda record: record["extra"].get("tag") == "auth")
    logger_configured = True


setup_logger()
auth_logger = logger.bind(tag="auth")
