"""
kk - 纯装x
赠与账户，禁用，删除
"""
import pyrogram
from pyrogram import filters
from pyrogram.errors import BadRequest
from bot import bot, prefixes, owner, bot_photo, admins, LOGGER, extra_emby_libs
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.fix_bottons import cr_kk_ikb, gog_rester_ikb
from bot.func_helper.msg_utils import deleteMessage, sendMessage, sendPhoto, editMessage
from bot.func_helper.utils import judge_admins, cr_link_two
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby


# 管理用户
@bot.on_message(filters.command('kk', prefixes) & admins_on_filter)
async def user_info(_, msg):
    await deleteMessage(msg)
    if msg.reply_to_message is None:
        try:
            uid = int(msg.command[1])
            if msg.from_user.id != owner and uid == owner:
                return await sendMessage(msg,
                                         f"⭕ [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})！不可以偷窥主人",
                                         timer=60)

            first = await bot.get_chat(uid)
        except (IndexError, KeyError):
            return await sendMessage(msg, '**请先给我一个tg_id！**\n\n用法：/kk [id]\n或者对某人回复kk', timer=60)
        except BadRequest:
            return await sendMessage(msg, f'{uid} - 🎂抱歉，此id未登记bot，或者id错误', timer=60)
        except AttributeError:
            pass
        else:
            text, keyboard = await cr_kk_ikb(uid, first.first_name)
            await sendPhoto(msg, photo=bot_photo, caption=text, buttons=keyboard)  # protect_content=True 移除禁止复制

    else:
        uid = msg.reply_to_message.from_user.id
        try:
            if msg.from_user.id != owner and uid == owner:
                return await msg.reply(
                    f"⭕ [{msg.from_user.first_name}](tg://user?id={msg.from_user.id})！不可以偷窥主人")
        except AttributeError:
            pass

        first = await bot.get_chat(uid)
        text, keyboard = await cr_kk_ikb(uid, first.first_name)
        await sendMessage(msg, text=text, buttons=keyboard)


