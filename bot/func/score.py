"""
对用户分数调整
"""

import logging
from datetime import datetime, timedelta

from pyrogram.errors import BadRequest
from _mysql import sqlhelper
from bot.func import emby
from config import *


@bot.on_message(filters.command('score', prefixes=prefixes) & filters.user(admins))
async def score_user(_, msg):
    # await msg.delete()
    # a = judge_user(msg.from_user.id)
    # if a == 1:
    #     await msg.reply("🚨 **这不是你能使用的！**")
    # if a == 3:
    if msg.reply_to_message is None:
        try:
            b = int(msg.text.split()[1])
            c = int(msg.text.split()[2])
            first = await bot.get_chat(b)
            # print(c)
        except (IndexError, KeyError, BadRequest):
            send = await msg.reply(
                "🔔 **使用格式：**[命令符]score [id] [加减分数]\n\n或回复某人[命令符]score [+/-分数] 请确认tg_id输入正确")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            sqlhelper.update_one("update emby set us=us+%s where tg=%s", [c, b])
            us = sqlhelper.select_one("select us from emby where tg =%s", b)[0]
            await msg.reply(
                f"· 🎯管理员 {msg.from_user.first_name} 调节了 [{first.first_name}](tg://user?id={b}) 积分： {c}"
                f"\n· 🎟️ 实时积分: **{us}**")
            logging.info(f"【admin】[积分]：{msg.from_user.first_name} 对 {first.first_name}-{b}  {c}分  ")
    else:
        try:
            uid = msg.reply_to_message.from_user.id
            first = await bot.get_chat(uid)
            b = int(msg.text.split()[1])
            # print(c)
        except IndexError:
            send = await msg.reply(
                "🔔 **使用格式：**/score [id] [加减分数]\n\n或回复某人[命令符]score [+/-分数]")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            sqlhelper.update_one("update emby set us=us+%s where tg=%s", [b, uid])
            us = sqlhelper.select_one("select us from emby where tg =%s", uid)[0]
            await msg.reply(
                f"· 🎯管理员 {msg.from_user.first_name} 调节了 [{first.first_name}](tg://user?id={uid}) 积分： {b}"
                f"\n· 🎟️ 实时积分: **{us}**")
            logging.info(f"【admin】[积分]：{msg.from_user.first_name} 对 {first.first_name}-{uid}  {b}分  ")


@bot.on_message(filters.command('renew', prefixes) & filters.user(owner))
async def renew_user(_, msg):
    if msg.reply_to_message is None:
        try:
            b = msg.text.split()[1]  # name
            c = int(msg.text.split()[2])  # 天数
            # print(c)
        except (IndexError, KeyError, BadRequest):
            send = await msg.reply(
                "🔔 **使用格式：**/renew [emby_name] [加减天数]\n\n或回复某人 /renew [+/-天数] \nemby_name为emby账户名")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            embyid, ex = sqlhelper.select_one("select embyid,ex from emby2 where name=%s", b)
            if embyid is not None:
                ex_new = datetime.now()
                if ex_new > ex:
                    ex_new = ex_new + timedelta(days=c)
                    print(ex_new)
                    await emby.ban_user(embyid, 1)
                    await msg.reply(f'🍒 __已调整emby用户 {b} 到期时间 {c}天 (以当前时间计)。__')
                elif ex_new < ex:
                    ex_new = ex + timedelta(days=c)
                    await msg.reply(f'🍒  __已调整emby用户 {b} 到期时间 {c}天__ ')
                sqlhelper.update_one("update emby2 set ex=%s,expired=%s where name=%s", [ex_new, 0, b])
                logging.info(f"【admin】[extra]：{msg.from_user.first_name} 对 emby账户{b} 调节 {c} 天  ")
            else:
                embyid, lv, ex = sqlhelper.select_one("select embyid,lv,ex from emby where name=%s", b)
                if embyid is not None:
                    ex_new = datetime.now()
                    if ex_new > ex:
                        ex_new = ex_new + timedelta(days=c)
                        print(ex_new)
                        await msg.reply(f'🍒 __已调整emby用户 {b} 到期时间 {c}天 (以当前时间计)。__')
                    elif ex_new < ex:
                        ex_new = ex + timedelta(days=c)
                        await msg.reply(f'🍒  __已调整emby用户 {b} 到期时间 {c}天__ ')
                    if ex_new < datetime.now():
                        lv = 'c'
                        await emby.ban_user(embyid, 0)
                    if ex_new > datetime.now():
                        lv = 'b'
                        await emby.ban_user(embyid, 1)
                    sqlhelper.update_one("update emby set ex=%s,lv=%s where name=%s", [ex_new, lv, b])
                    logging.info(f"【admin】[extra]：{msg.from_user.first_name} 对 emby账户{b} 调节 {c} 天  ")
                else:
                    await msg.reply(f"♻️ 没有检索到 {b} 这个账户，请确认重试。")
    else:
        try:
            uid = msg.reply_to_message.from_user.id
            first = await bot.get_chat(uid)
            b = int(msg.text.split()[1])
            # print(c)
        except IndexError:
            send = await msg.reply(
                "🔔 **使用格式：**/renew [emby_name] [加减天数]\n\n或回复某人 /renew [+/-天数] \nemby_name为emby账户名")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            embyid, name, lv, ex = sqlhelper.select_one("select embyid,name,lv,ex from emby where tg=%s", uid)
            if embyid is not None:
                ex_new = datetime.now()
                if ex_new > ex:
                    ex_new = ex_new + timedelta(days=b)
                    await msg.reply(
                        f'🍒 __已调整用户 [{first.first_name}](tg://user?id={uid})-{name} 到期时间 {b}天 (以当前时间计)__')
                    await bot.send_message(uid,
                                           f"🎯 管理员 {msg.from_user.first_name} 调节了您的到期时间：{b}天"
                                           f"📅 实时到期：{ex_new} ")
                elif ex_new < ex:
                    ex_new = ex + timedelta(days=b)
                    await msg.reply(f'🍒  __已调整用户 {first.first_name}({uid})-{name} 到期时间 {b}天__')
                if ex_new < datetime.now():
                    lv = 'c'
                    await emby.ban_user(embyid, 0)
                if ex_new > datetime.now():
                    lv = 'b'
                    await emby.ban_user(embyid, 1)
                sqlhelper.update_one("update emby set ex=%s,lv=%s where tg=%s", [ex_new, lv, uid])
                logging.info(
                    f"【admin】[extra]：{msg.from_user.first_name} 对 {first.first_name}({uid})-{name} 用户调节到期时间 {b} 天")
            else:
                await msg.reply("💢 回复的 ta 还没有注册账户呢")
