import time

from pyrogram import filters

from bot import bot, owner, prefixes, extra_emby_libs, LOGGER, Now
from bot.func_helper.msg_utils import sendMessage, deleteMessage
from bot.sql_helper.sql_emby import get_all_emby, Emby
from bot.func_helper.emby import emby

# embylibs_block
@bot.on_message(filters.command('embylibs_blockall', prefixes) & filters.user(owner))
async def embylibs_blockall(_, msg):
    await deleteMessage(msg)
    reply = await msg.reply(f"🍓 正在处理ing····, 正在更新所有用户的媒体库访问权限")
    rst = get_all_emby(Emby.embyid is not None)
    if rst is None:
        LOGGER.info(
            f"【关闭媒体库任务】 -{msg.from_user.first_name}({msg.from_user.id}) 没有检测到任何emby账户，结束")
        return await reply.edit("⚡【关闭媒体库任务】\n\n结束，没有一个有号的")
    allcount = 0
    successcount = 0
    start = time.perf_counter()
    text = ''
    # 获取所有媒体库的文件夹ID
    all_libs = await emby.get_emby_libs()
    all_folder_ids = await emby.get_folder_ids_by_names(all_libs)
    for i in rst:
        success, rep = await emby.user(emby_id=i.embyid)
        if success:
            allcount += 1
            try:
                # 新版本API：使用EnabledFolders控制访问
                policy = rep.get("Policy", {})
                original_enable_all_folders = policy.get("EnableAllFolders")
                
                if original_enable_all_folders is True:
                    # 如果启用所有文件夹，需要先获取所有文件夹ID
                    current_enabled_folder_ids = all_folder_ids.copy()
                else:
                    current_enabled_folder_ids = policy.get("EnabledFolders", [])
                
                # 从启用列表中移除所有媒体库的文件夹ID（保留空列表，即关闭所有媒体库）
                new_enabled_folder_ids = [folder_id for folder_id in current_enabled_folder_ids 
                                         if folder_id not in all_folder_ids]
                
                # 更新用户策略，关闭所有媒体库
                re = await emby.update_user_enabled_folder(emby_id=i.embyid, enabled_folder_ids=new_enabled_folder_ids, enable_all_folders=False)
                if re is True:
                    successcount += 1
                    text += f'已关闭了 [{i.name}](tg://user?id={i.tg}) 的媒体库权限\n'
                else:
                    text += f'🌧️ 关闭失败 [{i.name}](tg://user?id={i.tg}) 的媒体库权限\n'
            except Exception as e:
                LOGGER.error(f"关闭媒体库权限失败: {i.name} - {str(e)}")
                text += f'🌧️ 关闭失败 [{i.name}](tg://user?id={i.tg}) 的媒体库权限\n'
    # 防止触发 MESSAGE_TOO_LONG 异常
    n = 1000
    chunks = [text[i:i + n] for i in range(0, len(text), n)]
    for c in chunks:
        await msg.reply(c + f'\n**{Now.strftime("%Y-%m-%d %H:%M:%S")}**')
    end = time.perf_counter()
    times = end - start
    if allcount != 0:
        await sendMessage(msg,
                          text=f"⚡#关闭媒体库任务 done\n  共检索出 {allcount} 个账户，成功关闭 {successcount}个，耗时：{times:.3f}s")
    else:
        await sendMessage(msg, text=f"**#关闭媒体库任务 结束！搞毛，没有人被干掉。**")
    LOGGER.info(
        f"【关闭媒体库任务结束】 - {msg.from_user.id} 共检索出 {allcount} 个账户，成功关闭 {successcount}个，耗时：{times:.3f}s")

