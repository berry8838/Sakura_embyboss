#! /usr/bin/python3
from pyrogram import filters
from pyrogram.enums import ChatType

from bot import bot
from bot.func_helper.msg_utils import callAnswer, deleteMessage
from bot.func_helper.utils import judge_admins


# 使用装饰器语法来定义回调函数，并传递 client 和 call 参数
@bot.on_callback_query(filters.regex('closeit'))
async def close_it(_, call):
    if call.message.chat.type is ChatType.PRIVATE:
        await deleteMessage(call)
    else:
        try:
            t = int(call.data.split('_')[1])
        except:
            pass
        else:
            if t == call.from_user.id:
                return await deleteMessage(call)
            # else:
            #     return await callAnswer(call, '此非你的专属', True)
        # 只有管理员才能删除消息，并且只能删除自己发送的消息
        if judge_admins(call.from_user.id):
            await deleteMessage(call)
        else:
            await callAnswer(call, '⚠️ 请不要以下犯上，ok？', True)
