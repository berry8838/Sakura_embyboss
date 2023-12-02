from bot import bot, prefixes, owner, LOGGER, db_is_docker, db_docker_name, db_host, db_name, db_user, db_pwd, db_backup_dir, db_backup_maxcount
from pyrogram import filters
from bot.func_helper.backup_db_utils import BackupDBUtils
from bot.func_helper.msg_utils import sendMessage, deleteMessage
# bot数据库手动备份
@bot.on_message(filters.command('manual_backup', prefixes) & filters.user(owner))
async def db_manual_backup(_, msg):
    await deleteMessage(msg)
    await sendMessage(msg, "👨‍💻BOT数据库手动备份开始")
    backup_file = None
    if db_is_docker:
        backup_file = await BackupDBUtils.backup_mysql_db_docker(
            container_name=db_docker_name,
            user=db_user,
            password=db_pwd,
            database_name=db_name,
            backup_dir=db_backup_dir,
            max_backup_count=db_backup_maxcount
        )
    else:
        backup_file = await BackupDBUtils.backup_mysql_db(
            host=db_host,
            user=db_user,
            password=db_pwd,
            database_name=db_name,
            backup_dir=db_backup_dir,
            max_backup_count=db_backup_maxcount
        )
    if backup_file is not None:
        try:
            await bot.send_document(
                chat_id=owner,
                document=backup_file,
                caption=f'BOT数据库备份完毕'
            )
        except Exception as e:
            await sendMessage(msg, "⚠️发送到owner失败，文件保存在本地")
        await sendMessage(msg, '👨‍💻BOT数据库手动备份完毕')
    else:
        await sendMessage(msg, '⚠️BOT数据库手动备份失败，请尽快检查相关配置')