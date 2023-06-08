"""
对用户分数调整
"""

import logging
from pyrogram.errors import BadRequest
from _mysql import sqlhelper
from config import *


@bot.on_message(filters.command('score', prefixes=prefixes))
async def score_user(_, msg):
    await msg.delete()
    a = judge_user(msg.from_user.id)
    if a == 1:
        await msg.reply("🚨 **这不是你能使用的！**")
    if a == 3:
        if msg.reply_to_message is None:
            try:
                b = int(msg.text.split()[1])
                c = int(msg.text.split()[2])
                first = await bot.get_chat(b)
                # print(c)
            except (IndexError, KeyError, BadRequest):
                send = await msg.reply(
                    "🔔 **使用格式为：**[命令符]score [id] [加减分数]\n\n或回复某人[命令符]score [+/-分数] 请再次确认tg_id输入正确")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            else:
                sqlhelper.update_one("update emby set us=us+%s where tg=%s", [c, b])
                us = sqlhelper.select_one("select us from emby where tg =%s", b)[0]
                send = await msg.reply(
                    f"· 🎯管理员 {msg.from_user.first_name} 调节了 [{first.first_name}](tg://user?id={b}) 积分： {c}"
                    f"\n· 🎟️ 实时积分: **{us}**")
                logging.info(f"【admin】[积分]：{msg.from_user.first_name} 对 {first.first_name}-{b}  {c}分  ")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            try:
                uid = msg.reply_to_message.from_user.id
                first = await bot.get_chat(uid)
                b = int(msg.text.split()[1])
                # print(c)
            except IndexError:
                send = await msg.reply(
                    "🔔 **使用格式为：**[命令符]score [id] [加减分数]\n\n或回复某人[命令符]score [+/-分数]")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))
            else:
                sqlhelper.update_one("update emby set us=us+%s where tg=%s", [b, uid])
                us = sqlhelper.select_one("select us from emby where tg =%s", uid)[0]
                send = await msg.reply(
                    f"· 🎯管理员 {msg.from_user.first_name} 调节了 [{first.first_name}](tg://user?id={uid}) 积分： {b}"
                    f"\n· 🎟️ 实时积分: **{us}**")
                logging.info(f"【admin】[积分]：{msg.from_user.first_name} 对 {first.first_name}-{uid}  {b}分  ")
                asyncio.create_task(send_msg_delete(send.chat.id, send.id))