# embylibs_unblock
@bot.on_message(filters.command('embylibs_unblockall', prefixes) & filters.user(owner))
async def embylibs_unblockall(_, msg):
    await deleteMessage(msg)
    reply = await msg.reply(f"🍓 正在处理ing····, 正在更新所有用户的媒体库访问权限")
    rst = get_all_emby(Emby.embyid is not None)
    if rst is None:
        LOGGER.info(
            f"【开启媒体库任务】 -{msg.from_user.first_name}({msg.from_user.id}) 没有检测到任何emby账户，结束")
        return await reply.edit("⚡【开启媒体库任务】\n\n结束，没有一个有号的")
    allcount = 0
    successcount = 0
    start = time.perf_counter()
    text = ''
    for i in rst:
        success, rep = await emby.user(emby_id=i.embyid)
        if success:
            allcount += 1
            try:
                # 新版本API：使用EnabledFolders控制访问
                # 开启所有媒体库，设置 enable_all_folders=True
                re = await emby.update_user_enabled_folder(emby_id=i.embyid, enable_all_folders=True)
                if re is True:
                    successcount += 1
                    text += f'已开启了 [{i.name}](tg://user?id={i.tg}) 的媒体库权限\n'
                else:
                    text += f'🌧️ 开启失败 [{i.name}](tg://user?id={i.tg}) 的媒体库权限\n'
            except Exception as e:
                LOGGER.error(f"开启媒体库权限失败: {i.name} - {str(e)}")
                text += f'🌧️ 开启失败 [{i.name}](tg://user?id={i.tg}) 的媒体库权限\n'
    # 防止触发 MESSAGE_TOO_LONG 异常
    n = 1000
    chunks = [text[i:i + n] for i in range(0, len(text), n)]
    for c in chunks:
        await msg.reply(c + f'\n**{Now.strftime("%Y-%m-%d %H:%M:%S")}**')
    end = time.perf_counter()
    times = end - start
    if allcount != 0:
        await sendMessage(msg,
                          text=f"⚡#开启媒体库任务 done\n  共检索出 {allcount} 个账户，成功开启 {successcount}个，耗时：{times:.3f}s")
    else:
        await sendMessage(msg, text=f"**#开启媒体库任务 结束！搞毛，没有人被干掉。**")
    LOGGER.info(
        f"【开启媒体库任务结束】 - {msg.from_user.id} 共检索出 {allcount} 个账户，成功开启 {successcount}个，耗时：{times:.3f}s")

@bot.on_message(filters.command('extraembylibs_blockall', prefixes) & filters.user(owner))
async def extraembylibs_blockall(_, msg):
    await deleteMessage(msg)
    reply = await msg.reply(f"🍓 正在处理ing····, 正在更新所有用户的额外媒体库访问权限")

    rst = get_all_emby(Emby.embyid is not None)
    if rst is None:
        LOGGER.info(
            f"【关闭额外媒体库任务】 -{msg.from_user.first_name}({msg.from_user.id}) 没有检测到任何emby账户，结束")
        return await reply.edit("⚡【关闭额外媒体库任务】\n\n结束，没有一个有号的")

    allcount = 0
    successcount = 0
    start = time.perf_counter()
    text = ''
    # 获取额外媒体库对应的文件夹ID
    extra_folder_ids = await emby.get_folder_ids_by_names(extra_emby_libs)
    for i in rst:
        success, rep = await emby.user(emby_id=i.embyid)
        if success:
            allcount += 1
            try:
                # 新版本API：使用EnabledFolders控制访问
                policy = rep.get("Policy", {})
                current_enabled_folders = policy.get("EnabledFolders", [])
                enable_all_folders = policy.get("EnableAllFolders", False)
                
                if enable_all_folders is True:
                    # 如果启用所有文件夹，需要先获取所有文件夹ID，然后移除额外媒体库
                    all_libs = await emby.get_emby_libs()
                    all_folder_ids = await emby.get_folder_ids_by_names(all_libs)
                    # 从所有文件夹中移除额外媒体库
                    current_enabled_folders = [folder_id for folder_id in all_folder_ids 
                                              if folder_id not in extra_folder_ids]
                    re = await emby.update_user_enabled_folder(emby_id=i.embyid, enabled_folder_ids=current_enabled_folders, enable_all_folders=False)
                else:
                    # 从启用列表中移除额外媒体库的文件夹ID
                    current_enabled_folders = [folder_id for folder_id in current_enabled_folders 
                                              if folder_id not in extra_folder_ids]
                    re = await emby.update_user_enabled_folder(emby_id=i.embyid, enabled_folder_ids=current_enabled_folders, enable_all_folders=False)
                
                if re is True:
                    successcount += 1
                    text += f'已关闭了 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
                else:
                    text += f'🌧️ 关闭失败 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
            except Exception as e:
                LOGGER.error(f"关闭额外媒体库权限失败: {i.name} - {str(e)}")
                text += f'🌧️ 关闭失败 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
    # 防止触发 MESSAGE_TOO_LONG 异常
    n = 1000
    chunks = [text[i:i + n] for i in range(0, len(text), n)]
    for c in chunks:
        await msg.reply(c + f'\n**{Now.strftime("%Y-%m-%d %H:%M:%S")}**')
    end = time.perf_counter()
    times = end - start
    if allcount != 0:
        await sendMessage(msg,
                          text=f"⚡#关闭额外媒体库任务 done\n  共检索出 {allcount} 个账户，成功关闭 {successcount}个，耗时：{times:.3f}s")
    else:
        await sendMessage(msg, text=f"**#关闭额外媒体库任务 结束！搞毛，没有人被干掉。**")
    LOGGER.info(
        f"【关闭额外媒体库任务结束】 - {msg.from_user.id} 共检索出 {allcount} 个账户，成功关闭 {successcount}个，耗时：{times:.3f}s")


