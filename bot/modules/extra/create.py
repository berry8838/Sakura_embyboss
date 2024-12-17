import asyncio
from datetime import datetime

from pyrogram import filters
from pyrogram.types import CallbackQuery

from bot import bot, prefixes, LOGGER, emby_line, owner, bot_photo, schedall
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.fix_bottons import cv_user_playback_reporting
from bot.func_helper.msg_utils import sendMessage, editMessage, callAnswer, sendPhoto
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby
from bot.sql_helper.sql_emby2 import sql_get_emby2, sql_delete_emby2, sql_add_emby2


@bot.on_message(filters.command('ucr', prefixes) & admins_on_filter & filters.private)
async def login_account(_, msg):
    # await deleteMessage(msg)
    try:
        name = msg.command[1]
        days = int(msg.command[2])
    except (IndexError, ValueError, KeyError):
        return await sendMessage(msg, "🔍 **无效的值。\n\n"
                                      "正确用法:** `/ucr [用户名] [使用天数]`", timer=60)
    else:
        send = await msg.reply(
            f'🆗 收到设置\n\n'
            f'用户名：**{name}**\n\n'
            f'__正在为您初始化账户，更新用户策略__......')
        result = await emby.emby_create(name, days)
        if not result:
            await send.edit(
                '创建失败，原因可能如下：\n\n'
                '❎ 已有此账户名，请重新输入注册\n'
                '❔ __emby服务器未知错误！！！请自行排查服务器__\n\n'
                ' 会话已结束！')
            LOGGER.error("【创建非tg账户】未知错误，检查是否重复id %s 或 emby状态" % name)
        else:
            embyid, pwd, ex = result
            sql_add_emby2(embyid=embyid, name=name, cr=datetime.now(), ex=ex, pwd=pwd, pwd2=pwd)
            await send.edit(
                f'**🎉 成功创建有效期{days}天 #{name}\n\n'
                f'• 用户名称 | `{name}`\n'
                f'• 用户密码 | `{pwd}`\n'
                f'• 当前线路 | \n{emby_line}\n\n'
                f'• 到期时间 | {ex}**')

            if msg.from_user.id != owner:
                await bot.send_message(owner,
                                       f"®️ 管理员 {msg.from_user.first_name} - `{msg.from_user.id}` 已经创建了一个非tg绑定用户 #{name} 有效期**{days}**天")
            LOGGER.info(
                f"【创建非tg账户】：管理员 {msg.from_user.first_name}[{msg.from_user.id}] - 建立了账户 {name}，有效期{days}天 ")


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

    if await emby.emby_del(id=e.embyid):
        sql_update_emby(Emby.tg == e.tg, lv='d', name=None, embyid=None, cr=None,
                        ex=None) if not stats else sql_delete_emby2(e.embyid)
        try:
            await reply.edit(
                f'🎯 done，管理员 [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})\n'
                f'您对Emby账户 {e.name} 的删除操作已完成。')
        except:
            pass
        LOGGER.info(
            f"【admin】：管理员 {msg.from_user.first_name} 成功执行删除 emby 账户 {e.name}")
    else:
        await reply.edit(f"❌ [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})\n"
                         f"f'您对Emby账户 {e.name} 的删除操作失败。'")
        LOGGER.error(
            f"【admin】：管理员 {msg.from_user.first_name} 执行删除失败 emby 账户 {e.name}")


@bot.on_message(filters.command('uinfo', prefixes) & admins_on_filter)
async def uun_info(_, msg, name = None):
    try:
        if name:
            n = name
        else:
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

    if e.name and schedall.low_activity and not schedall.check_ex:
        ex = '__若21天无观看将封禁__'

    elif e.name and not schedall.low_activity and not schedall.check_ex:
        ex = ' __无需保号，放心食用__'
    else:
        ex = e.ex or '无账户信息'
    text += f"▎ 查询返回\n" \
            f"**· 🍉 账户名称** | {e.name}\n{a}" \
            f"**· 🍓 当前状态** | {e.lv}\n" \
            f"**· 🍒 创建时间** | {e.cr}\n" \
            f"**· 🚨 到期时间** | **{ex}**\n"

    await asyncio.gather(sendPhoto(msg, photo=bot_photo, caption=text, buttons=cv_user_playback_reporting(e.embyid)), msg.delete())


@bot.on_callback_query(filters.regex('userip') & admins_on_filter)
@bot.on_message(filters.command('userip', prefixes) & admins_on_filter)
async def user_cha_ip(_, msg, name = None):
    try:
        if isinstance(msg, CallbackQuery):
            user_id = msg.data.split('-')[1]
            msg = msg.message
        else:
            if name:
                user_id = name
            else:
                user_id = msg.command[1]
    except IndexError:
        return await sendMessage(msg, "⭕ 用法：/userip + emby用户名或tgid")
        
    e = sql_get_emby(user_id)
    if not e:
        return await sendMessage(msg, f"数据库中未查询到 {user_id}，请手动确认")
        
    success, result = await emby.get_emby_userip(e.embyid)
    if not success or len(result) == 0:
        return await sendMessage(msg, 'TA好像没播放信息吖')
    else:
        text = '**🌏 以下为该用户播放过的设备&ip 共{}个设备，{}个ip：**\n\n'
        device_count = 0
        ip_count = 0
        device_list = []
        ip_list = []
        details = ""
        for r in result:
            device, client, ip = r
            # 统计ip
            if ip not in ip_list:
                ip_count += 1
                ip_list.append(ip)
            # 统计设备并拼接详情
            if device + client not in device_list:
                device_count += 1
                device_list.append(device + client)
                details += f'{device} | {client} | [{ip}](https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true) \n'
        text = '**🌏 以下为该用户播放过的设备&ip 共{}个设备，{}个ip：**\n\n'.format(device_count, ip_count) + details

        # 以\n分割文本，每20条发送一个消息
        messages = text.split('\n')
        # 每20条消息组成一组
        for i in range(0, len(messages), 20):
            chunk = messages[i:i+20]
            chunk_text = '\n'.join(chunk)
            if not chunk_text.strip():
                continue
            await sendMessage(msg, chunk_text)
