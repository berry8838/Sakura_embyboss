"""init schema and normalize tables charset

Revision ID: 20260315_01
Revises:
Create Date: 2026-03-15 12:00:00
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260315_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 基础业务表
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS `emby` (
          `tg` BIGINT NOT NULL,
          `embyid` VARCHAR(255) NULL,
          `name` VARCHAR(255) NULL,
          `pwd` VARCHAR(255) NULL,
          `pwd2` VARCHAR(255) NULL,
          `lv` VARCHAR(1) NULL,
          `cr` DATETIME NULL,
          `ex` DATETIME NULL,
          `us` INT NULL,
          `iv` INT NULL,
          `ch` DATETIME NULL,
          PRIMARY KEY (`tg`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS `emby2` (
          `embyid` VARCHAR(255) NOT NULL,
          `name` VARCHAR(255) NULL,
          `pwd` VARCHAR(255) NULL,
          `pwd2` VARCHAR(255) NULL,
          `lv` VARCHAR(1) NULL,
          `cr` DATETIME NULL,
          `ex` DATETIME NULL,
          `expired` INT NULL,
          PRIMARY KEY (`embyid`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS `Rcode` (
          `code` VARCHAR(50) NOT NULL,
          `tg` BIGINT NULL,
          `us` INT NULL,
          `used` BIGINT NULL,
          `usedtime` DATETIME NULL,
          PRIMARY KEY (`code`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS `request_records` (
          `download_id` VARCHAR(255) NOT NULL,
          `tg` BIGINT NOT NULL,
          `request_name` VARCHAR(255) NOT NULL,
          `cost` VARCHAR(255) NOT NULL,
          `detail` TEXT NOT NULL,
          `left_time` VARCHAR(255) NULL,
          `download_state` VARCHAR(50) NULL,
          `transfer_state` VARCHAR(50) NULL,
          `progress` FLOAT NULL,
          `create_at` DATETIME NULL,
          `update_at` DATETIME NULL,
          PRIMARY KEY (`download_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS `emby_favorites` (
          `id` INT NOT NULL AUTO_INCREMENT,
          `embyid` VARCHAR(64) NOT NULL,
          `embyname` VARCHAR(128) NOT NULL,
          `item_id` VARCHAR(64) NOT NULL,
          `item_name` VARCHAR(256) NOT NULL,
          `created_at` DATETIME NULL,
          PRIMARY KEY (`id`),
          CONSTRAINT `uix_emby_item` UNIQUE (`embyid`, `item_id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS `partition_codes` (
          `code` VARCHAR(50) NOT NULL,
          `partition` VARCHAR(64) NOT NULL,
          `duration_days` INT NOT NULL,
          `created_by` BIGINT NULL,
          `created_at` DATETIME NULL,
          PRIMARY KEY (`code`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS `partition_grants` (
          `id` INT NOT NULL AUTO_INCREMENT,
          `tg` BIGINT NOT NULL,
          `embyid` VARCHAR(255) NULL,
          `partition` VARCHAR(64) NOT NULL,
          `expires_at` DATETIME NOT NULL,
          `status` VARCHAR(20) NULL,
          `code` VARCHAR(50) NULL,
          `created_at` DATETIME NULL,
          `updated_at` DATETIME NULL,
          PRIMARY KEY (`id`),
          KEY `ix_partition_grants_tg` (`tg`),
          KEY `ix_partition_grants_status` (`status`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """
    )

    # 对历史已存在表执行字符集统一。
    op.execute("ALTER TABLE `emby` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    op.execute("ALTER TABLE `emby2` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    op.execute("ALTER TABLE `Rcode` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    op.execute("ALTER TABLE `request_records` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    op.execute("ALTER TABLE `emby_favorites` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    op.execute("ALTER TABLE `partition_codes` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    op.execute("ALTER TABLE `partition_grants` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS `partition_grants`;")
    op.execute("DROP TABLE IF EXISTS `partition_codes`;")
    op.execute("DROP TABLE IF EXISTS `emby_favorites`;")
    op.execute("DROP TABLE IF EXISTS `request_records`;")
    op.execute("DROP TABLE IF EXISTS `Rcode`;")
    op.execute("DROP TABLE IF EXISTS `emby2`;")
    op.execute("DROP TABLE IF EXISTS `emby`;")
