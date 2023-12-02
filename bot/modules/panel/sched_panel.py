from pyrogram import filters

from bot import bot, sakura_b, schedall, save_config
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.fix_bottons import sched_buttons
from bot.func_helper.msg_utils import callAnswer, editMessage
from bot.func_helper.scheduler import Scheduler
from bot.modules.check_ex import check_expired
from bot.modules.ranks_task import day_ranks, week_ranks
from bot.modules.userplays_rank import user_day_plays, user_week_plays, check_low_activity
from bot.modules.backup_db import auto_backup_db

scheduler = Scheduler()
if schedall["dayrank"]:
    scheduler.add_job(day_ranks, 'cron', hour=18, minute=30, id='day_ranks')
if schedall["weekrank"]:
    scheduler.add_job(week_ranks, 'cron', day_of_week="sun", hour=23, minute=59, id='week_ranks')
if schedall["dayplayrank"]:
    scheduler.add_job(user_day_plays, 'cron', hour=23, minute=0, id='user_day_plays')  # args=(1,)
if schedall["weekplayrank"]:
    scheduler.add_job(user_week_plays, 'cron', day_of_week="sun", hour=23, minute=0, id='user_week_plays')
if schedall["check_ex"]:
    scheduler.add_job(check_expired, 'cron', hour=1, minute=30, id='check_expired')
if schedall["low_activity"]:
    scheduler.add_job(check_low_activity, 'cron', hour=8, minute=30, id='check_low_activity')
if schedall["backup_db"]:
    scheduler.add_job(auto_backup_db, 'cron', hour=1, minute=30, id='auto_backup_db')


async def sched_panel(_, msg):
    # await deleteMessage(msg)
    await editMessage(msg,
                      text=f'🎮 **管理定时任务面板**\n\n默认关闭**看片榜单**，开启请在日与周中二选一，以免重复{sakura_b}的计算，谨慎',
                      buttons=sched_buttons())


@bot.on_callback_query(filters.regex('sched') & admins_on_filter)
async def sched_change_policy(_, call):
    try:
        method = call.data.split('-')[1]
        if schedall[method]:
            m_dict = {'dayrank': 'day_ranks', 'weekrank': 'week_ranks', 'dayplayrank': 'user_day_plays',
                      'weekplayrank': 'user_week_plays', 'check_ex': 'check_expired',
                      'low_activity': 'check_low_activity', 'backup_db': 'auto_backup_db'}
            m = m_dict.get(method, '未知')
            scheduler.remove_job(job_id=m, jobstore='default')
        schedall[method] = not schedall[method]
        save_config()
        if schedall["dayrank"]:
            scheduler.add_job(day_ranks, 'cron', hour=18, minute=30, id='day_ranks')
        if schedall["weekrank"]:
            scheduler.add_job(week_ranks, 'cron', day_of_week="sun", hour=23, minute=59, id='week_ranks')
        if schedall["dayplayrank"]:
            scheduler.add_job(user_day_plays, 'cron', hour=23, minute=0, id='user_day_plays')  # args=(1,)
        if schedall["weekplayrank"]:
            scheduler.add_job(user_week_plays, 'cron', day_of_week="sun", hour=23, minute=0, id='user_week_plays')
        if schedall["check_ex"]:
            scheduler.add_job(check_expired, 'cron', hour=1, minute=30, id='check_expired')
        if schedall["low_activity"]:
            scheduler.add_job(check_low_activity, 'cron', hour=8, minute=30, id='check_low_activity')
        if schedall["backup_db"]:
            scheduler.add_job(auto_backup_db, 'cron', hour=1, minute=30, id='auto_backup_db')
        await callAnswer(call, f'⭕ 更改成功')
        await sched_panel(_, call.message)
    except IndexError:
        await sched_panel(_, call.message)
