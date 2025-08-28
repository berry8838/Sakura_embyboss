"""
定时检测账户有无过期
"""
from datetime import timedelta, datetime

from pyrogram.errors import FloodWait
from sqlalchemy import and_
from asyncio import sleep
from bot import bot, group, LOGGER, _open, config
from bot.func_helper.emby import emby
from bot.func_helper.utils import tem_deluser
from bot.sql_helper.sql_emby import Emby, get_all_emby, sql_update_emby
from bot.sql_helper.sql_emby2 import get_all_emby2, Emby2, sql_update_emby2


async def check_expired():
    # 询问 到期时间的用户，判断有无积分，有则续期，无就禁用
    rst = get_all_emby(and_(Emby.ex < datetime.now(), Emby.lv == 'b'))
    if rst is None:
        return LOGGER.info('【到期检测】- 等级 b 无到期用户，跳过')
    ext = (datetime.now() + timedelta(days=30))
    for r in rst:
        if r.us >= 30:
            b = r.us - 30
            if sql_update_emby(Emby.tg == r.tg, ex=ext, us=b):
                text = f'【到期检测】\n#id{r.tg} 续期账户 [{r.name}](tg://user?id={r.tg})\n' \
                       f'在当前时间自动续期30天\n' \
                       f'📅实时到期：{ext.strftime("%Y-%m-%d %H:%M:%S")}'
                LOGGER.info(text)
            else:
                text = f'【到期检测】\n#id{r.tg} 续期账户 [{r.name}](tg://user?id={r.tg})\n' \
                       f'自动续期失败，请联系闺蜜（管理）'
                LOGGER.error(text)
            try:
                await bot.send_message(r.tg, text)
            except FloodWait as f:
                LOGGER.warning(str(f))
                await sleep(f.value * 1.2)
                await bot.send_message(r.tg, text)
            except Exception as e:
                LOGGER.error(e)

        elif _open.exchange and r.iv >= _open.exchange_cost:
            b = r.iv - _open.exchange_cost
            if sql_update_emby(Emby.tg == r.tg, ex=ext, iv=b):
                text = f'【到期检测】\n#id{r.tg} 续期账户 [{r.name}](tg://user?id={r.tg})\n' \
                       f'在当前时间自动续期30天\n' \
                       f'📅实时到期: {ext.strftime("%Y-%m-%d %H:%M:%S")}'
                LOGGER.info(text)
            else:
                text = f'【到期检测】\n#id{r.tg} 续期账户 [{r.name}](tg://user?id={r.tg})\n续期失败，请联系闺蜜（管理）'
                LOGGER.error(text)
            try:
                await bot.send_message(r.tg, text)
            except FloodWait as f:
                LOGGER.warning(str(f))
                await sleep(f.value * 1.2)
                await bot.send_message(r.tg, text)
            except Exception as e:
                LOGGER.error(e)

        else:
            if await emby.emby_change_policy(r.embyid, method=True):
                dead_day = r.ex + timedelta(days=config.freeze_days)
                if sql_update_emby(Emby.tg == r.tg, lv='c'):
                    text = f'【到期检测】\n#id{r.tg} 到期禁用 [{r.name}](tg://user?id={r.tg})\n将为您封存至 {dead_day.strftime("%Y-%m-%d")}，请及时续期'
                    LOGGER.info(text)
                else:
                    text = f'【到期检测】\n#id{r.tg} 到期禁用 [{r.name}](tg://user?id={r.tg}) 已禁用，数据库写入失败'
                    LOGGER.warning(text)
            else:
                text = f'【到期检测】\n#id{r.tg} 到期禁用 [{r.name}](tg://user?id={r.tg}) embyapi操作失败'
                LOGGER.error(text)
            try:
                send = await bot.send_message(r.tg, text)
                await send.forward(group[0])
            except FloodWait as f:
                LOGGER.warning(str(f))
                await sleep(f.value * 1.2)
                send = await bot.send_message(r.tg, text)
                await send.forward(group[0])
            except Exception as e:
                LOGGER.error(e)

    rsc = get_all_emby(and_(Emby.ex < datetime.now(), Emby.lv == 'c'))
    if rsc is None:
        return LOGGER.info('【到期检测】- 等级 c 无到期用户，跳过')
    for c in rsc:
        if c.us >= 30:
            c_us = c.us - 30
            if await emby.emby_change_policy(id=c.embyid, method=False):
                if sql_update_emby(Emby.tg == c.tg, lv='b', ex=ext, us=c_us):
                    text = f'【到期检测】\n#id{c.tg} 解封账户 [{c.name}](tg://user?id={c.tg})\n' \
                           f'在当前时间自动续期30天\n📅实时到期: {ext.strftime("%Y-%m-%d %H:%M:%S")}'
                    LOGGER.info(text)
                else:
                    text = f'【到期检测】\n#id{c.tg} 解封账户 [{c.name}](tg://user?id={c.tg}) 数据库写入失败，请联系管理'
                    LOGGER.warning(text)
            else:
                text = f'【到期检测】\n#id{c.tg} 解封账户 [{c.name}](tg://user?id={c.tg}) embyapi操作失败'
                LOGGER.error(text)
            try:
                await bot.send_message(c.tg, text)
            except FloodWait as f:
                LOGGER.warning(str(f))
                await sleep(f.value * 1.2)
                await bot.send_message(c.tg, text)
            except Exception as e:
                LOGGER.error(e)

        elif _open.exchange and c.iv >= _open.exchange_cost:
            c_iv = c.iv - _open.exchange_cost
            if await emby.emby_change_policy(id=c.embyid, method=False):
                if sql_update_emby(Emby.tg == c.tg, lv='b', ex=ext, iv=c_iv):
                    text = f'【到期检测】\n#id{c.tg} 解封账户 [{c.name}](tg://user?id={c.tg})\n在当前时间自动续期30天\n📅实时到期：{ext.strftime("%Y-%m-%d %H:%M:%S")}'
                    LOGGER.info(text)
                else:
                    text = f'【到期检测】\n#id{c.tg} 解封账户 [{c.name}](tg://user?id={c.tg}) 已禁用，数据库写入失败，请联系管理'
                    LOGGER.warning(text)
            else:
                text = f'【到期检测】\n#id{c.tg} 解封账户 [{c.name}](tg://user?id={c.tg}) embyapi操作失败，请联系管理'
                LOGGER.error(text)
            try:
                await bot.send_message(c.tg, text)
            except FloodWait as f:
                LOGGER.warning(str(f))
                await sleep(f.value * 1.2)
                await bot.send_message(c.tg, text)
            except Exception as e:
                LOGGER.error(e)

        else:
            delete_day = c.ex + timedelta(days=config.freeze_days)
            if datetime.now() < delete_day:
                continue
            if await emby.emby_del(c.embyid):
                sql_update_emby(Emby.embyid == c.embyid, embyid=None, name=None, pwd=None, pwd2=None, lv='d', cr=None,
                                ex=None)
                tem_deluser()
                text = f'【到期检测】\n#id{c.tg} 删除账户 [{c.name}](tg://user?id={c.tg})\n已到期 {config.freeze_days} 天，执行清除任务。期待下次与你相遇'
                LOGGER.info(text)
            else:
                text = f'【到期检测】\n#id{c.tg} #删除账户 [{c.name}](tg://user?id={c.tg})\n到期删除失败，请检查以免无法进行后续使用'
                LOGGER.warning(text)
            try:
                send = await bot.send_message(c.tg, text)
                await send.forward(group[0])
            except FloodWait as f:
                LOGGER.warning(str(f))
                await sleep(f.value * 1.2)
                send = await bot.send_message(c.tg, text)
                await send.forward(group[0])
            except Exception as e:
                LOGGER.error(e)

    rseired = get_all_emby2(and_(Emby2.expired == 0, Emby2.ex < datetime.now()))
    if rseired is None:
        return LOGGER.info(f'【封禁检测】- emby2 无数据，跳过')
    for e in rseired:
        if await emby.emby_change_policy(id=e.embyid, method=True):
            if sql_update_emby2(Emby2.embyid == e.embyid, expired=1):
                text = f"【封禁检测】- 到期封印非TG账户 [{e.name}](google.com?q={e.embyid}) Done！"
                LOGGER.info(text)
            else:
                text = f'【封禁检测】- 到期封印非TG账户：`{e.name}` 数据库更改失败'
        else:
            text = f'【封禁检测】- 到期封印非TG账户：`{e.name}` embyapi操作失败，请手动处理'
        try:
            await bot.send_message(group[0], text)
        except FloodWait as f:
            LOGGER.warning(str(f))
            await sleep(f.value * 1.2)
            await bot.send_message(group[0], text)
        except Exception as e:
            LOGGER.error(e)

