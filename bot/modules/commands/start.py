"""
启动面板start命令 返回面ban
"""
import asyncio
from pyrogram import filters

from bot.modules.commands.exchange import rgs_code
from bot.sql_helper.sql_emby import sql_add_emby
from bot.func_helper.filters import user_in_group_filter
from bot.func_helper.msg_utils import deleteMessage, sendMessage, sendPhoto, callAnswer
from bot.func_helper.fix_bottons import group_f, judge_start_ikb, judge_group_ikb
from bot import bot, prefixes, group, bot_photo


# 反命令提示
@bot.on_message((filters.command('start', prefixes) | filters.command('exchange', prefixes)) & filters.chat(group))
async def ui_g_command(_, msg):
    await asyncio.gather(deleteMessage(msg),
                         sendMessage(msg,
                                     f"🤖 亲爱的 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 这是一条私聊命令",
                                     buttons=group_f, timer=60))


# 私聊开启面板
@bot.on_message(filters.command('start', prefixes) & filters.private)
async def p_start(_, msg):
    if not await user_in_group_filter(_, msg):
        return await asyncio.gather(deleteMessage(msg),
                                    sendMessage(msg,
                                                '💢 拜托啦！请先点击下面加入我们的群组和频道，然后再 /start 一下好吗？',
                                                buttons=judge_group_ikb))
    try:
        u = msg.command[1]
        await msg.delete()
        return await rgs_code(_, msg)
    except IndexError:
        if await user_in_group_filter(_, msg):
            await asyncio.gather(deleteMessage(msg),
                                 sendPhoto(msg, bot_photo,
                                           f"**✨ 只有你想见我的时候我们的相遇才有意义**\n\n🍉__你好鸭 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 请选择功能__👇",
                                           buttons=judge_start_ikb(msg.from_user.id)))
            sql_add_emby(msg.from_user.id)


# 返回面板
@bot.on_callback_query(filters.regex('back_start'))
async def b_start(_, call):
    if await user_in_group_filter(_, call):
        await asyncio.gather(callAnswer(call, "⭐ 返回start"),
                             deleteMessage(call), sendPhoto(call, bot_photo,
                                                            f"**✨ 只有你想见我的时候我们的相遇才有意义**\n\n🍉__你好鸭 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 请选择功能__👇",
                                                            buttons=judge_start_ikb(
                                                                call.from_user.id)))
    elif not await user_in_group_filter(_, call):
        await asyncio.gather(callAnswer(call, "⭐ 返回start"),
                             deleteMessage(call), sendPhoto(call, bot_photo,
                                                            '💢 拜托啦！请先点击下面加入我们的群组和频道，然后再 /start 一下好吗？',
                                                            judge_group_ikb))


@bot.on_callback_query(filters.regex('store_all'))
async def store_alls(_, call):
    if not await user_in_group_filter(_, call):
        await asyncio.gather(callAnswer(call, "⭐ 返回start"),
                             deleteMessage(call), sendPhoto(call, bot_photo,
                                                            '💢 拜托啦！请先点击下面加入我们的群组和频道，然后再 /start 一下好吗？',
                                                            judge_group_ikb))
    elif await user_in_group_filter(_, call):
        await callAnswer(call, '⭕ 正在编辑', True)
