"""
Syncs 功能

1.sync——groupm 群组成员同步任务，遍历数据库中等级 b 账户，tgapi检测是否仍在群组，否->封禁

2.sync——unbound 绑定同步任务，遍历服务器中users，未在数据表中找到同名数据的即 删除

3. bindall_id 遍历emby users，从数据库中匹配，更新其embyid字段

4. 小功能 - 给admin的账号开管理员后台，但是会被续期覆盖

"""
import time
from datetime import datetime, timedelta
from asyncio import sleep
from pyrogram import filters
from pyrogram.errors import FloodWait
from bot import bot, prefixes, bot_photo, LOGGER, owner, group
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.utils import tem_deluser
from bot.sql_helper.sql_emby import get_all_emby, Emby, sql_get_emby, sql_update_embys, sql_delete_emby, sql_update_emby
from bot.func_helper.msg_utils import deleteMessage, sendMessage, sendPhoto
from bot.sql_helper.sql_emby2 import sql_get_emby2
from bot.sql_helper.sql_favorites import sql_update_favorites, EmbyFavorites


@bot.on_message(filters.command('syncgroupm', prefixes) & admins_on_filter)
async def sync_emby_group(_, msg):
    await deleteMessage(msg)
    send = await sendPhoto(msg, photo=bot_photo, caption="⚡群组成员同步任务\n  **正在开启中...消灭未在群组的账户**",
                           send=True)
    sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'{msg.from_user.first_name}'
    LOGGER.info(f"{sign_name} 执行了群组成员同步任务")
    # 减少api调用
    members = [member.user.id async for member in bot.get_chat_members(group[0])]
    r = get_all_emby(Emby.lv == 'b')
    if not r:
        return await send.edit("⚡群组同步任务\n\n结束！搞毛，没有人。")
    a = b = 0
    text = ''
    start = time.perf_counter()
    for i in r:
        b += 1
        if i.tg not in members:
            if await emby.emby_del(emby_id=i.embyid):
                sql_update_emby(Emby.embyid == i.embyid, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None,
                                ex=None)
                tem_deluser()
                a += 1
                reply_text = f'{b}. #id{i.tg} - [{i.name}](tg://user?id={i.tg}) 删除\n'
                LOGGER.info(reply_text)
                sql_delete_emby(tg=i.tg)
            else:
                reply_text = f'{b}. #id{i.tg} - [{i.name}](tg://user?id={i.tg}) 删除错误\n'
                LOGGER.error(reply_text)
            text += reply_text
            try:
                await bot.send_message(i.tg, reply_text)
            except FloodWait as f:
                LOGGER.warning(str(f))
                await sleep(f.value * 1.2)
                await bot.send_message(i.tg, reply_text)
            except Exception as e:
                LOGGER.error(e)

    # 防止触发 MESSAGE_TOO_LONG 异常，text可以是4096，caption为1024，取小会使界面好看些
    n = 1000
    chunks = [text[i:i + n] for i in range(0, len(text), n)]
    for c in chunks:
        await sendMessage(msg, c + f'\n🔈 当前时间：{datetime.now().strftime("%Y-%m-%d")}')
    end = time.perf_counter()
    times = end - start
    if a != 0:
        await sendMessage(msg,
                          text=f"**⚡群组成员同步任务 结束！**\n  共检索出 {b} 个账户，处刑 {a} 个账户，耗时：{times:.3f}s")
    else:
        await sendMessage(msg, text="** 群组成员同步任务 结束！没人偷跑~**")
    LOGGER.info(f"【群组同步任务结束】 - {sign_name} 共检索出 {b} 个账户，处刑 {a} 个账户，耗时：{times:.3f}s")


