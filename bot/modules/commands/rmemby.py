from pyrogram import filters

from bot import bot, prefixes, LOGGER
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import deleteMessage, editMessage, sendMessage
from bot.func_helper.utils import tem_deluser
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby, sql_delete_emby_by_tg, sql_delete_emby


# 删除账号命令
@bot.on_message(filters.command('rmemby', prefixes) & admins_on_filter)
async def rmemby_user(_, msg):
    await deleteMessage(msg)
    reply = await msg.reply("🍉 正在处理ing....")
    if msg.reply_to_message is None:
        try:
            b = msg.command[1]  # name
        except (IndexError, KeyError, ValueError):
            return await editMessage(reply,
                                     "🔔 **使用格式：**/rmemby tg_id或回复某人 \n/rmemby [emby用户名亦可]")
        e = sql_get_emby(tg=b)
    else:
        b = msg.reply_to_message.from_user.id
        e = sql_get_emby(tg=b)

    if e is None:
        return await reply.edit(f"♻️ 没有检索到 {b} 账户，请确认重试或手动检查。")

    if e.embyid is not None:
        first = await bot.get_chat(e.tg)
        if await emby.emby_del(emby_id=e.embyid):
            sql_update_emby(Emby.embyid == e.embyid, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None, ex=None)
            tem_deluser()
            sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})'
            try:
                await reply.edit(
                    f'🎯 done，管理员  {sign_name} 已将 [{first.first_name}](tg://user?id={e.tg}) 账户 {e.name} 删除。')
                await bot.send_message(e.tg,
                                       f'🎯 done，管理员 {sign_name} 已将 您的账户 {e.name} 删除。')
            except:
                pass
            LOGGER.info(
                f"【admin】：管理员 {sign_name} 执行删除 {first.first_name}-{e.tg} 账户 {e.name}")
    else:
        await reply.edit(f"💢 [ta](tg://user?id={b}) 还没有注册账户呢")
@bot.on_message(filters.command('only_rm_record', prefixes) & admins_on_filter)
async def only_rm_record(_, msg):
    await deleteMessage(msg)
    tg_id = None
    if msg.reply_to_message is None:
        try:
            tg_id = int(msg.command[1])
        except (IndexError, ValueError):
            tg_id = None
    else:
        tg_id = msg.reply_to_message.from_user.id
    if tg_id is None:
        return await sendMessage(msg, "❌ 使用格式：/only_rm_record tg_id或回复用户的消息")

    e = sql_get_emby(tg=tg_id)
    if not e:
        return await sendMessage(msg, f"❌ 未找到 TG ID: {tg_id} 的记录")

    try:
        res = sql_delete_emby_by_tg(tg_id)
        sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})'
        if res:
            await sendMessage(msg, f"管理员 {sign_name} 已删除 TG ID: {tg_id} 的数据库记录")
            LOGGER.info(
                f"管理员 {sign_name} 删除了用户 {tg_id} 的数据库记录")
        else:
            await sendMessage(msg, f"❌ 删除记录失败")
            LOGGER.error(
                f"管理员 {sign_name} 删除用户 {tg_id} 的数据库记录失败")
    except Exception as e:
        await sendMessage(msg, f"❌ 删除记录失败: {str(e)}")

        LOGGER.error(f"删除用户 {tg_id} 的数据库记录失败: {str(e)}")


@bot.on_message(filters.command('only_rm_emby', prefixes) & admins_on_filter)
async def only_rm_emby(_, msg):
    await deleteMessage(msg)
    try:
        emby_id = msg.command[1]
    except (IndexError, ValueError):
        return await sendMessage(msg, "❌ 使用格式：/only_rm_emby embyid或者embyname")
    
    res = await emby.emby_del(emby_id=emby_id)
    if not res:
        # 使用 emby_name 获取此用户的 emby_id
        success, embyuser = await emby.get_emby_user_by_name(emby_name=emby_id)
        if not success:
            return await sendMessage(msg, f"❌ 未找到此用户 {emby_id} 的记录")
        res = await emby.emby_del(emby_id=embyuser.get("Id"))
        if not res:
            return await sendMessage(msg, f"❌ 删除用户 {emby_id} 失败")
        sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})'
        await sendMessage(msg, f"管理员 {sign_name} 已删除用户 {emby_id} 的Emby账号")
        LOGGER.info(
            f"管理员 {sign_name} 删除了用户 {emby_id} 的Emby账号")