from pyrogram import filters

from bot import bot, sakura_b, schedall, save_config
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.fix_bottons import sched_buttons
from bot.func_helper.msg_utils import callAnswer, editMessage
from bot.func_helper.scheduler import Scheduler
from bot.modules.check_ex import check_expired
from bot.modules.ranks_task import day_ranks, week_ranks
from bot.modules.userplays_rank import user_day_plays, user_week_plays, check_low_activity

scheduler = Scheduler()
if schedall["dayrank"]:
    # 添加一个cron任务，每天18点30分执行日榜推送
    scheduler.add_job(day_ranks, 'cron', hour=18, minute=30)
if schedall["weekrank"]:
    # 添加一个cron任务，每周日23点59分执行周榜推送
    scheduler.add_job(week_ranks, 'cron', day_of_week="sun", hour=23, minute=59)
if schedall["dayplayrank"]:
    scheduler.add_job(user_day_plays, 'cron', hour=23, minute=0)  # args=(1,)
if schedall["weekplayrank"]:
    scheduler.add_job(user_week_plays, 'cron', day_of_week="sun", hour=23, minute=0)
if schedall["check_ex"]:
    scheduler.add_job(check_expired, 'cron', hour=1, minute=30)
if schedall["low_activity"]:
    scheduler.add_job(check_low_activity, 'cron', hour=8, minute=30)


async def sched_panel(_, msg):
    # await deleteMessage(msg)
    await editMessage(msg,
                      text=f'🎮 **管理定时任务面板**\n\n默认关闭**看片榜单**，开启请在日与周中二选一，以免重复{sakura_b}的计算，谨慎',
                      buttons=sched_buttons())


@bot.on_callback_query(filters.regex('sched') & admins_on_filter)
async def sched_change_policy(_, call):
    try:
        method = call.data.split('-')[1]
        schedall[method] = not schedall[method]
        save_config()
        await callAnswer(call, f'⭕ 成功更改了 {method} 状态，请 /restart 重启bot 使其生效', True)
        await sched_panel(_, call.message)
    except IndexError:
        await sched_panel(_, call.message)
