"""
对用户分数调整
"""

import logging
import os
import time
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
            await msg.delete()
            logging.info(f"【admin】[积分]：{msg.from_user.first_name} 对 {first.first_name}-{uid}  {b}分  ")


@bot.on_message(filters.command('renew', prefixes) & filters.user(admins))
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
            try:
                embyid, ex, expired = sqlhelper.select_one("select embyid,ex,expired from emby2 where name=%s", b)
                if embyid is not None:
                    ex_new = datetime.now()
                    if ex_new > ex:
                        ex_new = ex_new + timedelta(days=c)
                        await msg.reply(
                            f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c}天 (以当前时间计)__'
                            f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                    elif ex_new < ex:
                        ex_new = ex + timedelta(days=c)
                        await msg.reply(
                            f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c}天__'
                            f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                    if ex_new < datetime.now():
                        expired = 1
                        await emby.ban_user(embyid, 0)
                    if ex_new > datetime.now():
                        expired = 0
                        await emby.ban_user(embyid, 1)
                    sqlhelper.update_one("update emby2 set ex=%s,expired=%s where name=%s", [ex_new, expired, b])
                    logging.info(
                        f"【admin】[renew]：{msg.from_user.first_name} 对 emby账户{b} 调节 {c} 天, 📅 实时到期：{ex_new} ")
            except TypeError:
                try:
                    embyid, lv, ex = sqlhelper.select_one("select embyid,lv,ex from emby where name=%s", b)
                except TypeError:
                    await msg.reply(f"♻️ 没有检索到 {b} 这个账户，请确认重试。")
                else:
                    if embyid is not None:
                        ex_new = datetime.now()
                        if ex_new > ex:
                            ex_new = ex_new + timedelta(days=c)
                            # print(ex_new)
                            await msg.reply(
                                f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c} 天 (以当前时间计)__'
                                f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                        elif ex_new < ex:
                            ex_new = ex + timedelta(days=c)
                            await msg.reply(
                                f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c} 天__'
                                f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                        if ex_new < datetime.now():
                            lv = 'c'
                            await emby.ban_user(embyid, 0)
                        if ex_new > datetime.now():
                            lv = 'b'
                            await emby.ban_user(embyid, 1)
                        sqlhelper.update_one("update emby set ex=%s,lv=%s where name=%s", [ex_new, lv, b])
                        logging.info(
                            f"【admin】[renew]：{msg.from_user.first_name} 对 emby账户{b} 调节 {c} 天，"
                            f"实时到期：{ex_new.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        try:
            uid = msg.reply_to_message.from_user.id
            first = await bot.get_chat(uid)
            b = int(msg.text.split()[1])
            # print(c)
        except IndexError:
            send = await msg.reply(
                "🔔 **使用格式：**/renew [emby_name] [加减天数]\n\n或回复某人 /renew [+/-天数]\nemby_name为emby账户名")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            embyid, name, lv, ex = sqlhelper.select_one("select embyid,name,lv,ex from emby where tg=%s", uid)
            if embyid is not None:
                ex_new = datetime.now()
                if ex_new > ex:
                    ex_new = ex_new + timedelta(days=b)
                    await msg.reply(
                        f'🍒 __管理员 {msg.from_user.first_name} 已调整用户 [{first.first_name}](tg://user?id={uid}) - {name} 到期时间 {b}天 (以当前时间计)__'
                        f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                    await bot.send_message(uid,
                                           f"🎯 管理员 {msg.from_user.first_name} 调节了您的到期时间：{b}天"
                                           f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                elif ex_new < ex:
                    ex_new = ex + timedelta(days=b)
                    await msg.reply(
                        f'🍒 __管理员 {msg.from_user.first_name} 已调整用户 [{first.first_name}](tg://user?id={uid}) - {name} 到期时间 {b}天__'
                        f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")} ')
                    await bot.send_message(uid,
                                           f"🎯 管理员 {msg.from_user.first_name} 调节了您的到期时间：{b}天"
                                           f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                if ex_new < datetime.now():
                    lv = 'c'
                    await emby.ban_user(embyid, 0)
                if ex_new > datetime.now():
                    lv = 'b'
                    await emby.ban_user(embyid, 1)
                sqlhelper.update_one("update emby set ex=%s,lv=%s where tg=%s", [ex_new, lv, uid])
                await msg.delete()
                logging.info(
                    f"【admin】[renew]：{msg.from_user.first_name} 对 {first.first_name}({uid})-{name} 用户调节到期时间 {b} 天"
                    f'  实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
            else:
                await msg.reply(f"💢 [ta](tg://user?id={uid}) 还没有注册账户呢")


# 小功能 - 给自己的账号开管理员后台
@bot.on_message(filters.command('admin', prefixes) & filters.user(admins))
async def reload_admins(_, msg):
    await msg.delete()
    embyid = sqlhelper.select_one("select embyid from emby where tg=%s", msg.from_user.id)[0]
    # print(embyid)
    await emby.re_admin(embyid)
    send = await msg.reply("👮🏻 授权完成。已开启emby后台")
    logging.info(f"{msg.from_user.first_name} - {msg.from_user.id} 开启了 emby 后台")
    asyncio.create_task(send_msg_delete(send.chat.id, send.id))


# 小功能 - 给所有未被封禁的 emby 延长指定天数。
@bot.on_message(filters.command('renewall', prefixes) & filters.user(owner))
async def renewall(_, msg):
    try:
        a = int(msg.text.split()[1])
    except IndexError:
        send = await msg.reply(
            "🔔 **使用格式：**/renewall [+/-天数]\n\n  给所有未封禁emby [+/-天数]")
        asyncio.create_task(send_msg_delete(send.chat.id, send.id))
    else:
        send = await bot.send_photo(msg.chat.id, photo=photo, caption="⚡【派送任务】\n  **正在开启派送中...请稍后**")
        result = sqlhelper.select_all("select tg,embyid,name,ex from emby where lv=%s", 'b')
        if result is not None:
            b = 0
            start = time.perf_counter()
            for i in result:
                ex_new = i[3] + timedelta(days=a)
                try:
                    sqlhelper.update_one("update emby set ex=%s where tg=%s", [ex_new, i[0]])
                    await bot.send_message(i[0],
                                           f"🎯 管理员 {msg.from_user.first_name} 调节了您的 {i[2]} 到期时间：{a}天"
                                           f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                except:
                    continue
                b += 1
            end = time.perf_counter()
            times = end - start
            await bot.edit_message_caption(msg.chat.id, send.id,
                                           caption=f"⚡【派送任务】\n  派出 {a} 天 * {b} ，耗时：{times:.3f}s\n  消息已私发。")
            logging.info(f"【派送任务】 -{msg.from_user.first_name}({msg.from_user.id}) 派出 {a} 天 * {b} ，耗时：{times}s")
        else:
            await bot.edit_message_caption(msg.chat.id, send.id, caption="⚡【派送任务】\n\n结束，没有一个有号的。")


# 重启
@bot.on_message(filters.command('restart', prefixes) & filters.user(owner))
async def restart_bot(_, msg):
    send = await msg.reply("Restarting，等待几秒钟。")
    with open(".restartmsg", "w") as f:
        f.write(f"{msg.chat.id} {send.id}\n")
        f.close()
    # some code here
    os.execl('/bin/systemctl', 'systemctl', 'restart', 'embyboss')  # 用当前进程执行systemctl命令，重启embyboss服务