@bot.on_message(filters.command('syncunbound', prefixes) & admins_on_filter)
async def sync_emby_unbound(_, msg):
    await deleteMessage(msg)
    send = await sendPhoto(msg, photo=bot_photo, caption="⚡扫描未绑定Bot任务\n  **正在开启中...消灭扫描bot的emby账户**",
                           send=True)
    sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'{msg.from_user.first_name}'
    LOGGER.info(f"{sign_name} 执行了扫描未绑定Bot任务")
    confirm_delete = False
    try:
        confirm_delete = msg.command[1]
    except:
        pass

    a = b = 0
    text = ''
    start = time.perf_counter()
    success, alluser = await emby.users()
    if not success or alluser is None:
        return await send.edit("⚡扫描未绑定Bot任务结束\n\n结束！搞毛，emby库中一个人都没有。")

    if success:
        for v in alluser:
            b += 1
            try:
                # 消灭不是管理员的账号
                if v['Policy'] and not bool(v['Policy']['IsAdministrator']):
                    embyid = v['Id']
                    # 查询无异常，并且无sql记录
                    e = sql_get_emby(embyid)
                    if e is None:
                        e1 = sql_get_emby2(name=embyid)
                        if e1 is None:
                            a += 1
                            if confirm_delete:
                                await emby.emby_del(emby_id=embyid)
                                text += f"🎯 #{v['Name']} 未绑定bot，删除\n"
                            else:
                                text += f"🎯 #{v['Name']} 未绑定bot\n"
            except Exception as e:
                LOGGER.warning(e)
        # 防止触发 MESSAGE_TOO_LONG 异常
        n = 1000
        chunks = [text[i:i + n] for i in range(0, len(text), n)]
        for c in chunks:
            await sendMessage(msg, c + f'\n**{datetime.now().strftime("%Y-%m-%d")}**')
    end = time.perf_counter()
    times = end - start
    if a != 0:
        await sendMessage(msg, text=f"⚡扫描未绑定Bot任务 done\n  共检索出 {b} 个账户， {a}个未绑定，耗时：{times:.3f}s，如需删除请输入 `/syncunbound true`")
    else:
        await sendMessage(msg, text=f"**扫描未绑定Bot任务 结束！搞毛，没有人被干掉。**")
    LOGGER.info(f"{sign_name} 扫描未绑定Bot任务结束，共检索出 {b} 个账户， {a}个未绑定，耗时：{times:.3f}s")


@bot.on_message(filters.command('bindall_id', prefixes) & filters.user(owner))
async def bindall_id(_, msg):
    await deleteMessage(msg)
    send = await msg.reply(f'** 一键更新用户们Emby_id，正在启动ing，请等待运行结束......**')
    LOGGER.info('一键更新绑定所有用户的Emby_id，正在启动ing，请等待运行结束......')
    success, rst = await emby.users()
    if not success:
        await send.edit(rst)
        LOGGER.error(rst)
        return

    unknow_txt = '**非数据库人员名单**\n\n'
    b = 0
    ls = []
    start = time.perf_counter()
    for i in rst:
        b += 1
        Name = i["Name"]
        Emby_id = i["Id"]
        e = sql_get_emby(tg=Name)
        if not e:
            unknow_txt += f'{Name}\n'
            continue
        ls.append([e.tg, Name, Emby_id])
    if sql_update_embys(some_list=ls, method='bind'):
        # 更新收藏记录
        for i in ls:
           favorites_updated = sql_update_favorites(condition=EmbyFavorites.embyname == i[1], embyid=i[2])
           if not favorites_updated:
               LOGGER.warning(f"用户 {i[1]} 的收藏记录更新失败，可能存在数据冲突")
               pass
        end = time.perf_counter()
        times = end - start
        n = 1000
        chunks = [unknow_txt[i:i + n] for i in range(0, len(unknow_txt), n)]
        for c in chunks:
            await send.reply(c + f"⚡一键更新Emby_id执行完成，耗时：{times:.3f} s")
        LOGGER.info(
            f"一键更新Emby_id执行完成。{unknow_txt}")
    else:
        await msg.reply("数据库批量更新操作出错，请检查重试")
        LOGGER.error('数据库批量更新操作出错，请检查重试')


