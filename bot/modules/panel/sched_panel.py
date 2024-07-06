import asyncio
import os

from pyrogram import filters
from bot import bot, sakura_b, schedall, save_config, prefixes, _open, owner, LOGGER
from bot.func_helper.filters import admins_on_filter, user_in_group_on_filter
from bot.func_helper.fix_bottons import sched_buttons, plays_list_button
from bot.func_helper.msg_utils import callAnswer, editMessage, deleteMessage
from bot.func_helper.scheduler import Scheduler
from bot.scheduler import *

# 实例化
scheduler = Scheduler()

# 初始化命令 开机检查重启
loop = asyncio.get_event_loop()
loop.call_later(10, lambda: loop.create_task(BotCommands.set_commands(client=bot)))
loop.call_later(10, lambda: loop.create_task(check_restart()))

# 启动定时任务
auto_backup_db = DbBackupUtils.auto_backup_db
user_plays_rank = Uplaysinfo.user_plays_rank
check_low_activity = Uplaysinfo.check_low_activity


async def user_day_plays(): await user_plays_rank(1)


async def user_week_plays(): await user_plays_rank(7)


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
        if getattr(schedall, key):
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
        if getattr(schedall, method):
            scheduler.remove_job(job_id=args['id'], jobstore='default')
        else:
            scheduler.add_job(action, 'cron', **args)
        setattr(schedall, method, not getattr(schedall, method))
        save_config()
        await asyncio.gather(callAnswer(call, f'⭕️ {method} 更改成功'), sched_panel(_, call.message))
    except IndexError:
        await sched_panel(_, call.message)


@bot.on_message(filters.command('check_ex', prefixes) & admins_on_filter)
async def check_ex_admin(_, msg):
    send = await msg.reply("🍥 正在运行 【到期检测】。。。")
    await check_expired()
    await asyncio.gather(msg.delete(), send.edit("✅ 【到期检测结束】"))


# bot数据库手动备份
@bot.on_message(filters.command('backup_db', prefixes) & filters.user(owner))
async def manual_backup_db(_, msg):
    await asyncio.gather(deleteMessage(msg), auto_backup_db())


@bot.on_message(filters.command('days_ranks', prefixes) & admins_on_filter)
async def day_r_ranks(_, msg):
    await asyncio.gather(msg.delete(), day_ranks(pin_mode=False))


@bot.on_message(filters.command('week_ranks', prefixes) & admins_on_filter)
async def week_r_ranks(_, msg):
    await asyncio.gather(msg.delete(), week_ranks(pin_mode=False))


@bot.on_message(filters.command('low_activity', prefixes) & admins_on_filter)
async def run_low_ac(_, msg):
    await deleteMessage(msg)
    send = await msg.reply(f"⭕ 不活跃检测运行ing···")
    await asyncio.gather(check_low_activity(), send.delete())


@bot.on_message(filters.command('uranks', prefixes) & admins_on_filter)
async def shou_dong_uplayrank(_, msg):
    await deleteMessage(msg)
    try:
        days = int(msg.command[1])
        await user_plays_rank(days=days, uplays=False)
    except (IndexError, ValueError):
        await msg.reply(
            f"🔔 请输入 `/uranks 天数`，此运行手动不会影响{sakura_b}的结算（仅定时运行时结算），放心使用。\n"
            f"定时结算状态: {_open.uplays}")


@bot.on_message(filters.command('restart', prefixes) & admins_on_filter)
async def restart_bot(_, msg):
    await deleteMessage(msg)
    send = await msg.reply("Restarting，等待几秒钟。")
    schedall.restart_chat_id = send.chat.id
    schedall.restart_msg_id = send.id
    save_config()
    try:
        # some code here
        LOGGER.info("重启")
        os.execl('/bin/systemctl', 'systemctl', 'restart', 'embyboss')  # 用当前进程执行systemctl命令，重启embyboss服务
    except FileNotFoundError:
        exit(1)


@bot.on_callback_query(filters.regex('uranks') & user_in_group_on_filter)
async def page_uplayrank(_, call):
    j, days = map(int, call.data.split(":")[1].split('_'))
    await callAnswer(call, f'将为您翻到第 {j} 页')
    a, b, c = await Uplaysinfo.users_playback_list(days)
    if not a:
        return await callAnswer(call, f'🍥 获取过去{days}天UserPlays失败了嘤嘤嘤 ~ 手动重试', True)
    button = await plays_list_button(b, j, days)
    text = a[j - 1]
    await editMessage(call, text, buttons=button)