# 封禁或者解除
@bot.on_callback_query(filters.regex('user_ban'))
async def kk_user_ban(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("✅ ok")
    b = int(call.data.split("-")[1])
    if b in admins and b != call.from_user.id:
        return await editMessage(call,
                                 f"⚠️ 打咩，no，机器人不可以对bot管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决",
                                 timer=60)

    first = await bot.get_chat(b)
    e = sql_get_emby(tg=b)
    if e.embyid is None:
        await editMessage(call, f'💢 ta 没有注册账户。', timer=60)
    else:
        if e.lv != "c":
            if await emby.emby_change_policy(id=e.embyid, method=True) is True:
                if sql_update_emby(Emby.tg == b, lv='c') is True:
                    await editMessage(call,
                                      f'🎯 管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 已禁用[{first.first_name}](tg://user?id={b}) 账户 {e.name}\n'
                                      f'此状态可在下次续期时刷新')
                    await bot.send_message(b,
                                           f"🎯 管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 已禁用 您的账户 {e.name}\n此状态可在下次续期时刷新")
                    LOGGER.info(f"【admin】：管理员 {call.from_user.id} 完成禁用 {b} 账户 {e.name}")
                else:
                    await editMessage(call, '⚠️ 封禁失败，服务器已执行，数据库写入错误')
            else:
                await editMessage(call, '⚠️ 封禁失败，请检查emby服务器。响应错误')
        elif e.lv == "c":
            if await emby.emby_change_policy(id=e.embyid):
                if sql_update_emby(Emby.tg == b, lv='b'):
                    await editMessage(call,
                                      f'🎯 管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 已解除禁用[{first.first_name}](tg://user?id={b}) 账户 {e.name}')
                    await bot.send_message(b,
                                           f"🎯 管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 已解除禁用 您的账户 {e.name}")
                    LOGGER.info(f"【admin】：管理员 {call.from_user.id} 解除禁用 {b} 账户 {e.name}")
                else:
                    await editMessage(call, '⚠️ 解封失败，服务器已执行，数据库写入错误')
            else:
                await editMessage(call, '⚠️ 解封失败，请检查emby服务器。响应错误')


# 开通额外媒体库
@bot.on_callback_query(filters.regex('embyextralib_unblock'))
async def user_embyextralib_unblock(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)
    await call.answer(f'🎬 正在为TA开启显示ing')
    tgid = int(call.data.split("-")[1])
    e = sql_get_emby(tg=tgid)
    if e.embyid is None:
        await editMessage(call, f'💢 ta 没有注册账户。', timer=60)
    embyid = e.embyid
    success, rep = emby.user(embyid=embyid)
    currentblock = []
    if success:
        try:
            currentblock = list(set(rep["Policy"]["BlockedMediaFolders"] + ['播放列表']))
            # 保留不同的元素
            currentblock = [x for x in currentblock if x not in extra_emby_libs] + [x for x in extra_emby_libs if x not in currentblock]
        except KeyError:
            currentblock = ["播放列表"]
        re = await emby.emby_block(embyid, 0, block=currentblock)
        if re is True:
            await editMessage(call, f'🌟 好的，管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n'
                                    f'已开启了 [TA](tg://user?id={tgid}) 的额外媒体库权限\n{extra_emby_libs}')
        else:
            await editMessage(call,
                              f'🌧️ Error！管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n操作失败请检查设置！')


# 隐藏额外媒体库
@bot.on_callback_query(filters.regex('embyextralib_block'))
async def user_embyextralib_block(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)
    await call.answer(f'🎬 正在为TA关闭显示ing')
    tgid = int(call.data.split("-")[1])
    e = sql_get_emby(tg=tgid)
    if e.embyid is None:
        await editMessage(call, f'💢 ta 没有注册账户。', timer=60)
    embyid = e.embyid
    success, rep = emby.user(embyid=embyid)
    currentblock = []
    if success:
        try:
            currentblock = list(set(rep["Policy"]["BlockedMediaFolders"] + ['播放列表']))
            currentblock = list(set(currentblock + extra_emby_libs))
        except KeyError:
            currentblock = ["播放列表"] + extra_emby_libs
        re = await emby.emby_block(embyid, 0, block=currentblock)
        if re is True:
            await editMessage(call, f'🌟 好的，管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n'
                                    f'已关闭了 [TA](tg://user?id={tgid}) 的额外媒体库权限\n{extra_emby_libs}')
        else:
            await editMessage(call,
                              f'🌧️ Error！管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n操作失败请检查设置！')


# 赠送资格
@bot.on_callback_query(filters.regex('gift'))
async def gift(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("✅ ok")
    b = int(call.data.split("-")[1])
    if b in admins and b != call.from_user.id:
        return await editMessage(call,
                                 f"⚠️ 打咩，no，机器人不可以对bot管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决")

    first = await bot.get_chat(b)
    e = sql_get_emby(tg=b)
    if e.embyid is None:
        link = await cr_link_two(tg=call.from_user.id, times=b, days=30)
        await editMessage(call, f"🌟 好的，管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n"
                                f'已为 [{first.first_name}](tg://user?id={b}) 赠予资格。前往bot进行下一步操作：',
                          buttons=gog_rester_ikb(link))
        LOGGER.info(f"【admin】：{call.from_user.id} 已发送 注册资格 {first.first_name} - {b} ")
    else:
        await editMessage(call, f'💢 [ta](tg://user?id={b}) 已注册账户。')


# 删除账户
@bot.on_callback_query(filters.regex('closeemby'))
async def close_emby(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("✅ ok")
    b = int(call.data.split("-")[1])
    if b in admins and b != call.from_user.id:
        return await editMessage(call,
                                 f"⚠️ 打咩，no，机器人不可以对bot管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决",
                                 timer=60)

    first = await bot.get_chat(b)
    e = sql_get_emby(tg=b)
    if e.embyid is None:
        return await editMessage(call, f'💢 ta 还没有注册账户。', timer=60)

    if await emby.emby_del(e.embyid):
        await editMessage(call,
                          f'🎯 done，管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n等级：{e.lv} - [{first.first_name}](tg://user?id={b}) '
                          f'账户 {e.name} 已完成删除。')
        await bot.send_message(b,
                               f"🎯 管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 已删除 您 的账户 {e.name}")
        LOGGER.info(f"【admin】：{call.from_user.id} 完成删除 {b} 的账户 {e.name}")
    else:
        await editMessage(call, f'🎯 done，等级：{e.lv} - {first.first_name}的账户 {e.name} 删除失败。')
        LOGGER.info(f"【admin】：{call.from_user.id} 对 {b} 的账户 {e.name} 删除失败 ")


@bot.on_callback_query(filters.regex('fuckoff'))
async def fuck_off_m(_, call):
    if not judge_admins(call.from_user.id):
        return await call.answer("请不要以下犯上 ok？", show_alert=True)

    await call.answer("✅ ok")
    b = int(call.data.split("-")[1])
    if b in admins and b != call.from_user.id:
        return await editMessage(call,
                                 f"⚠️ 打咩，no，机器人不可以对bot管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决",
                                 timer=60)
    try:
        await bot.ban_chat_member(call.message.chat.id, b)
    except pyrogram.errors.ChatAdminRequired:
        await editMessage(call,
                          f"⚠️ 请赋予我踢出成员的权限 [{call.from_user.first_name}](tg://user?id={call.from_user.id})")
    except pyrogram.errors.UserAdminInvalid:
        await editMessage(call,
                          f"⚠️ 打咩，no，机器人不可以对群组管理员出手喔，请[自己](tg://user?id={call.from_user.id})解决")
    else:
        first = await bot.get_chat(b)
        e = sql_get_emby(tg=b)
        if e.embyid is None:
            await editMessage(call, f'💢 ta 还没有注册账户，但会为 [您](tg://user?id={call.from_user.id}) 执行踢出')
            LOGGER.info(
                f"【admin】：{call.from_user.id} 已从群组 {call.message.chat.id} 封禁 {first.first_name}-{b} ")
        else:
            if await emby.emby_del(e.embyid) is True:
                await editMessage(call,
                                  f'🎯 done，管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id})\n等级：{e.lv} - [{first.first_name}](tg://user?id={b}) '
                                  f'账户 {e.name} 已删除并封禁')
                await bot.send_message(b,
                                       f"🎯 管理员 [{call.from_user.first_name}](tg://user?id={call.from_user.id}) 已删除 您 的账户 {e.name}，并将您从群组封禁。")
                LOGGER.info(f"【admin】：{call.from_user.id} 已从群组 {call.message.chat.id} 封禁 {b} 并删除账户")
            else:
                await editMessage(call,
                                  f'🎯 管理员 {call.from_user.first_name}\n等级：{e.lv} - {first.first_name}的账户 {e.name} 操作失败')
                LOGGER.info(f"【admin】：{call.from_user.id} 对 {b} 的账户 {e.name} 删除封禁失败 ")
