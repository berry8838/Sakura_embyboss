# 重启
import os
import threading
from pyrogram import filters
from bot import bot, prefixes, LOGGER, schedall, save_config
from bot.func_helper.filters import admins_on_filter
from pyrogram.errors import BadRequest


# 定义一个检查函数
def check_restart():
    if schedall['restart_chat_id'] != 0:
        chat_id, msg_id = schedall['restart_chat_id'], schedall['restart_msg_id']
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text='Restarted Successfully!')
        except BadRequest:
            bot.send_message(chat_id=chat_id, text='Restarted Successfully!')
        LOGGER.info(f"目标：{chat_id} 消息id：{msg_id} 已提示重启成功")
        schedall.update({"restart_chat_id": 0, "restart_msg_id": 0})
        save_config()

    else:
        LOGGER.info("未检索到有重启指令，直接启动")


timer = threading.Timer(3, check_restart)
timer.start()  # 重启


@bot.on_message(filters.command('restart', prefixes) & admins_on_filter)
async def restart_bot(_, msg):
    await msg.delete()
    send = await msg.reply("Restarting，等待几秒钟。")
    schedall.update({"restart_chat_id": int(send.chat.id), "restart_msg_id": int(send.id)})
    save_config()
    try:
        # some code here
        LOGGER.info("重启")
        os.execl('/bin/systemctl', 'systemctl', 'restart', 'embyboss')  # 用当前进程执行systemctl命令，重启embyboss服务
    except FileNotFoundError:
        exit(1)
