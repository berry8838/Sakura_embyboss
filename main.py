#! /usr/bin/python3
# -*- coding: utf-8 -*-
import uvloop

uvloop.install()
from pyrogram.errors import BadRequest

from config import bot

import threading
import os
import logging


def main():
    from bot import admin_panel, config_panel, member_panel, mylogger, sever_panel, start
    from bot.func import exchange, expired, kk, leave_unauth_chat, admin_command, user_permission
    from bot.extra import create
    # 创建一个 Timer 对象, 对重启命令
    timer = threading.Timer(3, check_restart)
    # 启动 Timer
    timer.start()


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
                logging.info(f"目标：{chat_id}, 消息id：{msg_id} 已提示重启成功。")
            # 捕获可能的异常
            except (ValueError, UnicodeDecodeError) as e:
                # 打印错误信息
                print(f"Invalid file content: {e}")
    # 如果文件不存在
    else:
        pass


bot.run(main())
