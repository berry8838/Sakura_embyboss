"""
对用户分数调整
"""

import logging
import os
import time
from datetime import datetime, timedelta

import asyncio
from pyrogram import filters
from pyrogram.errors import BadRequest

from _mysql import sqlhelper
from bot.reply import emby
from config import bot, prefixes, admins, send_msg_delete, owner, photo, judge_user_in_group, group


@bot.on_message(filters.command('score', prefixes=prefixes) & filters.user(admins))
async def score_user(_, msg):
    if msg.reply_to_message is None:
        try:
            b = int(msg.command[1])
            c = int(msg.command[2])
            first = await bot.get_chat(b)
        except (IndexError, KeyError, BadRequest, ValueError):
            send = await msg.reply(
                "🔔 **使用格式：**[命令符]score [id] [加减分数]\n\n或回复某人[命令符]score [+/-分数] 请确认tg_id输入正确")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            sqlhelper.update_one("update emby set us=us+%s where tg=%s", [c, b])
            us = sqlhelper.select_one("select us from emby where tg =%s", b)[0]
            await msg.reply(
                f"· 🎯管理员 {msg.from_user.first_name} 调节了 [{first.first_name}](tg://user?id={b}) 积分： {c}"
                f"\n· 🎟️ 实时积分: **{us}**")
            logging.info(f"【admin】[积分]：管理员 {msg.from_user.first_name} 对 {first.first_name}-{b}  {c}分  ")
    else:
        try:
            uid = msg.reply_to_message.from_user.id
            first = await bot.get_chat(uid)
            b = int(msg.command[1])
        except (IndexError, ValueError):
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
            logging.info(f"【admin】[积分]：管理员 {msg.from_user.first_name} 对 {first.first_name}-{uid}  {b}分  ")


