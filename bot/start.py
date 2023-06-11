"""
启动面板start命令
"""

import asyncio
from pyrogram import filters
from pyrogram.errors import BadRequest

from bot.func import emby
from config import bot, prefixes, BOT_NAME, photo, judge_group_ikb, group, send_msg_delete, judge_user, judge_start_ikb, \
    judge_user_in_group


@bot.on_message((filters.command('start', prefixes) | filters.command('exchange', prefixes)) & filters.chat(group))
async def gun_sb(_, msg):
    await msg.delete()
    send = await msg.reply(f"🤖 看不懂是私聊命令吗？去私聊。@{BOT_NAME}")
    asyncio.create_task(send_msg_delete(send.chat.id, send.id))


# 开启面板
@bot.on_message(filters.command('start', prefixes) & filters.private)
async def _start(_, msg):
    welcome = f"**✨ 只有你想见我的时候我们的相遇才有意义**\n\n💫 __你好鸭__  [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) "
    if judge_user(msg.from_user.id) == 3:
        gm_menu = judge_start_ikb(3)
        await bot.send_photo(chat_id=msg.from_user.id,
                             photo=photo,
                             caption=welcome,
                             reply_markup=gm_menu)
        await emby.start_user(msg.from_user.id, 0)
    elif judge_user(msg.from_user.id) == 1:
        if await judge_user_in_group(msg.from_user.id) is True:
            start_ikb = judge_start_ikb(1)
            await bot.send_photo(chat_id=msg.from_user.id,
                                 photo=photo,
                                 caption=welcome,
                                 reply_markup=start_ikb)
            await emby.start_user(msg.from_user.id, 0)
        else:
            await msg.reply('💢 拜托啦！请先点击下面加入我们的群组和频道，然后再 /start 一下好吗？',
                            reply_markup=judge_group_ikb)
    await msg.delete()


@bot.on_callback_query(filters.regex('back_start'))
async def start(_, call):
    welcome = f"**✨ 只有你想见我的时候我们的相遇才有意义**\n\n💫 __你好鸭__  [{call.from_user.first_name}](tg://user?id={call.from_user.id}) "
    if judge_user(call.from_user.id) == 3:
        gm_menu = judge_start_ikb(3)
        try:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption=welcome,
                                           reply_markup=gm_menu)
        except BadRequest:
            await call.message.reply("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai")
    else:
        start_ikb = judge_start_ikb(1)
        try:
            await bot.edit_message_caption(call.from_user.id,
                                           call.message.id,
                                           caption=welcome,
                                           reply_markup=start_ikb)
        except BadRequest:
            await call.message.reply("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai")
