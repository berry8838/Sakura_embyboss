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
    all_libs = await emby.get_emby_libs()
    for i in rst:
        success, rep = await emby.user(emby_id=i.embyid)
        if success:
            allcount += 1
            currentblock = ['播放列表'] + all_libs
            # 去除相同的元素
            currentblock = list(set(currentblock))
            re = await emby.emby_block(emby_id=i.embyid, stats=0, block=currentblock)
            if re is True:
                successcount += 1
                text += f'已关闭了 [{i.name}](tg://user?id={i.tg}) 的媒体库权限\n'
            else:
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
            currentblock = ['播放列表']
            # 去除相同的元素
            re = await emby.emby_block(emby_id=i.embyid, stats=0, block=currentblock)
            if re is True:
                successcount += 1
                text += f'已开启了 [{i.name}](tg://user?id={i.tg}) 的媒体库权限\n'
            else:
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
    for i in rst:
        success, rep = await emby.user(emby_id=i.embyid)
        if success:
            allcount += 1
            try:
                currentblock = list(set(rep["Policy"]["BlockedMediaFolders"] + ['播放列表']))
            except KeyError:
                currentblock = ['播放列表'] + extra_emby_libs
            if not set(extra_emby_libs).issubset(set(currentblock)):
                # 去除相同的元素
                currentblock = list(set(currentblock + extra_emby_libs))
                re = await emby.emby_block(emby_id=i.embyid, stats=0, block=currentblock)
                if re is True:
                    successcount += 1
                    text += f'已关闭了 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
                else:
                    text += f'🌧️ 关闭失败 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
            else:
                successcount += 1
                text += f'已关闭了 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
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
    for i in rst:
        success, rep = await emby.user(emby_id=i.embyid)
        if success:
            allcount += 1
            try:
                currentblock = list(set(rep["Policy"]["BlockedMediaFolders"] + ['播放列表']))
                # 保留不同的元素
                currentblock = [x for x in currentblock if x not in extra_emby_libs] + [x for x in extra_emby_libs if
                                                                                        x not in currentblock]
            except KeyError:
                currentblock = ['播放列表']
            if not set(extra_emby_libs).issubset(set(currentblock)):
                re = await emby.emby_block(emby_id=i.embyid, stats=0, block=currentblock)
                if re is True:
                    successcount += 1
                    text += f'已开启了 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
                else:
                    text += f'🌧️ 开启失败 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
            else:
                successcount += 1
                text += f'已开启了 [{i.name}](tg://user?id={i.tg}) 的额外媒体库权限\n'
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
