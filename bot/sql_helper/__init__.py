"""
初始化数据库
"""
import os
import importlib
from pathlib import Path

from bot import db_host, db_user, db_pwd, db_name, db_port
from bot import LOGGER
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

# 创建engine对象
DATABASE_URL = f"mysql+pymysql://{db_user}:{db_pwd}@{db_host}:{db_port}/{db_name}?charset=utf8mb4"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    echo_pool=False,
    pool_size=16,
    pool_recycle=60 * 30,
    connect_args={"init_command": "SET NAMES utf8mb4"},
)

# 创建Base对象
Base = declarative_base()
Base.metadata.bind = engine

_MIGRATION_GUARD_ENV = "SAKURA_RUNNING_MIGRATIONS"


def _legacy_create_all_tables():
    """
    在未安装 Alembic 或配置缺失时兜底建表，保证服务可启动。
    """
    from bot.sql_helper import sql_code, sql_emby, sql_emby2, sql_favorites, sql_partition, sql_request_record  # noqa: F401

    Base.metadata.create_all(bind=engine, checkfirst=True)


def run_migrations():
    """
    启动时自动执行数据库迁移到最新版本。
    """
    if os.getenv(_MIGRATION_GUARD_ENV) == "1":
        return

    alembic_ini = Path(__file__).resolve().parents[2] / "alembic.ini"
    if not alembic_ini.exists():
        LOGGER.warning(f"未找到 Alembic 配置文件，跳过自动迁移: {alembic_ini}")
        _legacy_create_all_tables()
        return

    os.environ[_MIGRATION_GUARD_ENV] = "1"
    try:
        try:
            alembic_command = importlib.import_module("alembic.command")
            alembic_config = importlib.import_module("alembic.config")
        except ImportError:
            LOGGER.warning("未安装 alembic，跳过自动迁移")
            _legacy_create_all_tables()
            return

        Config = getattr(alembic_config, "Config")
        config = Config(str(alembic_ini))
        config.set_main_option("sqlalchemy.url", DATABASE_URL)
        alembic_command.upgrade(config, "head")
        LOGGER.info("数据库迁移完成，当前已升级到最新版本")
    except Exception as e:
        LOGGER.error(f"数据库自动迁移失败: {e}")
        raise
    finally:
        os.environ.pop(_MIGRATION_GUARD_ENV, None)


# 调用sql_start()函数，返回一个Session工厂
def sql_start() -> sessionmaker:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


Session = sql_start()


run_migrations()
