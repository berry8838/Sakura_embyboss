# 重启
from bot import bot, LOGGER, schedall, save_config
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
