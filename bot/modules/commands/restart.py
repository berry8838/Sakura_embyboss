# 重启
import os

from pyrogram import filters

from bot import bot, prefixes, owner, LOGGER


@bot.on_message(filters.command('restart', prefixes) & filters.user(owner))
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
