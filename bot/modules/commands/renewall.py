"""
小功能 - 给所有未被封禁的 emby 延长指定天数。加货币
"""
import asyncio
import time
from datetime import timedelta

from pyrogram import filters
from pyrogram.errors import FloodWait

from bot import bot, prefixes, bot_photo, LOGGER, sakura_b
from bot.func_helper.msg_utils import sendMessage, deleteMessage, ask_return
from bot.func_helper.filters import admins_on_filter
from bot.sql_helper.sql_emby import get_all_emby, Emby, sql_update_embys, sql_clear_emby_iv


@bot.on_message(filters.command('renewall', prefixes) & admins_on_filter)
async def renew_all(_, msg):
    await deleteMessage(msg)
    # send_chat
    try:
        a = float(msg.command[1])
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
        if i.ex is None:
            continue
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


# coinsall 全部人加硬币
@bot.on_message(filters.command('coinsall', prefixes) & admins_on_filter)
async def coins_all(_, msg):
    await deleteMessage(msg)
    try:
        a = int(msg.command[1])
    except (IndexError, ValueError):
        return await sendMessage(msg,
                                 f"🔔 **使用格式：**/coinsall [+/-数量]\n\n  给所有未封禁emby [+/- {sakura_b}]", timer=60)
    send = await bot.send_photo(msg.chat.id, photo=bot_photo,
                                caption=f"⚡【{sakura_b}任务】\n  **正在开启派送{sakura_b}中...请稍后**")
    rst = get_all_emby(Emby.lv == 'b')
    if rst is None:
        LOGGER.info(
            f"【{sakura_b}任务】 -{msg.from_user.first_name}({msg.from_user.id}) 没有检测到任何emby账户，结束")
        return await send.edit("⚡【派送任务】\n\n结束，没有一个有号的")

    b = 0
    ls = []
    start = time.perf_counter()
    for i in rst:
        b += 1
        iv_new = i.iv + a
        ls.append([i.tg, iv_new])
    if sql_update_embys(some_list=ls, method='iv'):
        end = time.perf_counter()
        times = end - start
        await send.edit(
            f"⚡【{sakura_b}任务】\n\n  批量派出 {a} {sakura_b} * {b} ，耗时：{times:.3f}s\n 已到账，正在向每个拥有emby的用户私发消息，短时间内请不要重复使用")
        LOGGER.info(
            f"【派送{sakura_b}任务】 - {msg.from_user.first_name}({msg.from_user.id}) 派出 {a} * {b} 更改用时{times:.3f} s")
        for l in ls:
            await bot.send_message(l[0], f"🎯 管理员 {msg.from_user.first_name} 调节了您的账户{sakura_b} {a}"
                                         f'\n📅 实时数量：{l[1]}')
        LOGGER.info(
            f"【派送{sakura_b}任务】 - {msg.from_user.first_name}({msg.from_user.id}) 派出 {a} {sakura_b} * {b}，消息私发完成")
    else:
        await msg.reply("数据库操作出错，请检查重试")

# coinsclear 清除所有用户币币
@bot.on_message(filters.command('coinsclear', prefixes) & admins_on_filter)
async def coinsclear(_, msg):
    await deleteMessage(msg)
    try:
        confirm_clear = msg.command[1]
    except (IndexError, ValueError):
        return await sendMessage(msg,
                                 f"🔔 如果确定清除所有用户币币，请输入 `/coinsclear true`", timer=60)
    if confirm_clear == 'true':
        send = await bot.send_photo(msg.chat.id, photo=bot_photo,
                                caption=f"⚡【{sakura_b}任务】\n  **正在清除所有用户币币...请稍后**")
        rst = sql_clear_emby_iv()
        if rst:
            await send.edit(f"⚡【{sakura_b}任务】\n\n  清除所有用户币币完成")
        else:
            await send.edit(f"⚡【{sakura_b}任务】\n\n  清除所有用户币币失败")
    else:
        return await sendMessage(msg,
                                 f"🔔 如果确定清除所有用户币币，请输入 `/coinsclear true`", timer=60)
@bot.on_message(filters.command('callall', prefixes) & admins_on_filter & filters.private)
async def call_all(_, msg):
    await msg.delete()
    # 可以做分级 所有 b类 非群组类 ：太麻烦，随便搞搞就行
    m = await ask_return(msg,
                         text='**🕶️ 一键公告**\n\n倒计时10min，发送您想要公告的消息，然后根据提示选择发送的用户组，取消请 /cancel',
                         timer=600)

    if not m:
        return
    elif m.text == '/cancel':
        return

    call = await ask_return(msg,
                         text='回复 `1` - 仅公告账户的人\n回复 `2` - 公告全体成员\n取消请 /cancel',
                         timer=600)

    if not call or call.text == '/cancel':
        return await msg.reply('好的,您已取消操作.')
    elif call.text == '2':
        chat_members = get_all_emby(Emby.tg is not None)
    elif call.text == '1':
        chat_members = get_all_emby(Emby.embyid is not None)
    reply = await msg.reply('开始执行发送......')
    a = 0
    start = time.perf_counter()
    for member in chat_members:
        try:
            a += 1
            await m.copy(member.tg)
        except FloodWait as f:
            LOGGER.warning(str(f))
            await asyncio.sleep(f.value * 1.2)
            return await m.copy(member.tg)
        except Exception as e:
            LOGGER.warning(str(e))
    end = time.perf_counter()
    times = end - start
    await reply.edit(f'消息发送完毕\n\n共计：{a} 次，用时 {times:.3f} s')
    LOGGER.info(f'【群发消息】：{msg.from_user.first_name} 消息发送完毕 - 共计：{a} 次，用时 {times:.3f} s')
