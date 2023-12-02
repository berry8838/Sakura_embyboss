import os
from bot import bot, prefixes, owner, LOGGER, db_is_docker, db_docker_name, db_host, db_name, db_user, db_pwd, db_backup_dir, db_backup_maxcount
from pyrogram import filters
from bot.func_helper.backup_db_utils import BackupDBUtils
from bot.func_helper.msg_utils import deleteMessage

async def backup_db():
    backup_file = None
    # 如果是在docker模式下运行的此程序，使用BackupDBUtils.backup_mysql_db的方式备份数据库（此镜像中已经安装了mysqldump工具）
    if os.environ.get('DOCKER_MODE') == 1 or not db_is_docker:
        backup_file = await BackupDBUtils.backup_mysql_db(
            host=db_host,
            user=db_user,
            password=db_pwd,
            database_name=db_name,
            backup_dir=db_backup_dir,
            max_backup_count=db_backup_maxcount
        )
    elif db_is_docker:
        backup_file = await BackupDBUtils.backup_mysql_db_docker(
            container_name=db_docker_name,
            user=db_user,
            password=db_pwd,
            database_name=db_name,
            backup_dir=db_backup_dir,
            max_backup_count=db_backup_maxcount
        )
    return backup_file
async def auto_backup_db():
    LOGGER.info("BOT数据库备份开始")
    backup_file = await backup_db()
    if backup_file is not None:
        LOGGER.info(f'BOT数据库备份完毕')
        try:
            await bot.send_document(
                chat_id=owner,
                document=backup_file,
                caption=f'BOT数据库备份完毕'
            )
        except Exception as e:
            LOGGER.info(f'发送到owner失败，文件保存在本地')
    else:
        LOGGER.error(f'BOT数据库手动备份失败，请尽快检查相关配置')
# bot数据库手动备份
@bot.on_message(filters.command('backup_db', prefixes) & filters.user(owner))
async def manual_backup_db(_, msg):
    await deleteMessage(msg)
    await auto_backup_db()