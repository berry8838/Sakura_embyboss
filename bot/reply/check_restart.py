from pyrogram.errors import BadRequest
import threading
import os
import logging

from config import bot


# 定义一个检查函数
def check_restart():
    # 使用 os.path.isfile 来检查文件是否存在
    if os.path.isfile('.restartmsg'):
        # 使用 open 来打开文件，并使用 with 语句来管理文件对象
        with open(".restartmsg") as f:
            try:
                # 读取文件的一行内容
                line = f.readline()
                # 将字符串分割为列表，并转换为整数
                chat_id, msg_id = [int(x) for x in line.split()]
                f.close()
                try:
                    bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text='Restarted Successfully!')
                except BadRequest:
                    pass
                os.remove(".restartmsg")  # 使用 os.remove 来删除文件
                logging.info(f"————目标：{chat_id} 消息id：{msg_id} 已提示重启成功————")
            # 捕获可能的异常
            except (ValueError, UnicodeDecodeError) as e:
                # 打印错误信息
                print(f"Invalid file content: {e}")
    # 如果文件不存在
    else:
        logging.info("————未检索到有重启指令，直接启动————")


timer = threading.Timer(3, check_restart)
timer.start()  # 重启
