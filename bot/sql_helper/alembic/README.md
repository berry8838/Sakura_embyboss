## 数据库自动迁移（Alembic）

- 项目已接入 Alembic，程序启动时会自动执行 `upgrade head`，将数据库升级到最新版本。
- 迁移入口在 `bot/sql_helper/__init__.py`，配置文件在 `alembic.ini`，迁移脚本目录在 `bot/sql_helper/alembic/versions`。
- 首个迁移脚本会初始化当前所有业务表，并对 `emby` 等历史已存在表执行字符集统一（`utf8mb4_unicode_ci`）。

### 使用方式

- 安装依赖：`pip install -r requirements.txt`
- 启动程序：`python main.py`（启动时自动迁移，无需手动执行）

### 后续字段变更流程

- 修改 SQLAlchemy 模型后，新增一个迁移脚本到 `bot/sql_helper/alembic/versions`。
- 推荐命名方式：`YYYYMMDD_xx_xxx.py`（例如：`20260315_02_add_xxx.py`）。
- 可选：使用命令生成迁移骨架 `alembic -c alembic.ini revision -m "your message"`。
- 启动程序后会自动把该迁移应用到数据库。

> 说明：自动迁移到“最新版本”是指自动执行已编写的迁移脚本；字段变更后仍需要新增对应迁移脚本。