@bot.on_message(filters.command('extraembylibs_unblockall', prefixes) & filters.user(owner))
async def extraembylibs_unblockall(_, msg):
    await deleteMessage(msg)
    reply = await msg.reply(f"🍓 正在处理ing····, 正在更新所有用户的额外媒体库访问权限")

    rst = get_all_emby(Emby.embyid is not None)
    if rst is None:
        LOGGER.info(
            f"【开启额外媒体库任务】 -{msg.from_user.first_name}({msg.from_user.id}) 没有检测到任何emby账户，结束")
        return await reply.edit("⚡【开启额外媒体库任务】\n\n结束，没有一个有号的")

    allcount = 0
    successcount = 0
    start = time.perf_counter()
    text = ''
    # 获取额外媒体库对应的文件夹ID
    extra_folder_ids = await emby.get_folder_ids_by_names(extra_emby_libs)
    for i in rst:
        success, rep = await emby.user(emby_id=i.embyid)
        if success:
            allcount += 1
            try:
                # 新版本API：使用EnabledFolders控制访问
                policy = rep.get("Policy", {})
                current_enabled_folders = policy.get("EnabledFolders", [])
                enable_all_folders = policy.get("EnableAllFolders", False)
                
                if enable_all_folders is True:
                    # 如果已经启用所有文件夹，则不需要修改（因为已经可以看到所有文件夹）
                    re = await emby.update_user_enabled_folder(emby_id=i.embyid, enable_all_folders=True)
                else:
                    # 将额外媒体库的文件夹ID添加到启用列表中
                    current_enabled_folders = list(set(current_enabled_folders + extra_folder_ids))
                    re = await emby.update_user_enabled_folder(emby_id=i.embyid, enabled_folder_ids=current_enabled_folders, enable_all_folders=False)
                
                if re is True:
                    successcount += 1
                    text += f'已开启了 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
                else:
                    text += f'🌧️ 开启失败 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
            except Exception as e:
                LOGGER.error(f"开启额外媒体库权限失败: {i.name} - {str(e)}")
                text += f'🌧️ 开启失败 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
    # 防止触发 MESSAGE_TOO_LONG 异常
    n = 1000
    chunks = [text[i:i + n] for i in range(0, len(text), n)]
    for c in chunks:
        await msg.reply(c + f'\n**{Now.strftime("%Y-%m-%d %H:%M:%S")}**')
    end = time.perf_counter()
    times = end - start
    if allcount != 0:
        await sendMessage(msg,
                          text=f"⚡#开启额外媒体库任务 done\n  共检索出 {allcount} 个账户，成功开启 {successcount}个，耗时：{times:.3f}s")
    else:
        await sendMessage(msg, text=f"**#开启额外媒体库任务 结束！搞毛，没有人被干掉。**")
    LOGGER.info(
        f"【开启额外媒体库任务结束】 - {msg.from_user.id} 共检索出 {allcount} 个账户，成功开启 {successcount}个，耗时：{times:.3f}s")
