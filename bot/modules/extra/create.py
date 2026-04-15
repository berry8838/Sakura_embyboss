import asyncio
from datetime import datetime

from pyrogram import filters
from pyrogram.types import CallbackQuery

from bot import bot, prefixes, LOGGER, emby_line, owner, bot_photo, schedall, config
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.fix_bottons import uinfo_ikb, uinfo_delete_confirm_ikb, close_it_ikb
from bot.func_helper.msg_utils import sendMessage, editMessage, sendPhoto, callAnswer
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby
from bot.sql_helper.sql_emby2 import sql_get_emby2, sql_delete_emby2, sql_add_emby2, sql_update_emby2
from bot.sql_helper.sql_emby2 import Emby2


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
        result = await emby.emby_create(name=name, days=days)
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

    if await emby.emby_del(emby_id=e.embyid):
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
    if msg.reply_to_message is None:
        try:
            if name:
                user_id = name
            else:
                user_id = msg.command[1]
        except (IndexError, ValueError):
            user_id = None
    else:
        user_id = msg.reply_to_message.from_user.id
    if not user_id:
        return await asyncio.gather(msg.delete(), sendMessage(msg, "⭕ 用法：/uinfo + emby用户名或tgid 或回复用户消息"))
    else:
        text = ''
        e = sql_get_emby(user_id)
        if not e:
            e2 = sql_get_emby2(user_id)
            if not e2:
                return await sendMessage(msg, f'数据库中未查询到 {user_id}，请手动确认')
            e = e2
    try:
        a = f'**· 🆔 查询 TG** | {e.tg}\n'
    except AttributeError:
        a = ''

    if e.name and schedall.low_activity and not schedall.check_ex:
        ex = f'__若{config.activity_check_days}天无观看将封禁__'

    elif e.name and not schedall.low_activity and not schedall.check_ex:
        ex = ' __无需保号，放心食用__'
    else:
        ex = e.ex or '无账户信息'
    str_lv = ''
    str_ex = ex
    if e.lv == 'a':
        str_lv = 'a (白名单)'
        str_ex = '白名单用户，无到期时间'
    elif e.lv == 'b':
        str_lv = 'b (普通用户)'
    elif e.lv == 'c':
        str_lv = 'c (已封禁用户)'
    elif e.lv == 'd':
        str_lv = 'd (已删除用户)'

    text += f"▎ 查询返回\n" \
            f"**· 🍉 账户名称** | {e.name}\n{a}" \
            f"**· 🍓 当前状态** | {str_lv}\n" \
            f"**· 🍒 创建时间** | {e.cr}\n" \
            f"**· 🚨 到期时间** | **{str_ex}**\n"
    await asyncio.gather(sendPhoto(msg, photo=bot_photo, caption=text, buttons=uinfo_ikb(e.embyid, e.lv)), msg.delete())


@bot.on_callback_query(filters.regex(r'^uinfo_disable-') & admins_on_filter)
async def uinfo_disable_cb(_, call):
    embyid = call.data.split('-', 1)[1]
    e = sql_get_emby(embyid)
    stats = None
    if not e:
        e = sql_get_emby2(embyid)
        if not e:
            return await callAnswer(call, "❌ 未找到该用户", show_alert=True)
        stats = 1
    if e.lv == 'c':
        return await callAnswer(call, "⚠️ 账户已是禁用状态", show_alert=True)
    if await emby.emby_change_policy(emby_id=embyid, disable=True):
        if stats:
            sql_update_emby2(Emby2.embyid == embyid, lv='c')
        else:
            sql_update_emby(Emby.embyid == embyid, lv='c')
        await call.message.edit_reply_markup(reply_markup=uinfo_ikb(embyid, 'c'))
        await callAnswer(call, f"✅ 账户 {e.name} 已禁用", show_alert=True)
        LOGGER.info(f"【uinfo】管理员通过 uinfo 禁用了账户 {e.name}[{embyid}]")
    else:
        await callAnswer(call, "❌ 禁用账户失败，请检查 Emby 状态", show_alert=True)


@bot.on_callback_query(filters.regex(r'^uinfo_enable-') & admins_on_filter)
async def uinfo_enable_cb(_, call):
    embyid = call.data.split('-', 1)[1]
    e = sql_get_emby(embyid)
    stats = None
    if not e:
        e = sql_get_emby2(embyid)
        if not e:
            return await callAnswer(call, "❌ 未找到该用户", show_alert=True)
        stats = 1
    if e.lv != 'c':
        return await callAnswer(call, "⚠️ 账户当前未被禁用", show_alert=True)
    if await emby.emby_change_policy(emby_id=embyid, disable=False):
        if stats:
            sql_update_emby2(Emby2.embyid == embyid, lv='b')
        else:
            sql_update_emby(Emby.embyid == embyid, lv='b')
        await call.message.edit_reply_markup(reply_markup=uinfo_ikb(embyid, 'b'))
        await callAnswer(call, f"✅ 账户 {e.name} 已启用", show_alert=True)
        LOGGER.info(f"【uinfo】管理员通过 uinfo 启用了账户 {e.name}[{embyid}]")
    else:
        await callAnswer(call, "❌ 启用账户失败，请检查 Emby 状态", show_alert=True)


@bot.on_callback_query(filters.regex(r'^uinfo_delete-') & admins_on_filter)
async def uinfo_delete_cb(_, call):
    embyid = call.data.split('-', 1)[1]
    e = sql_get_emby(embyid)
    if not e:
        e = sql_get_emby2(embyid)
        if not e:
            return await callAnswer(call, "❌ 未找到该用户", show_alert=True)
    await call.message.edit_reply_markup(reply_markup=uinfo_delete_confirm_ikb(embyid))
    await callAnswer(call, f"⚠️ 请确认是否删除账户 {e.name}，此操作不可恢复！", show_alert=True)


