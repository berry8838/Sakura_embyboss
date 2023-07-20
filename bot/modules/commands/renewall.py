"""
小功能 - 给所有未被封禁的 emby 延长指定天数。
"""
import time
from datetime import timedelta

from pyrogram import filters

from bot import bot, prefixes, owner, bot_photo, LOGGER
from bot.func_helper.msg_utils import sendMessage, deleteMessage
from bot.sql_helper.sql_emby import get_all_emby, Emby, sql_update_embys


@bot.on_message(filters.command('renewall', prefixes) & filters.user(owner))
async def renew_all(_, msg):
    await deleteMessage(msg)
    try:
        a = int(msg.command[1])
    except (IndexError, ValueError):
        return await sendMessage(msg,
                                 "🔔 **使用格式：**/renewall [+/-天数]\n\n  给所有未封禁emby [+/-天数]", timer=60)

    send = await bot.send_photo(msg.chat.id, photo=bot_photo, caption="⚡【派送任务】\n  **正在开启派送中...请稍后**")
    rst = get_all_emby(Emby.lv == 'b')
    if rst is None:
        LOGGER.info(
            f"【派送任务】 -{msg.from_user.first_name}({msg.from_user.id}) 没有检测到任何emby账户，结束")
        return await send.edit("⚡【派送任务】\n\n结束，没有一个有号的")

    b = 0
    ls = []
    start = time.perf_counter()
    for i in rst:
        b += 1
        ex_new = i.ex + timedelta(days=a)
        ls.append([i.tg, ex_new])
    if sql_update_embys(some_list=ls, method='ex'):
        end = time.perf_counter()
        times = end - start
        await send.edit(
            f"⚡【派送任务】\n  批量派出 {a} 天 * {b} ，耗时：{times:.3f}s\n 时间已到账，正在向每个拥有emby的用户私发消息，短时间内请不要重复使用")
        LOGGER.info(
            f"【派送任务】 - {msg.from_user.first_name}({msg.from_user.id}) 派出 {a} 天 * {b} 更改用时{times:.3f} s")
        for l in ls:
            await bot.send_message(l[0], f"🎯 管理员 {msg.from_user.first_name} 调节了您的账户 到期时间：{a}天"
                                         f'\n📅 实时到期：{l[1].strftime("%Y-%m-%d %H:%M:%S")}')
        LOGGER.info(
            f"【派送任务】 - {msg.from_user.first_name}({msg.from_user.id}) 派出 {a} 天 * {b}，消息私发完成")
    else:
        await msg.reply("数据库操作出错，请检查重试")
