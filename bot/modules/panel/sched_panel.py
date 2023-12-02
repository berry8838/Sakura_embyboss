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

# 写优雅点
# 字典，method相应的操作函数
action_dict = {
    "dayrank": day_ranks,
    "weekrank": week_ranks,
    "dayplayrank": user_day_plays,
    "weekplayrank": user_week_plays,
    "check_ex": check_expired,
    "low_activity": check_low_activity,
    "backup_db": auto_backup_db
}

# 字典，对应的操作函数的参数和id
args_dict = {
    "dayrank": {'hour': 18, 'minute': 30, 'id': 'day_ranks'},
    "weekrank": {'day_of_week': "sun", 'hour': 23, 'minute': 59, 'id': 'week_ranks'},
    "dayplayrank": {'hour': 23, 'minute': 0, 'id': 'user_day_plays'},
    "weekplayrank": {'day_of_week': "sun", 'hour': 23, 'minute': 0, 'id': 'user_week_plays'},
    "check_ex": {'hour': 1, 'minute': 30, 'id': 'check_expired'},
    "low_activity": {'hour': 8, 'minute': 30, 'id': 'check_low_activity'},
    "backup_db": {'hour': 2, 'minute': 30, 'id': 'backup_db'}
}


def set_all_sche():
    for key, value in action_dict.items():
        if schedall[key]:
            action = action_dict[key]
            args = args_dict[key]
            scheduler.add_job(action, 'cron', **args)


set_all_sche()


async def sched_panel(_, msg):
    # await deleteMessage(msg)
    await editMessage(msg,
                      text=f'🎮 **管理定时任务面板**\n\n默认关闭**看片榜单**，开启请在日与周中二选一，以免重复{sakura_b}的计算，谨慎',
                      buttons=sched_buttons())


@bot.on_callback_query(filters.regex('sched') & admins_on_filter)
async def sched_change_policy(_, call):
    try:
        method = call.data.split('-')[1]
        # 根据method的值来添加或移除相应的任务
        action = action_dict[method]
        args = args_dict[method]
        if schedall[method]:
            scheduler.remove_job(job_id=args['id'], jobstore='default')
        else:
            scheduler.add_job(action, 'cron', **args)
        schedall[method] = not schedall[method]
        save_config()
        await callAnswer(call, f'⭕️ {method} 更改成功')
        await sched_panel(_, call.message)
    except IndexError:
        await sched_panel(_, call.message)