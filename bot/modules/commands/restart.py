# 重启
import os

from pyrogram import filters

from bot import bot, prefixes, LOGGER
from bot.func_helper.filters import admins_on_filter


@bot.on_message(filters.command('restart', prefixes) & admins_on_filter)
async def restart_bot(_, msg):
    send = await msg.reply("Restarting，等待几秒钟。")
    with open(".restartmsg", "w") as f:
        f.write(f"{msg.chat.id} {send.id}\n")
        f.close()
    try:
        # some code here
        LOGGER.info("————重启————")
        os.execl('/bin/systemctl', 'systemctl', 'restart', 'embyboss')  # 用当前进程执行systemctl命令，重启embyboss服务
    except FileNotFoundError:
        exit(1)
