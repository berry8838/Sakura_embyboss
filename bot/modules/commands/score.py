"""
对用户分数调整
"""

from pyrogram import filters
from pyrogram.errors import BadRequest
from bot import bot, prefixes, LOGGER
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import sendMessage, deleteMessage
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby
from bot.func_helper.fix_bottons import group_f


@bot.on_message(filters.command('score', prefixes=prefixes) & admins_on_filter)
async def score_user(_, msg):
    if msg.reply_to_message is None:
        try:
            uid = int(msg.command[1])
            b = int(msg.command[2])
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest, ValueError):
            await deleteMessage(msg)
            return await sendMessage(msg,
                                     "🔔 **使用格式：**[命令符]score [id] [加减分数]\n\n或回复某人[命令符]score [+/-分数] 请确认tg_id输入正确",
                                     timer=60)
    else:
        try:
            uid = msg.reply_to_message.from_user.id
            b = int(msg.command[1])
            first = await bot.get_chat(uid)
        except (IndexError, ValueError):
            await deleteMessage(msg)
            return await sendMessage(msg,
                                     "🔔 **使用格式：**/score [id] [加减分数]\n\n或回复某人[命令符]score [+/-分数]",
                                     timer=60)
    e = sql_get_emby(tg=uid)
    if e is None:
        return await sendMessage(msg, f"数据库中没有[ta](tg://user?id={uid}) 。请先私聊我", buttons=group_f)
    us = e.us + b
    if sql_update_emby(Emby.tg == uid, us=us):
        await sendMessage(msg,
                          f"· 🎯管理员 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 调节了 [{first.first_name}](tg://user?id={uid}) 积分： {b}"
                          f"\n· 🎟️ 实时积分: **{us}**")
        LOGGER.info(f"【admin】[积分]：管理员 {msg.from_user.first_name} 对 {first.first_name}-{uid}  {b}分  ")
    else:
        await sendMessage(msg, '⚠️ 数据库操作失败，请检查')
    await msg.delete()
