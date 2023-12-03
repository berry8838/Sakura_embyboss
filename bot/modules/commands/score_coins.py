"""
对用户分数调整
score +-

对用户sakura_b币调整
coins +-
"""
import asyncio

from pyrogram import filters
from pyrogram.errors import BadRequest
from bot import bot, prefixes, LOGGER, sakura_b
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import sendMessage, deleteMessage
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby
from bot.func_helper.fix_bottons import group_f


async def get_user_input(msg):
    if msg.reply_to_message is None:
        try:
            uid = int(msg.command[1])
            b = int(msg.command[2])
            first = await bot.get_chat(uid)
        except (IndexError, KeyError, BadRequest, ValueError):
            await deleteMessage(msg)
            return None, None, None
    else:
        try:
            uid = msg.reply_to_message.from_user.id
            b = int(msg.command[1])
            first = await bot.get_chat(uid)
        except (IndexError, ValueError):
            await deleteMessage(msg)
            return None, None, None
    return uid, b, first


@bot.on_message(filters.command('score', prefixes=prefixes) & admins_on_filter)
async def score_user(_, msg):
    uid, b, first = await get_user_input(msg)
    if not first:
        return await sendMessage(msg,
                                 "🔔 **使用格式：**[命令符]score [id] [加减分数]\n\n或回复某人[命令符]score [+/-分数] 请确认tg_id输入正确",
                                 timer=60)
    e = sql_get_emby(tg=uid)
    if not e:
        return await sendMessage(msg, f"数据库中没有[ta](tg://user?id={uid}) 。请先私聊我", buttons=group_f)

    us = e.us + b
    if sql_update_emby(Emby.tg == uid, us=us):
        await asyncio.gather(sendMessage(msg,
                                         f"· 🎯管理员 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 调节了 [{first.first_name}](tg://user?id={uid}) 积分： {b}"
                                         f"\n· 🎟️ 实时积分: **{us}**"),
                             msg.delete())
        LOGGER.info(f"【admin】[积分]：管理员 {msg.from_user.first_name} 对 {first.first_name}-{uid}  {b}分  ")
    else:
        await sendMessage(msg, '⚠️ 数据库操作失败，请检查')
        LOGGER.info(f"【admin】[积分]：管理员 {msg.from_user.first_name} 对 {first.first_name}-{uid} 数据操作失败")


@bot.on_message(filters.command('coins', prefixes=prefixes) & admins_on_filter)
async def coins_user(_, msg):
    uid, b, first = await get_user_input(msg)
    if not first:
        return await sendMessage(msg,
                                 "🔔 **使用格式：**[命令符]coins [id] [+/-币]\n\n或回复某人[命令符]coins [+/-币] 请确认tg_id输入正确",
                                 timer=60)

    e = sql_get_emby(tg=uid)
    if not e:
        return await sendMessage(msg, f"数据库中没有[ta](tg://user?id={uid}) 。请先私聊我", buttons=group_f)

    us = e.iv + b
    if sql_update_emby(Emby.tg == uid, iv=us):
        await asyncio.gather(sendMessage(msg,
                                         f"· 🎯管理员 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 调节了 [{first.first_name}](tg://user?id={uid}) {sakura_b}： {b}"
                                         f"\n· 🎟️ 实时{sakura_b}: **{us}**"),
                             msg.delete())
        LOGGER.info(
            f"【admin】[{sakura_b}]- 管理员 {msg.from_user.first_name} 对 {first.first_name}-{uid}  {b}{sakura_b}")
    else:
        await sendMessage(msg, '⚠️ 数据库操作失败，请检查')
        LOGGER.info(f"【admin】[{sakura_b}]：管理员 {msg.from_user.first_name} 对 {first.first_name}-{uid} 数据操作失败")
