import json
import sys
from contextvars import ContextVar
from pathlib import Path

from loguru import logger

from app.config.config import CFG, LogCfg

LOG_DIR = Path(__file__).parent.parent / "logs"

# 请求上下文变量
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="")
trace_id_ctx: ContextVar[str] = ContextVar("trace_id", default="")
client_ip_ctx: ContextVar[str] = ContextVar("client_ip", default="")
method_ctx: ContextVar[str] = ContextVar("method", default="")
path_ctx: ContextVar[str] = ContextVar("path", default="")

# 控制台日志格式（彩色）
LOG_FORMAT_CONSOLE = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
    "<level>{level:^8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
    "<level>{message}</level>"
)


def _patch_record(record: dict) -> bool:
    """将日志记录转换为 JSON 格式并注入上下文信息"""
    log_obj = {
        "time": record["time"].strftime("%Y-%m-%d %H:%M:%S.%f")[:-3],
        "level": record["level"].name,
        "request_id": request_id_ctx.get(),
        "trace_id": trace_id_ctx.get(),
        "client_ip": client_ip_ctx.get(),
        "method": method_ctx.get(),
        "path": path_ctx.get(),
        "message": record["message"],
    }
    # 从 extra 中读取 bind 的动态字段
    extra = record.get("extra", {})
    for key, value in extra.items():
        if key != "tag":  # 排除 tag 字段
            log_obj[key] = value
    record["message"] = json.dumps(log_obj, ensure_ascii=False)
    return True


def _setup_logger(logger_instance, cfg: LogCfg, filter_func):
    """配置日志输出"""
    # 控制台输出
    if cfg.to_console:
        logger_instance.add(
            sink=sys.stdout,
            level=cfg.level,
            format=LOG_FORMAT_CONSOLE,
            colorize=True,
            catch=False,
            filter=filter_func,
            enqueue=True,
        )

    # 文件输出（JSON 格式）
    if cfg.to_file:
        (LOG_DIR / cfg.log_dir).mkdir(parents=True, exist_ok=True)
        logger_instance.add(
            sink=str(LOG_DIR / cfg.log_dir / "{time:YYYY-MM-DD}.log"),
            level=cfg.level,
            format="{message}",
            rotation=cfg.max_file_size,
            encoding="utf-8",
            catch=False,
            filter=lambda r: _patch_record(r) and filter_func(r),
            enqueue=True,
        )


logger_configured = False

app_logger = logger.bind(tag="app")
auth_logger = logger.bind(tag="auth")


def setup_logger():
    """初始化日志配置"""
    global logger_configured
    if not logger_configured:
        logger.remove()  # 移除默认的日志输出
        _setup_logger(
            app_logger,
            CFG.log.app,
            lambda record: record["extra"].get("tag") == "app",
        )
        _setup_logger(
            auth_logger,
            CFG.log.auth,
            lambda record: record["extra"].get("tag") == "auth",
        )
        logger_configured = True
