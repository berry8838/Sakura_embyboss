import time
from datetime import datetime, timezone, timedelta

from pyrogram import filters

from bot import bot, _open, sakura_b, owner,prefixes, extra_emby_libs,LOGGER, Now
from bot.func_helper.fix_bottons import checkin_button
from bot.func_helper.msg_utils import sendMessage, deleteMessage
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, get_all_emby, Emby
from bot.func_helper.emby import emby

@bot.on_message(filters.command('extraembylibs_blockall', prefixes) & filters.user(owner))
async def extraembylibs_blockall(_, msg):
    await deleteMessage(msg)
    reply = await msg.reply(f"🍓 正在处理ing····, 正在更新所有用户的额外媒体库访问权限，时间较长，请耐心等待(完成后会有提示)")

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
        success, rep = emby.user(embyid=i.embyid)
        if success:
            allcount += 1
            try:
                currentblock = rep["Policy"]["BlockedMediaFolders"]
            except KeyError:
                pass
            else:
                if not set(extra_emby_libs).issubset(set(currentblock)):
                    currentblock = list(set(rep["Policy"]["BlockedMediaFolders"] + extra_emby_libs))
                    re = await emby.emby_block(i.embyid, 0, block=currentblock)
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
        await sendMessage(msg, text=f"⚡#关闭额外媒体库任务 done\n  共检索出 {allcount} 个账户，成功关闭 {successcount}个，耗时：{times:.3f}s")
    else:
        await sendMessage(msg, text=f"**#关闭额外媒体库任务 结束！搞毛，没有人被干掉。**")
    LOGGER.info(f"【关闭额外媒体库任务结束】 - {msg.from_user.id} 共检索出 {allcount} 个账户，成功关闭 {successcount}个，耗时：{times:.3f}s")