@bot.on_message(filters.command('renew', prefixes) & filters.user(admins))
async def renew_user(_, msg):
    reply = await msg.reply(f"🍓 正在处理ing···/·")
    if msg.reply_to_message is None:
        try:
            b = msg.command[1]  # name
            c = int(msg.command[2])  # 天数
        except (IndexError, KeyError, BadRequest, ValueError):
            send = await reply.edit(
                "🔔 **使用格式：**/renew [emby_name] [+/-天数]\n\n或回复某人 /renew [+/-天数] \nemby_name为emby账户名")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            try:
                embyid, ex, expired = sqlhelper.select_one("select embyid,ex,expired from emby2 where name=%s", b)
                if embyid is not None:
                    ex_new = datetime.now()
                    if ex_new > ex:
                        ex_new = ex_new + timedelta(days=c)
                        await reply.edit(
                            f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c}天 (以当前时间计)__'
                            f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                    elif ex_new < ex:
                        ex_new = ex + timedelta(days=c)
                        await reply.edit(
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
                    tg, embyid, lv, ex = sqlhelper.select_one("select tg,embyid,lv,ex from emby where name=%s", b)
                except TypeError:
                    await reply.edit(f"♻️ 没有检索到 {b} 这个账户，请确认重试。")
                else:
                    if embyid is not None:
                        ex_new = datetime.now()
                        if ex_new > ex:
                            ex_new = ex_new + timedelta(days=c)
                            await reply.edit(
                                f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c} 天 (以当前时间计)__'
                                f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                        elif ex_new < ex:
                            ex_new = ex + timedelta(days=c)
                            await reply.edit(
                                f'🍒 __管理员 {msg.from_user.first_name} 已调整 emby 用户 {b} 到期时间 {c} 天__'
                                f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                        if ex_new < datetime.now():
                            lv = 'c'
                            await emby.ban_user(embyid, 0)
                        if ex_new > datetime.now():
                            lv = 'b'
                            await emby.ban_user(embyid, 1)
                        sqlhelper.update_one("update emby set ex=%s,lv=%s where name=%s", [ex_new, lv, b])
                        await reply.forward(tg)
                        logging.info(
                            f"【admin】[renew]：管理员 {msg.from_user.first_name} 对 emby账户{b} 调节 {c} 天，"
                            f"实时到期：{ex_new.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        try:
            uid = msg.reply_to_message.from_user.id
            first = await bot.get_chat(uid)
            b = int(msg.command[1])
        except (IndexError, ValueError):
            send = await reply.edit(
                "🔔 **使用格式：**/renew [emby_name] [+/-天数]\n\n或回复某人 /renew [+/-天数]\nemby_name为emby账户名")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        else:
            embyid, name, lv, ex = sqlhelper.select_one("select embyid,name,lv,ex from emby where tg=%s", uid)
            if embyid is not None:
                ex_new = datetime.now()
                if ex_new > ex:
                    ex_new = ex_new + timedelta(days=b)
                    await reply.edit(
                        f'🍒 __管理员 {msg.from_user.first_name} 已调整用户 [{first.first_name}](tg://user?id={uid}) - '
                        f'{name} 到期时间 {b}天 (以当前时间计)__'
                        f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                    await bot.send_message(uid,
                                           f"🎯 管理员 {msg.from_user.first_name} 调节了您的到期时间：{b}天"
                                           f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                elif ex_new < ex:
                    ex_new = ex + timedelta(days=b)
                    await reply.edit(
                        f'🍒 __管理员 {msg.from_user.first_name} 已调整用户 [{first.first_name}](tg://user?id={uid}) - '
                        f'{name} 到期时间 {b}天__'
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
                    f"【admin】[renew]：管理员 {msg.from_user.first_name} 对 {first.first_name}({uid})-{name} 用户调节到期时间 {b} 天"
                    f'  实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
            else:
                await reply.edit(f"💢 [ta](tg://user?id={uid}) 还没有注册账户呢")


# 小功能 - 给自己的账号开管理员后台
@bot.on_message(filters.command('admin', prefixes) & filters.user(admins))
async def reload_admins(_, msg):
    await msg.delete()
    embyid = sqlhelper.select_one("select embyid from emby where tg=%s", msg.from_user.id)[0]
    if embyid is not None:
        await emby.re_admin(embyid)
        send = await msg.reply("👮🏻 授权完成。已开启emby后台")
        logging.info(f"{msg.from_user.first_name} - {msg.from_user.id} 开启了 emby 后台")
        asyncio.create_task(send_msg_delete(send.chat.id, send.id))
    else:
        send = await msg.reply("👮🏻 授权失败。未查询到绑定账户")
        logging.info(f"{msg.from_user.first_name} - {msg.from_user.id} 开启 emby 后台失败")
        asyncio.create_task(send_msg_delete(send.chat.id, send.id))


# 小功能 - 给所有未被封禁的 emby 延长指定天数。
@bot.on_message(filters.command('renewall', prefixes) & filters.user(owner))
async def renewall(_, msg):
    await msg.delete()
    try:
        a = int(msg.command[1])
    except (IndexError, ValueError):
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
                                           f"🎯 管理员 {msg.from_user.first_name} 调节了您的账户 {i[2]} 到期时间：{a}天"
                                           f'\n📅 实时到期：{ex_new.strftime("%Y-%m-%d %H:%M:%S")}')
                except:
                    continue
                b += 1
            end = time.perf_counter()
            times = end - start
            if b != 0:
                await send.edit(f"⚡【派送任务】\n  派出 {a} 天 * {b} ，耗时：{times:.3f}s\n  消息已私发。")
                logging.info(
                    f"【派送任务】 -{msg.from_user.first_name}({msg.from_user.id}) 派出 {a} 天 * {b} ，耗时：{times}s")
            else:
                await send.edit("⚡【派送任务】\n\n结束，没有一个有号的。")
                logging.info(
                    f"【派送任务】 -{msg.from_user.first_name}({msg.from_user.id}) 没有检测到任何emby账户，结束")
        else:
            await send.edit("⚡【派送任务】\n\n结束，没有一个有号的。")


# 重启
@bot.on_message(filters.command('restart', prefixes) & filters.user(owner))
async def restart_bot(_, msg):
    send = await msg.reply("Restarting，等待几秒钟。")
    with open(".restartmsg", "w") as f:
        f.write(f"{msg.chat.id} {send.id}\n")
        f.close()
    # some code here
    os.execl('/bin/systemctl', 'systemctl', 'restart', 'embyboss')  # 用当前进程执行systemctl命令，重启embyboss服务


# 删除账号命令
@bot.on_message(filters.command('rmemby', prefixes) & filters.user(admins))
async def renew_user(_, msg):
    reply = await msg.reply("🍉 正在处理ing....")
    if msg.reply_to_message is None:
        try:
            b = msg.command[1]  # name
            int(b)
            first = await bot.get_chat(b)  # if tg_id
            # print(b)
        # except (IndexError, KeyError, BadRequest):
        except (IndexError, KeyError):
            send = await reply.edit(
                "🔔 **使用格式：**/rmemby [tgid]或回复某人，推荐使用回复方式\n/rmemby [emby用户名亦可]")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        except (BadRequest, ValueError):
            try:
                embyid = sqlhelper.select_one("select embyid from emby2 where name=%s", b)[0]
                if embyid is not None:
                    sqlhelper.delete_one("delete from emby2 WHERE embyid =%s", embyid)
                    if await emby.emby_del(embyid) is True:
                        await reply.edit(f'🎯 done，管理员{msg.from_user.first_name} 已将 账户 {b} 已完成删除。')
                        logging.info(f"【admin】：{msg.from_user.first_name} 执行删除 emby2表 {b} 账户")
            except TypeError:
                try:
                    tg, embyid, lv, ex = sqlhelper.select_one("select tg,embyid,lv,ex from emby where name=%s", b)
                    first = await bot.get_chat(tg)
                except TypeError:
                    await reply.edit(f"♻️ 没有检索到 {b} 这个账户，请确认重试或手动检查。")
                else:
                    if embyid is not None:
                        if await emby.emby_del(embyid) is True:
                            sqlhelper.delete_one("delete from emby WHERE embyid =%s", embyid)
                            await reply.edit(
                                f'🎯 done，管理员{msg.from_user.first_name} 已将 [{first.first_name}](tg://user?id={tg}) '
                                f'账户 {b} 删除。')
                            await bot.send_message(tg,
                                                   f'🎯 done，管理员{msg.from_user.first_name} 已将 您的账户 {b} 删除。')
                            logging.info(
                                f"【admin】：管理员 {msg.from_user.first_name} 执行删除 {first.first_name}-{tg} 账户{b} ")
                    else:
                        await reply.edit(f"💢 [ta](tg://user?id={b}) 还没有注册账户呢")
        else:
            try:
                embyid, name, lv, ex = sqlhelper.select_one("select embyid,name,lv,ex from emby where tg=%s", b)
            except TypeError:
                await reply.edit(f"♻️ 没有检索到 {first.first_name} 账户，请确认重试或手动检查。")
            else:
                if embyid is not None:
                    if await emby.emby_del(embyid) is True:
                        sqlhelper.delete_one("delete from emby WHERE embyid =%s", embyid)
                        await reply.edit(
                            f'🎯 done，管理员 {msg.from_user.first_name}\n[{first.first_name}](tg://user?id={b}) 账户 {name} '
                            f'已完成删除。')
                        await bot.send_message(b,
                                               f'🎯 done，管理员{msg.from_user.first_name} 已将 您的账户 {name} 删除。')
                        await msg.delete()
                        logging.info(
                            f"【admin】：管理员 {msg.from_user.first_name} 执行删除 {first.first_name}-{b} 账户 {name}")
                else:
                    await reply.edit(f"💢 [ta](tg://user?id={b}) 还没有注册账户呢")

    else:
        uid = msg.reply_to_message.from_user.id
        first = await bot.get_chat(uid)
        try:
            embyid, name, lv, ex = sqlhelper.select_one("select embyid,name,lv,ex from emby where tg=%s", uid)
        except TypeError:
            await reply.edit(f"♻️ 没有检索到 {first.first_name} 账户，请确认重试或手动检查。")
        else:
            if embyid is not None:
                if await emby.emby_del(embyid) is True:
                    sqlhelper.delete_one("delete from emby WHERE embyid =%s", embyid)
                    await reply.edit(
                        f'🎯 done，管理员 {msg.from_user.first_name}\n[{first.first_name}](tg://user?id={uid}) 账户 {name} '
                        f'已完成删除。')
                    await bot.send_message(uid,
                                           f'🎯 done，管理员{msg.from_user.first_name} 已将 您的账户 {name} 删除。')
                    await msg.delete()
                    logging.info(
                        f"【admin】：管理员 {msg.from_user.first_name} 执行删除 {first.first_name}-{uid} 账户 {name}")
            else:
                await reply.edit(f"💢 [ta](tg://user?id={uid}) 还没有注册账户呢")


@bot.on_message(filters.command('syncemby', prefixes) & filters.user(admins))
async def sync_emby_group(_, msg):
    send = await bot.send_photo(msg.chat.id, photo=photo, caption="⚡【同步任务】\n  **正在开启中...消灭未在群组的账户**")
    logging.info(
        f"【同步任务开启】 - {msg.from_user.first_name} - {msg.from_user.id}")
    try:
        await send.pin()
        await msg.delete()
    except BadRequest:
        await send.edit("🔴 置顶/删除群消息失败，检查权限，继续运行ing")
    result = sqlhelper.select_all(
        "select tg,embyid,ex,us,name from emby where %s", 1)
    b = 0
    start = time.perf_counter()
    for r in result:
        if r[1] is None:
            continue
        else:
            first = await bot.get_chat(r[0])
            if await judge_user_in_group(r[0]) is False:
                if await emby.emby_del(r[1]) is True:
                    sqlhelper.delete_one("delete from emby WHERE embyid =%s", r[1])
                    await bot.send_message(group[0],
                                           f'🎯 【未在群组封禁】 #id{r[0]}\n已将 [{first.first_name}](tg://user?id={r[0]}) 账户 {r[4]} '
                                           f'完成删除。')
                else:
                    await send.reply(f'🎯 【未在群组封禁】 #id{r[0]}\n[{first.first_name}](tg://user?id={r[0]}) 账户 {r[4]} '
                                     f'删除错误')
        b += 1
    end = time.perf_counter()
    times = end - start
    try:
        await send.unpin()
    except BadRequest:
        pass
    if b != 0:
        await send.edit(f"⚡【同步任务】\n  共检索 {b} 个账户，耗时：{times:.3f}s\n**任务结束**")
        logging.info(
            f"【同步任务结束】 - {msg.from_user.id} 共检索 {b} 个账户，耗时：{times:.3f}s")
    else:
        await send.edit("⚡【同步任务】\n\n结束，没有一个有号的。")
        logging.info(
            f"【同步任务结束】 - {msg.from_user.id} 共检索 {b} 个账户，耗时：{times:.3f}s")
