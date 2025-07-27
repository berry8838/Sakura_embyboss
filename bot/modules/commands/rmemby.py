from pyrogram import filters

from bot import bot, prefixes, LOGGER
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import deleteMessage, editMessage, sendMessage
from bot.func_helper.utils import tem_deluser
from bot.func_helper.cloudflare_api import delete_user_domain
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
        if await emby.emby_del(id=e.embyid):
            # 删除 Cloudflare 三级域名
            domain_deleted = False
            domain_error = None
            
            if e.name:
                # 尝试用原始用户名删除域名
                domain_success, domain_error = await delete_user_domain(e.name)
                if domain_success:
                    domain_deleted = True
                    LOGGER.info(f"【删除域名成功】：{e.name}")
                else:
                    # 如果用户名删除失败，尝试用用户名+密码组合删除
                    if e.pwd2:
                        domain_success2, domain_error2 = await delete_user_domain(f"{e.name}-{e.pwd2}")
                        if domain_success2:
                            domain_deleted = True
                            LOGGER.info(f"【删除域名成功】：{e.name}-{e.pwd2}")
                        else:
                            LOGGER.warning(f"【删除域名失败】：{e.name} - {domain_error}, {e.name}-{e.pwd2} - {domain_error2}")
                    else:
                        LOGGER.warning(f"【删除域名失败】：{e.name} - {domain_error}")
            
            sql_update_emby(Emby.embyid == e.embyid, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None, ex=None)
            tem_deluser()
            sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})'
            
            # 构建回复消息
            success_msg = f'🎯 done，管理员 {sign_name} 已将 [{first.first_name}](tg://user?id={e.tg}) 账户 {e.name} 删除。'
            if domain_deleted:
                success_msg += "\n🌐 三级域名已同步删除。"
            elif domain_error:
                success_msg += f"\n⚠️ 三级域名删除失败：{domain_error}"
            
            try:
                await reply.edit(success_msg)
                await bot.send_message(e.tg, f'🎯 done，管理员 {sign_name} 已将 您的账户 {e.name} 删除。')
            except:
                pass
            LOGGER.info(f"【admin】：管理员 {sign_name} 执行删除 {first.first_name}-{e.tg} 账户 {e.name}")
    else:
        await reply.edit(f"💢 [ta](tg://user?id={b}) 还没有注册账户呢")
@bot.on_message(filters.command('only_rm_record', prefixes) & admins_on_filter)
async def only_rm_record(_, msg):
    await deleteMessage(msg)
    try:
        tg_id = int(msg.command[1])
    except (IndexError, ValueError):
        return await sendMessage(msg, "❌ 使用格式：/only_rm_record tg_id")

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
    
    # 获取用户名用于删除域名
    username = None
    pwd2 = None
    if not emby_id.isdigit():  # 如果输入的是用户名而不是ID
        username = emby_id
        # 尝试从数据库获取完整信息
        e = sql_get_emby(name=emby_id)
        if e:
            pwd2 = e.pwd2
    else:
        # 通过 embyid 查找用户名
        e = sql_get_emby(emby_id)
        if e:
            username = e.name
            pwd2 = e.pwd2
    
    res = await emby.emby_del(emby_id)
    if not res:
        success, embyuser = await emby.get_emby_user_by_name(emby_id)
        if not success:
            return await sendMessage(msg, f"❌ 未找到此用户 {emby_id} 的记录")
        username = embyuser.get("Name")  # 获取用户名
        res = await emby.emby_del(embyuser.get("Id"))
        if not res:
            return await sendMessage(msg, f"❌ 删除用户 {emby_id} 失败")
    
    # 删除 Cloudflare 三级域名
    domain_deleted = False
    domain_error = None
    if username:
        # 先尝试用原始用户名删除
        domain_success, domain_error = await delete_user_domain(username)
        if domain_success:
            domain_deleted = True
        elif pwd2:
            # 如果失败且有pwd2，尝试用组合名称删除
            domain_success2, domain_error2 = await delete_user_domain(f"{username}-{pwd2}")
            if domain_success2:
                domain_deleted = True
            else:
                domain_error = f"{domain_error}, {domain_error2}"
        
        if not domain_deleted and domain_error:
            LOGGER.warning(f"【删除域名失败】：{username} - {domain_error}")
    
    sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'[{msg.from_user.first_name}](tg://user?id={msg.from_user.id})'
    
    # 构建回复消息
    success_msg = f"管理员 {sign_name} 已删除用户 {emby_id} 的Emby账号"
    if domain_deleted:
        success_msg += "，三级域名已同步删除"
    elif domain_error:
        success_msg += f"，但三级域名删除失败：{domain_error}"
    
    await sendMessage(msg, success_msg)
    LOGGER.info(f"管理员 {sign_name} 删除了用户 {emby_id} 的Emby账号")