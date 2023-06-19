"""
兑换注册码exchange
"""
import asyncio
import logging
from datetime import datetime, timedelta

import pymysql
from pyrogram import filters
from pyromod.helpers import ikb
from _mysql import sqlhelper
from bot.reply import emby
from config import bot, prefixes, photo, send_msg_delete


# 兑换注册码
@bot.on_message(filters.command('exchange', prefixes) & filters.private)
async def rgs_code(_, msg):
    try:
        register_code = msg.command[1]
    except IndexError:
        send = await msg.reply("🔍 **无效的值。\n\n正确用法:** `/exchange [注册码]`")
        asyncio.create_task(send_msg_delete(send.chat.id, send.id))
    else:
        result = sqlhelper.select_one("select us,tg from invite where id=%s", register_code)
        if result is None:
            send = await msg.reply("⛔ **你输入了一个错误的注册码。\n\n正确用法:** `/exchange [注册码]`")
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
        elif result[0] != 0:
            us = result[0]
            try:
                embyid, ex = sqlhelper.select_one(f"select embyid,ex from emby where tg=%s", msg.from_user.id)
            except TypeError:
                await msg.reply("出错了，不确定您是否有资格使用，请先 /start")
                return
            if embyid is not None:
                # 此处需要写一个判断 now和ex的大小比较。进行日期加减。
                ex_new = datetime.now()
                if ex_new > ex:
                    ex_new = ex_new + timedelta(days=us)
                    await emby.ban_user(embyid, 1)
                    us = 0
                    # sqlhelper.update_one("update emby set lv=%s, ex=%s,us=%s where tg=%s",
                    #                      ['b', ex_new, 0, msg.from_user.id])
                    await msg.reply(f'🍒 __已解封账户并延长到期时间 {us}天 (以当前时间计)。__')
                elif ex_new < ex:
                    ex_new = ex + timedelta(days=us)
                    # sqlhelper.update_one("update emby set lv=%s, ex=%s,us=us+%s where tg=%s",
                    #                      ['b', ex_new, us, msg.from_user.id])
                    await msg.reply(f'🍒 __获得 {us} 积分。__')
                try:
                    sqlhelper.update_one("update emby set lv=%s, ex=%s,us=us+%s where tg=%s",
                                         ['b', ex_new, us, msg.from_user.id])
                    sqlhelper.update_one("update invite set us=%s,used=%s,usedtime=%s where id=%s",
                                         [0, msg.from_user.id, datetime.now(), register_code])
                    logging.info(f"【兑换码】：{msg.chat.id} 使用了 {register_code}")
                except pymysql.err.OperationalError as e:
                    logging.error(e, "数据库出错/未连接")
                    await msg.reply("联系管理，数据库出错。")
            else:
                try:
                    await emby.start_user(msg.from_user.id, us)
                    sqlhelper.update_one("update invite set us=%s,used=%s,usedtime=%s where id=%s",
                                         [0, msg.from_user.id, datetime.now(), register_code])
                    first = await bot.get_chat(result[1])
                except pymysql.err.OperationalError as e:
                    logging.error(e, "数据库出错/未连接")
                    await msg.reply("联系管理，数据库出错。")
                else:
                    await bot.send_photo(
                        msg.from_user.id,
                        photo=photo,
                        caption=f'🎊 少年郎，恭喜你，已经收到了 [{first.first_name}](tg://user?id={result[1]}) 发送的邀请注册资格\n\n请选择你的选项~',
                        reply_markup=ikb([[('🎟️ 注册', 'create'), ('⭕ 取消', 'closeit')]]))
                    logging.info(f"【兑换码】：{msg.chat.id} 使用了 {register_code}")
        else:
            send = await bot.send_message(msg.from_user.id,
                                          f'此 `{register_code}` \n邀请码已被使用,是别人的形状了喔')
            asyncio.create_task(send_msg_delete(send.chat.id, send.id))
