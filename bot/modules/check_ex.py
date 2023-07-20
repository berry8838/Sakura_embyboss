"""
定时检测账户有无过期
"""
from datetime import timedelta

from pyrogram import filters
from sqlalchemy import and_

from bot import bot, owner, group, Now, LOGGER, prefixes
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.scheduler import Scheduler
from bot.sql_helper.sql_emby import Emby, get_all_emby, sql_update_emby
from bot.sql_helper.sql_emby2 import get_all_emby2, Emby2, sql_update_emby2


async def check_expired():
    # 询问 到期时间的用户，判断有无积分，有则续期，无就禁用
    rst = get_all_emby(and_(Emby.ex < Now, Emby.lv == 'b'))
    if rst is None:
        return LOGGER.info('【到期检测】- 等级 b 无到期用户，跳过')

    for r in rst:
        if r.us >= 30:
            b = r.us - 30
            ext = (Now + timedelta(days=30))
            if sql_update_emby(Emby.tg == r.tg, ex=ext, us=b):
                try:
                    await bot.send_message(r.tg,
                                           f'#id{r.tg} #续期账户 [{r.name}](tg://user?id={r.tg})\n在当前时间自动续期30天\n📅实时**{ext.strftime("%Y-%m-%d %H:%M:%S")}**')
                except:
                    continue
            else:
                await bot.send_message(group[0],
                                       f'#id{r.tg} #续期账户 [{r.name}](tg://user?id={r.tg})\n续期失败，请联系闺蜜（管理）')
        else:
            if await emby.emby_change_policy(r.embyid, method=True):
                if sql_update_emby(Emby.tg == r.tg, lv='c'):
                    try:
                        send = await bot.send_message(r.tg,
                                                      f'#id{r.tg} #账户到期禁用 [{r.name}](tg://user?id={r.tg})\n保留数据5天，请及时续期')
                        await send.forward(group[0])
                        LOGGER.info(f"【到期检测】- 等级 b #{r.tg} 账号 {r.name} 已到期,已禁用")
                    except:
                        continue
                else:
                    await bot.send_message(group[0],
                                           f'#id{r.tg} #账户到期禁用 [{r.name}](tg://user?id={r.tg}) 已禁用，数据库写入失败')
            else:
                await bot.send_message(group[0],
                                       f'#id{r.tg} #账户到期禁用 [{r.name}](tg://user?id={r.tg}) embyapi操作失败')

    rsc = get_all_emby(and_(Emby.ex < Now, Emby.lv == 'c'))
    if rsc is None:
        return LOGGER.info('【到期检测】- 等级 c 无到期用户，跳过')
    for c in rsc:
        if c.us >= 30:
            c_us = c.us - 30
            ex = (Now + timedelta(days=30))
            if emby.emby_change_policy(id=c.embyid, method=False):
                if sql_update_emby(Emby.tg == c.tg, lv='b', ex=ex, us=c_us):
                    try:
                        await bot.send_message(c.tg,
                                               f'#id{c.tg} #解封账户 [{c.name}](tg://user?id={c.tg})\n在当前时间自动续期30天\n📅实时{ex.strftime("%Y-%m-%d %H:%M:%S")}')
                        LOGGER.info(
                            f'【到期检测】-等级 c {c.tg} 解封账户 {c.name} 在当前时间自动续期30天 实时{ex.strftime("%Y-%m-%d %H:%M:%S")}')
                    except:
                        continue
                else:
                    await bot.send_message(group[0],
                                           f'#id{c.tg} #账户到期禁用 [{c.name}](tg://user?id={c.tg}) 已禁用，数据库写入失败')
            else:
                await bot.send_message(group[0],
                                       f'#id{c.tg} #账户到期禁用 [{c.name}](tg://user?id={c.tg}) embyapi操作失败')

        else:
            delta = c.ex + timedelta(days=5)
            if Now < delta:
                await bot.send_message(c.tg,
                                       f'#id{c.tg} #删除账户 [{c.name}](tg://user?id={c.tg})\n已到期，将为您封存账户5天，请及时续期')
            elif Now > delta:
                if await emby.emby_del(c.embyid):
                    try:
                        send = await bot.send_message(c.tg,
                                                      f'#id{c.tg} #删除账户 [{c.name}](tg://user?id={c.tg})\n已到期 5 天，执行清除任务。期待下次见')
                        await send.forward(group[0])
                        LOGGER.info(f'【封禁检测】- c {c.tg} 账号 {c.name} 到期禁用已达5天，执行删除')
                    except:
                        continue
                else:
                    await bot.send_message(group[0],
                                           f'#id{c.tg} #删除账户 [{c.name}](tg://user?id={c.tg})\n到期删除失败，请手动')

    rseired = get_all_emby2(and_(Emby2.expired == 0, Emby2.ex < Now))
    if rseired is None:
        return LOGGER.info(f'【封禁检测】- emby2 无数据，跳过')
    for e in rseired:
        if emby.emby_change_policy(e.embyid):
            if sql_update_emby2(Emby2.embyid == e.embyid, expired=1):
                try:
                    LOGGER.info(f"【封禁检测】- emby2 {e.embyid} 封印非TG账户{e.naem} Done！")
                    send = await bot.send_message(owner, f'✨**自动任务：**\n  到期封印非TG账户：`{e.name}` Done！')
                except:
                    continue
            else:
                await bot.send_message(owner, f'✨**自动任务：**\n  到期封印非TG账户：`{e.name}` 数据库更改失败')
        else:
            await bot.send_message(owner, f'✨**自动任务：**\n  到期封印非TG账户：`{e.name}` embyapi操作失败，请手动')


scheduler = Scheduler()
scheduler.add_job(check_expired, 'cron', hour=0, minute=30)


# scheduler.add_job(check_expired, 'cron', minute='*/1')

@bot.on_message(filters.command('check_ex', prefixes) & admins_on_filter)
async def check_ex_admin(_, msg):
    send = msg.reply("🍥 正在运行 【到期检测】。。。")
    await check_expired()
    await send.edit("✅ 【到期检测结束】")
