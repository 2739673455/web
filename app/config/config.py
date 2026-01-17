from pathlib import Path

from omegaconf import OmegaConf
from pydantic import BaseModel

CONFIG_DIR = Path(__file__).parent


# 数据库
class DBCfg(BaseModel):
    host: str
    port: int
    user: str
    password: str
    database: str


class DBCfgs(BaseModel):
    app: DBCfg
    auth: DBCfg


# 日志
class LogCfg(BaseModel):
    level: str
    to_console: bool
    to_file: bool
    log_dir: str
    max_file_size: str


class LogCfgs(BaseModel):
    app: LogCfg
    auth: LogCfg


class Cfg(BaseModel):
    db: DBCfgs
    log: LogCfgs
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    refresh_token_expire_days: int
    encryption_key: str
    port: int


base_cfg = OmegaConf.load(CONFIG_DIR / "config.yml")  # 加载
OmegaConf.resolve(base_cfg)  # 解析插值
CFG = Cfg.model_validate(base_cfg)  # 转换为配置类
