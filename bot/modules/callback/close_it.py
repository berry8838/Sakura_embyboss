#! /usr/bin/python3
from pyrogram import filters

from bot import bot
from bot.func_helper.msg_utils import callAnswer, deleteMessage
from bot.func_helper.utils import judge_admins


# 使用装饰器语法来定义回调函数，并传递 client 和 call 参数
@bot.on_callback_query(filters.regex('closeit'))
async def close_it(_, call):
    if str(call.message.chat.type) == "ChatType.PRIVATE":
        await deleteMessage(call)
    else:
        # 只有管理员才能删除消息，并且只能删除自己发送的消息
        if judge_admins(call.from_user.id):
            await deleteMessage(call)
        else:
            await callAnswer(call, '⚠️ 请不要以下犯上，ok？', True)
