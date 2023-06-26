"""
定时检测账户有无过期
"""
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from _mysql import sqlhelper
from bot.reply import emby
from config import bot, owner, group


async def check_expired():
    now = datetime.now()
    # 询问 到期时间的用户，判断有无积分，有则续期，无就禁用
    result = sqlhelper.select_all(
        "select tg,embyid,ex,us,name from emby where (ex < %s and lv=%s)", [now, 'b'])
    # print(result)
    if result is not None:
        for i in result:
            if i[3] != 0 and int(i[3] >= 30):
                a = int(i[3]) - 30
                ex = (now + timedelta(days=30))
                try:
                    sqlhelper.update_one("update emby set ex=%s,us=%s where tg=%s", [ex, a, i[0]])
                    await bot.send_message(i[0], f'✨**自动任务：**\n\n#id{i[0]} #续期账户 {i[4]}\n在当前时间自动续期30天')
                    logging.info(f"✨**自动任务：{i[0]} - {i[4]}**在当前时间自动续期30天 - {ex} - {i[1]}")
                except:
                    continue
            else:
                if await emby.ban_user(i[1], 0) is True:
                    try:
                        sqlhelper.update_one("update emby set lv=%s where tg=%s", ['c', i[0]])
                        send = await bot.send_message(i[0],
                                                      f'💫**自动任务：**\n\n#id{i[0]} #账户到期禁用 {i[4]}\n保留数据5天，请及时续期')
                        await send.forward(group[0])
                        logging.info(f"✨**自动任务：**{i[0]} 账号 {i[4]} 已到期,已禁用 - {i[1]}")
                    except:
                        continue
    else:
        pass
    # 询问 已禁用用户，若有积分变化则续期
    result1 = sqlhelper.select_all(
        "select tg,embyid,ex,us,name from emby where  (ex < %s and lv=%s)", [now, 'c'])
    # print(result1)
    if result1 is not None:
        for i in result1:
            if i[1] is not None and int(i[3]) >= 30:
                a = int(i[3]) - 30
                ex = (now + timedelta(days=30))
                try:
                    await emby.ban_user(i[1], 1)
                    sqlhelper.update_one("update emby set lv=%s,ex=%s,us=%s where tg=%s",
                                         ['b', ex, a, i[0]])
                    await bot.send_message(i[0], f'✨**自动任务：**\n\n#id{i[0]} #解封账户 {i[4]}\n在当前时间自动续期30天')
                    logging.info(f"✨**自动任务：**{i[0]} 解封账户 {i[4]} 在当前时间自动续期30天- {ex}")
                except:
                    continue
            elif i[1] is not None and int(i[3]) < 30:
                delta = i[2] + timedelta(days=5)
                if now > delta:
                    if await emby.emby_del(i[1]) is True:
                        try:
                            send = await bot.send_message(i[0],
                                                          f'💫**自动任务：**\n\n#id{i[0]} #删除账户 {i[4]}\n已到期 5 天，执行清除任务。期待下次见')
                            await send.forward(group[0])
                            logging.info(f"✨自动任务：{i[0]} 账号 {i[4]} 到期禁用已达5天，执行删除 - {i[1]}")
                        except:
                            pass
            else:
                pass
    else:
        pass
    result2 = sqlhelper.select_all(
        "select embyid,name,ex from emby2 where (ex < %s and expired=%s) ", [now, 0])
    if result2 is not None:
        for i in result2:
            await emby.ban_user(i[0], 0)
            sqlhelper.update_one("update emby2 set expired=%s where embyid=%s", [1, i[0]])
            await bot.send_message(owner, f'✨**自动任务：**\n  到期封印非TG账户：`{i[1]}` Done！')
            logging.info(f"自动任务：{i[0]} 封印非TG账户{i[1]} Done！")
    else:
        pass


# 每天x点检测
# 创建一个AsyncIOScheduler对象
scheduler = AsyncIOScheduler()
# 添加一个cron任务，每2小时执行一次job函数
scheduler.add_job(check_expired, 'cron', hour='*/4', timezone="Asia/Shanghai")
# scheduler.add_job(job, 'cron', minute='*/1', timezone="Asia/Shanghai")
# 启动调度器
scheduler.start()
