import asyncio
from pyrogram import filters
from pyrogram.errors import BadRequest

from bot import bot, prefixes, LOGGER, emby_line, owner, bot_photo
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.fix_bottons import cv_user_ip
from bot.func_helper.msg_utils import sendMessage, editMessage, callAnswer, sendPhoto
from bot.sql_helper.sql_emby import sql_get_emby
from bot.sql_helper.sql_emby2 import sql_get_emby2


@bot.on_message(filters.command('ucr', prefixes) & admins_on_filter & filters.private)
async def login_account(_, msg):
    # await deleteMessage(msg)
    try:
        name = msg.command[1]
        days = int(msg.command[2])
    except (IndexError, ValueError, KeyError):
        return await sendMessage(msg, "🔍 **无效的值。\n\n正确用法:** `/ucr [用户名] [使用天数]`", timer=60)
    else:
        send = await msg.reply(
            f'🆗 收到设置\n\n用户名：**{name}**\n\n__正在为您初始化账户，更新用户策略__......')
        try:
            int(name)
        except ValueError:
            pass
        else:
            try:
                await bot.get_chat(name)
            except BadRequest:
                pass
            else:
                await send.edit("🚫 根据银河正义法，您创建的用户名不得与任何 tg_id 相同")
                return
        await asyncio.sleep(1)
        pwd1 = await emby.emby_create(5210, name, 1234, days, 'o')
        if pwd1 == 100:
            await send.edit(
                '**❎ 已有此账户名，请重新输入注册**\n或 ❔ __emby服务器未知错误！！！请联系闺蜜（管理）__ **会话已结束！**')
            LOGGER.error("未知错误，检查数据库和emby状态")
        elif pwd1 == 403:
            await send.edit('**🚫 很抱歉，注册总数已达限制**\n【admin】——>【注册状态】中可调节')
        else:
            await send.edit(
                f'**🎉 成功创建有效期{days}天 #{name}\n\n• 用户名称 | `{name}`\n'
                f'• 用户密码 | `{pwd1[0]}`\n• 安全密码 | `{1234}`\n'
                f'• 当前线路 | \n{emby_line}\n\n• 到期时间 | {pwd1[1]}**')

            await bot.send_message(owner,
                                   f"®️ 您的管理员 {msg.from_user.first_name} - `{msg.from_user.id}` 已经创建了一个非tg绑定用户 #{name} 有效期**{days}**天")
            LOGGER.info(f"【创建tg外账户】：{msg.from_user.id} - 建立了账户 {name}，有效期{days}天 ")


# 删除指定用户名账号命令
@bot.on_message(filters.command('urm', prefixes) & admins_on_filter)
async def urm_user(_, msg):
    reply = await msg.reply("🍉 正在处理ing....")
    try:
        b = msg.command[1]  # name
    except IndexError:
        return await asyncio.gather(editMessage(reply,
                                                "🔔 **使用格式：**/urm [emby用户名]，此命令用于删除指定用户名的用户"),
                                    msg.delete())
    e = sql_get_emby(tg=b)
    stats = None
    if not e:
        e2 = sql_get_emby2(name=b)
        if not e2:
            return await reply.edit(f"♻️ 没有检索到 {b} 账户，请确认重试或手动检查。")
        e = e2
        stats = 1

    if await emby.emby_del(id=e.embyid, stats=stats):
        try:
            await reply.edit(
                f'🎯 done，管理员 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})\n'
                f'账户 {e.name} 已完成删除。')
        except:
            pass
        LOGGER.info(
            f"【admin】：管理员 {msg.from_user.first_name} 执行删除 emby2账户 {e.name}")


@bot.on_message(filters.command('uinfo', prefixes) & admins_on_filter)
async def uun_info(_, msg):
    try:
        n = msg.command[1]
    except IndexError:
        return await asyncio.gather(msg.delete(), sendMessage(msg, "⭕ 用法：/uinfo + emby用户名"))
    else:
        text = ''
        e = sql_get_emby(n)
        if not e:
            e2 = sql_get_emby2(n)
            if not e2:
                return await sendMessage(msg, f'数据库中未查询到 {n}，请手动确认')
            e = e2
    try:
        a = f'**· 🆔 查询 TG** | {e.tg}\n'
    except AttributeError:
        a = ''
    text += f"▎ 查询返回\n" \
            f"**· 🍉 账户名称** | {e.name}\n{a}" \
            f"**· 🍓 当前状态** | {e.lv}\n" \
            f"**· 🍒 创建时间** | {e.cr}\n" \
            f"**· 🚨 到期时间** | **{e.ex}**\n"

    await asyncio.gather(sendPhoto(msg, photo=bot_photo, caption=text, buttons=cv_user_ip(e.embyid)), msg.delete())


@bot.on_callback_query(filters.regex('userip') & admins_on_filter)
async def user_cha_ip(_, call):
    user_id = call.data.split('-')[1]
    success, result = await emby.get_emby_userip(user_id)
    if not success or len(result) == 0:
        return await callAnswer(call, '没有更多信息咧')
    else:
        text = '🌏 以下为该用户播放过的设备&ip\n\n'
        for r in result:
            ip, device = r
            text += f'[{device}](https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true)\n'
        await bot.send_message(call.from_user.id, text)