@bot.on_message(filters.command('embyadmin', prefixes) & admins_on_filter)
async def reload_admins(_, msg):
    await deleteMessage(msg)
    e = sql_get_emby(tg=msg.from_user.id)
    if e.embyid is not None:
        await emby.emby_change_policy(emby_id=e.embyid, admin=True)
        LOGGER.info(f"{msg.from_user.first_name} - {msg.from_user.id} 开启了 emby 后台")
        await sendMessage(msg, "👮🏻 授权完成。已开启emby后台", timer=60)
    else:
        LOGGER.info(f"{msg.from_user.first_name} - {msg.from_user.id} 开启 emby 后台失败")
        await sendMessage(msg, "👮🏻 授权失败。未查询到绑定账户", timer=60)


@bot.on_message(filters.command('deleted', prefixes) & admins_on_filter)
async def clear_deleted_account(_, msg):
    await deleteMessage(msg)
    send = await msg.reply("🔍 正在运行清理程序...")
    a = b = 0
    text = '️⛔ 清理结束\n'
    async for d in bot.get_chat_members(group[0]):  # 以后别写group了,绑定一下聊天群更优雅
        b += 1
        try:
            # and d.is_member or any(keyword in l.user.first_name for keyword in keywords) 关键词检索，没模板不加了
            if d.user.is_deleted:
                await msg.chat.ban_member(d.user.id)
                sql_delete_emby(tg=d.user.id)
                a += 1
                # 打个注释，scheduler 默认出群就删号了，不需要再执行删除
                text += f'{a}. `{d.user.id}` 已注销\n'
        except Exception as e:
            LOGGER.error(e)
    await send.delete()
    n = 1024
    chunks = [text[i:i + n] for i in range(0, len(text), n)]
    for c in chunks:
        await sendMessage(msg, c)


@bot.on_message(filters.command('kick_not_emby', prefixes) & admins_on_filter & filters.group)
async def kick_not_emby(_, msg):
    await deleteMessage(msg)
    try:
        open_kick = msg.command[1]
    except:
        return await sendMessage(msg,
                                 '注意: 此操作会将 当前群组中无emby账户的选手kick, 如确定使用请输入 `/kick_not_emby true`')
    if open_kick == 'true':
        sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'{msg.from_user.first_name}'
        LOGGER.info(f"{sign_name} 执行了踢出非emby用户的操作")
        embyusers = get_all_emby(Emby.embyid is not None and Emby.embyid != '')
        # get tgid
        embytgs = []
        if embyusers:
            embytgs = [i.tg for i in embyusers]
        chat_members = [member.user.id async for member in bot.get_chat_members(chat_id=msg.chat.id)]
        until_date = datetime.now() + timedelta(minutes=1)
        for cmember in chat_members:
            if cmember not in embytgs:
                try:
                    await msg.chat.ban_member(cmember, until_date=until_date)
                    await sendMessage(msg, f'{cmember} 已踢出', send=True)
                    LOGGER.info(f"{cmember} 已踢出")
                except Exception as e:
                    LOGGER.info(f"踢出 {cmember} 失败，原因: {e}")
                    pass
