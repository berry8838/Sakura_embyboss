"""
定时检测账户有无过期
"""
import logging
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from _mysql import sqlhelper
from bot.func import emby
from config import bot


async def job():
    now = datetime.now()
    # 询问 到期时间的用户，判断有无积分，有则续期，无就禁用
    result = sqlhelper.select_all(
        "select tg,embyid,ex,us from emby where (ex < %s and lv=%s)", [now, 'b'])
    # print(result)
    if result is not None:
        for i in result:
            if i[3] != 0 and int(i[3] >= 30):
                a = int(i[3]) - 30
                ex = (now + timedelta(days=30))
                sqlhelper.update_one("update emby set ex=%s,us=%s where tg=%s", [ex, a, i[0]])
                await bot.send_message(i[0], f'✨**自动任务：**\n  在当前时间自动续期 30天 Done！')
                logging.info(f"✨**自动任务：**{i[0]} 在当前时间自动续期 30天 Done！- {ex}- {i[1]}")
            else:
                if await emby.ban_user(i[1], 0) is True:
                    sqlhelper.update_one("update emby set lv=%s where tg=%s", ['c', i[0]])
                await bot.send_message(i[0],
                                       f'💫**自动任务：**\n  你的账号已到期\n{i[1]}\n已禁用，但仍为您保留您的数据，请及时续期。')
                logging.info(f"✨**自动任务：**{i[0]} 账号已到期,已禁用 - {i[1]}")
    else:
        pass
    # 询问 已禁用用户，若有积分变化则续期
    result1 = sqlhelper.select_all(
        "select tg,embyid,ex,us from emby where  (ex < %s and lv=%s)", [now, 'c'])
    # print(result1)
    if result1 is not None:
        for i in result1:
            if i[1] is not None and int(i[3]) >= 30:
                a = int(i[3]) - 30
                ex = (now + timedelta(days=30))
                await emby.ban_user(i[1], 1)
                sqlhelper.update_one("update emby set lv=%s,ex=%s,us=%s where tg=%s",
                                     ['b', ex, a, i[0]])
                await bot.send_message(i[0], f'✨**自动任务：**\n  解封账户，在当前时间自动续期 30天 \nDone！')
                logging.info(f"✨**自动任务：**{i[0]} 解封账户，在当前时间自动续期 30天 Done！- {ex}")
            else:
                pass
    else:
        pass


# 每天x点检测
# 创建一个AsyncIOScheduler对象
scheduler = AsyncIOScheduler()
# 添加一个cron任务，每2小时执行一次job函数
scheduler.add_job(job, 'cron', hour='*/2', timezone="Asia/Shanghai")
# scheduler.add_job(job, 'cron', miniters='*/2', timezone="Asia/Shanghai")
# 启动调度器
scheduler.start()