@bot.on_callback_query(filters.regex(r'^uinfo_delete_confirm-') & admins_on_filter)
async def uinfo_delete_confirm_cb(_, call):
    embyid = call.data.split('-', 1)[1]
    e = sql_get_emby(embyid)
    stats = None
    if not e:
        e = sql_get_emby2(embyid)
        if not e:
            return await callAnswer(call, "❌ 未找到该用户", show_alert=True)
        stats = 1
    name = e.name
    if await emby.emby_del(emby_id=embyid):
        if stats:
            sql_delete_emby2(embyid)
        else:
            sql_update_emby(Emby.embyid == embyid, lv='d', name=None, embyid=None, cr=None, ex=None)
        try:
            await call.message.edit_caption(
                caption=f"🗑️ 账户 **{name}** 已被管理员删除。",
                reply_markup=close_it_ikb
            )
        except Exception:
            await call.message.edit_reply_markup(reply_markup=close_it_ikb)
        await callAnswer(call, f"✅ 账户 {name} 已删除", show_alert=True)
        LOGGER.info(f"【uinfo】管理员通过 uinfo 删除了账户 {name}[{embyid}]")
    else:
        await call.message.edit_reply_markup(reply_markup=uinfo_ikb(embyid, e.lv))
        await callAnswer(call, "❌ 删除账户失败，请检查 Emby 状态", show_alert=True)
        LOGGER.error(f"【uinfo】管理员通过 uinfo 删除账户失败 {name}[{embyid}]")


@bot.on_callback_query(filters.regex(r'^uinfo_delete_cancel-') & admins_on_filter)
async def uinfo_delete_cancel_cb(_, call):
    embyid = call.data.split('-', 1)[1]
    e = sql_get_emby(embyid)
    if not e:
        e = sql_get_emby2(embyid)
    lv = e.lv if e else None
    await call.message.edit_reply_markup(reply_markup=uinfo_ikb(embyid, lv))
    await callAnswer(call, "✅ 已取消删除")


@bot.on_callback_query(filters.regex('userip') & admins_on_filter)
@bot.on_message(filters.command('userip', prefixes) & admins_on_filter)
async def user_cha_ip(_, msg, name = None):
    if isinstance(msg, CallbackQuery):
        user_id = msg.data.split('-')[1]
        msg = msg.message
    else:
        if msg.reply_to_message is None:
            try:
                if name:
                    user_id = name
                else:
                    user_id = msg.command[1]
            except (IndexError, ValueError):
                user_id = None
        else:
            user_id = msg.reply_to_message.from_user.id
    if not user_id:
        return await sendMessage(msg, "⭕ 用法：/userip + emby用户名或tgid 或回复用户消息")

    e = sql_get_emby(user_id)
    if not e:
        return await sendMessage(msg, f"数据库中未查询到 {user_id}，请手动确认")

    success, result = await emby.get_emby_userip(emby_id = e.embyid)
    if not success or len(result) == 0:
        return await sendMessage(msg, 'TA好像没播放信息吖')
    else:
        device_count = 0
        ip_count = 0
        device_list = []
        ip_list = []
        device_details = ""
        ip_details = ""
        for r in result:
            device, client, ip = r
            # 统计ip
            if ip not in ip_list:
                ip_count += 1
                ip_list.append(ip)
                ip_details += f'{ip_count}: `{ip}`| [{ip}](https://whois.pconline.com.cn/ipJson.jsp?ip={ip}&json=true) \n'

            # 统计设备并拼接详情
            if device + client not in device_list:
                device_count += 1
                device_list.append(device + client)
                device_details += f'{device_count}: {device} | {client}  \n'
        text = '**🌏 以下为该用户播放过的设备&ip 共{}个设备，{}个ip：**\n\n'.format(device_count, ip_count) + '**设备:**\n' + device_details + '**IP:**\n'+ ip_details


        # 以\n分割文本，每20条发送一个消息
        messages = text.split('\n')
        # 每20条消息组成一组
        for i in range(0, len(messages), 20):
            chunk = messages[i:i+20]
            chunk_text = '\n'.join(chunk)
            if not chunk_text.strip():
                continue
            await sendMessage(msg, chunk_text)
@bot.on_message(filters.command('udeviceid', prefixes) & admins_on_filter)
async def get_user_by_deviceid(_, msg, deviceid = None):
    try:
        deviceid = msg.command[1]
    except IndexError:
        return await sendMessage(msg, "⭕ 用法：/udeviceid + 设备ID")
    await msg.delete()
    success, result = await emby.get_device_by_deviceid(deviceid = deviceid)
    if not success:
        return await sendMessage(msg, '获取设备信息失败')
    else:
        if isinstance(result, dict) and len(result) > 0:
            text = '▎ 查询返回:\n'
            text += f'•🧢 设备名称: {result.get("Name", "无设备名称")}\n'
            text += f'•🙆‍ App名称: {result.get("AppName", "无App名称")}\n'
            text += f'•👔 App版本: {result.get("AppVersion", "无App版本")}\n'
            text += f'•👖 用户名称: {result.get("LastUserName", "无用户名称")}\n'
            text += f'•👟 用户Id: {result.get("LastUserId", "无用户Id")}\n'
            text += f'•💼 最后活动时间: {result.get("DateLastActivity", "无最后活动时间")}\n'
            text += f'•🔐 Ip地址: {result.get("IpAddress", "无Ip地址")}\n'
            icon = result.get("IconUrl")
            if icon:
                await sendPhoto(msg, photo=icon, caption=text, buttons=close_it_ikb)
            else:
                await sendMessage(msg, text, buttons=close_it_ikb)
        else:
            await sendMessage(msg, "获取设备信息失败")
