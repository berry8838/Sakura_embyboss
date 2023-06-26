"""
启动面板start命令
"""

import asyncio
from pyrogram import filters
from pyrogram.errors import BadRequest, Forbidden
from pyromod.helpers import ikb

from bot.reply import emby
from config import bot, prefixes, BOT_NAME, photo, judge_group_ikb, group, send_msg_delete, judge_user, judge_start_ikb, \
    judge_user_in_group
from bot.reply.query import get_bot_wlc

# 定义一个全局变量来保存blc的值
global_blc = None


# 定义一个异步函数，每分钟执行一次get_bot_wlc()函数，并更新全局变量
async def update_blc():
    global global_blc  # 使用全局变量
    while True:
        # 等待get_bot_wlc()函数的结果，并赋值给global_blc
        global_blc = get_bot_wlc()
        # 等待一分钟
        await asyncio.sleep(60)


# 使用loop.call_later来延迟执行协程函数
loop = asyncio.get_event_loop()
loop.call_later(3, lambda: loop.create_task(update_blc()))  # 初始化命令


@bot.on_message((filters.command('start', prefixes) | filters.command('exchange', prefixes)) & filters.chat(group))
async def gun_sb(_, msg):
    try:
        await msg.delete()
    except Forbidden:
        await msg.reply("🚫 请先给我删除消息的权限~")
    send = await msg.reply(f"🤖 亲爱的 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 这是一条私聊命令",
                           reply_markup=ikb([[('点击我 ༼ つ ◕_◕ ༽つ', f't.me/{BOT_NAME}', 'url')]]))
    asyncio.create_task(send_msg_delete(send.chat.id, send.id))


# 开启面板
@bot.on_message(filters.command('start', prefixes) & filters.private)
async def _start(_, msg):
    bot_wlc = global_blc
    welcome = f"{bot_wlc}\n\n🍉__你好鸭 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id}) 请选择功能__👇"
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
    await call.answer("💫 初始面板")
    bot_wlc = global_blc
    welcome = f"{bot_wlc}\n\n🍉__你好鸭 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 请选择功能__👇"
    if judge_user(call.from_user.id) == 3:
        gm_menu = judge_start_ikb(3)
        try:
            await call.message.delete()
            await bot.send_photo(call.from_user.id,
                                 photo=photo,
                                 caption=welcome,
                                 reply_markup=gm_menu)
        except BadRequest:
            await call.message.reply("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
        except Forbidden:
            await call.answer("Forbidden - 时间太久远，请重新召唤面板！", show_alert=True)
    else:
        start_ikb = judge_start_ikb(1)
        try:
            await call.message.delete()
            await bot.send_photo(call.from_user.id,
                                 photo=photo,
                                 caption=welcome,
                                 reply_markup=start_ikb)
        except BadRequest:
            await call.message.reply("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
        except Forbidden:
            await call.answer("Forbidden - 时间太久远，请重新召唤面板！", show_alert=True)
