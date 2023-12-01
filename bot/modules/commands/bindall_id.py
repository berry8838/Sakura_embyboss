import time

from pyrogram import filters

from bot import bot, prefixes, owner, LOGGER
from bot.func_helper.emby import emby
from bot.func_helper.msg_utils import deleteMessage
from bot.sql_helper.sql_emby import sql_update_embys, sql_get_emby


@bot.on_message(filters.command('bindall_id', prefixes) & filters.user(owner))
async def renew_all(_, msg):
    await deleteMessage(msg)
    send = await msg.reply(f'** 一键更新用户们Emby_id，正在启动ing，请等待运行结束......**')
    LOGGER.info('一键更新绑定所有用户的Emby_id，正在启动ing，请等待运行结束......')
    success, rst = await emby.users()
    if not success:
        await send.edit(rst)
        LOGGER.error(rst)
        return
    unknow_txt = '非数据库人员名单'
    b = 0
    ls = []
    start = time.perf_counter()
    for i in rst:
        b += 1
        Name = i["Name"]
        Emby_id = i["Id"]
        e = sql_get_emby(tg=Name)
        if not e or e.embyid:
            unknow_txt += f'{Name}\n'
        else:
            if e.embyid != Emby_id:
                ls.append([Name, Emby_id])
    if sql_update_embys(some_list=ls, method='bind'):
        end = time.perf_counter()
        times = end - start
        await send.edit(
            f"⚡一键更新Emby_id执行完成，耗时：{times} s。剩余一些账户不在数据库，请过目\n\n{unknow_txt}")
        LOGGER.info(
            f"一键更新Emby_id执行完成。{unknow_txt}")
    else:
        await msg.reply("数据库批量更新操作出错，请检查重试")
        LOGGER.error('数据库批量更新操作出错，请检查重试.')