#停用账号
    now = datetime.now()
    # 1. 到期前3天提醒
    remind_time = now + timedelta(days=3)
    rse_remind = get_all_emby(and_(Emby.ex > now, Emby.ex <= remind_time, Emby.lv == 'e'))
    if rse_remind:
        for e in rse_remind:
            try:
                remind_text = (
                    f'【到期提醒】\n#id{e.tg} 停用账号 [{e.name}](tg://user?id={e.tg}) '
                    f'将在 {e.ex.strftime("%Y-%m-%d %H:%M:%S")} 到期，请及时启用，否则将被自动删除。'
                )
                await bot.send_message(e.tg, remind_text)
            except Exception as err:
                LOGGER.error(err)

    # 2. 到期未启用自动删除
    rse_expired = get_all_emby(and_(Emby.ex < now, Emby.lv == 'e'))
    if rse_expired:
        for e in rse_expired:
            until = parse_suspend_until(getattr(e, "suspend_until", None))
            if until and now > until:
                if sql_delete_emby(Emby.tg == e.tg):
                    del_text = (
                        f'【到期检测】\n#id{e.tg} 停用账号 [{e.name}](tg://user?id={e.tg})，因到期未启用。'
                    )
                    LOGGER.info(del_text)
                else:
                    del_text = (
                        f'【到期检测】\n#id{e.tg} 停用账号 [{e.name}](tg://user?id={e.tg}) 失败，请检查数据库。'
                    )
                    LOGGER.warning(del_text)
                try:
                    await bot.send_message(e.tg, del_text)
                except Exception as err:
                    LOGGER.error(err)

    # ... 其它等级处理 ...