@bot.on_message(filters.command('restore_from_db', prefixes) & filters.user(owner))
async def restore_from_db(_, msg):
    await deleteMessage(msg)
    try:
        confirm_restore = msg.command[1]
    except:
        return await sendMessage(msg,
                                 '注意: 此操作会将 从数据库中恢复用户到Emby中, 请在需要恢复的群组中执行此命令, 如确定使用请输入 `/restore_from_db true`')
    if confirm_restore == 'true':
        sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'{msg.from_user.first_name}'    
        LOGGER.info(
            f"{sign_name} 执行了从数据库中恢复用户到Emby中的操作")
        embyusers = get_all_emby(Emby.embyid is not None and Emby.embyid != '')
        # 获取当前执行命令的群组成员
        chat_members = [member.user.id async for member in bot.get_chat_members(chat_id=msg.chat.id)]
        await sendMessage(msg, '** 恢复中, 请耐心等待... **')
        text = ''
        for embyuser in embyusers:
            if embyuser.tg in chat_members:
                try:
                    # emby api操作
                    data = await emby.emby_create(name=embyuser.name, days=embyuser.us)
                    if not data:
                        text += f'**- ❎ 已有此账户名\n- ❎ 或检查有无特殊字符\n- ❎ 或emby服务器连接不通\n- ❎ 跳过恢复用户：#id{embyuser.tg} - [{embyuser.name}](tg://user?id={embyuser.tg}) \n**'
                        LOGGER.error(
                            f"【恢复账户】：重复账户 or 未知错误！{embyuser.name} 恢复失败！")
                    else:
                        tg = embyuser.tg
                        embyid = data[0]
                        pwd = data[1]
                        sql_update_emby(Emby.tg == tg, embyid=embyid, pwd=pwd)
                        
                        # 更安全的收藏记录更新，带错误处理
                        favorites_updated = sql_update_favorites(condition=EmbyFavorites.embyname == embyuser.name, embyid=embyid)
                        if not favorites_updated:
                            LOGGER.warning(f"用户 {embyuser.name} 的收藏记录更新失败，可能存在数据冲突")
                            text += f'**- ⚠️ 恢复用户：#id{embyuser.tg} - [{embyuser.name}](tg://user?id={embyuser.tg}) 成功，但收藏记录更新失败\n**'
                        else:
                            text += f'**- ✅ 恢复用户：#id{embyuser.tg} - [{embyuser.name}](tg://user?id={embyuser.tg}) 成功！\n**'
                        
                        LOGGER.info(f"恢复 #id{embyuser.tg} - [{embyuser.name}](tg://user?id={embyuser.tg}) 成功")
                except Exception as e:
                    text += f'**- ❎ 恢复 #id{embyuser.tg} - [{embyuser.name}](tg://user?id={embyuser.tg}) 失败 \n**'
                    LOGGER.info(f"恢复 #id{embyuser.tg} - [{embyuser.name}](tg://user?id={embyuser.tg}) 失败，原因: {e}")
                    pass
        # 防止触发 MESSAGE_TOO_LONG 异常，text可以是4096，caption为1024，取小会使界面好看些
        n = 1000
        chunks = [text[i:i + n] for i in range(0, len(text), n)]
        for c in chunks:
            await sendMessage(msg, c + f'\n🔈 当前时间：{datetime.now().strftime("%Y-%m-%d")}')
        await sendMessage(msg, '** 恢复完成 **')


@bot.on_message(filters.command('scan_embyname', prefixes) & admins_on_filter)
async def scan_embyname(_, msg):
    await deleteMessage(msg)
    send = await msg.reply("🔍 正在扫描重复用户名...")
    sign_name = f'{msg.sender_chat.title}' if msg.sender_chat else f'{msg.from_user.first_name}'
    LOGGER.info(
        f"{sign_name} 执行了扫描重复用户名操作")

    # 获取所有有效的emby用户
    emby_users = get_all_emby(Emby.name is not None)
    if not emby_users:
        return await send.edit("⚡扫描重复用户名任务\n\n结束！数据库中没有用户。")

    # 用字典统计相同name的用户
    name_count = {}
    for user in emby_users:
        if user.name:
            if user.name in name_count:
                name_count[user.name].append(user)
            else:
                name_count[user.name] = [user]
    # 筛选出重复的用户名
    duplicate_names = {name: users for name,
                       users in name_count.items() if len(users) > 1}
    if not duplicate_names:
        return await send.edit("✅ 没有发现重复的用户名！")
    text = "🔍 发现以下重复用户名：\n\n"
    for name, users in duplicate_names.items():
        text += f"用户名: {name}\n"
        for user in users:
            text += f"- TG ID: `{user.tg}` | Emby ID: `{user.embyid}`\n"
        text += "\n"
    text += "\n使用 `/only_rm_record tg_id` 可删除指定用户的数据库记录（此命令不会删除 Emby 账号）"
    # 分段发送消息，避免超过长度限制
    n = 1000
    chunks = [text[i:i + n] for i in range(0, len(text), n)]
    for c in chunks:
        await sendMessage(msg, c)
    LOGGER.info(
        f"{sign_name} 扫描重复用户名任务结束，共发现 {len(duplicate_names)} 个重复用户名")
