"""
定时推送日榜和周榜
"""
import json
import os
from pyrogram import enums, filters
from datetime import date

from bot.func_helper.filters import admins_on_filter
from bot.func_helper.scheduler import Scheduler
from bot.func_helper.emby import emby
from bot.ranks_helper import ranks_draw
from bot import bot, group, ranks, LOGGER, prefixes
from bot.func_helper.msg_utils import deleteMessage

# 记录推送日榜和周榜的消息id
rank_log_file_path = os.path.join('log', 'rank.json')


# 保存变量到文件
def save_data(data):
    with open(rank_log_file_path, 'w') as file:
        json.dump(data, file)


# 从文件加载变量
def get_data():
    # 判断文件是否存在，如果不存在，写入默认值
    if not os.path.exists(rank_log_file_path):
        variable = {"day_ranks_message_id": 0, "week_ranks_message_id": 0}
        save_data(variable)
    with open(rank_log_file_path, 'r') as file:
        try:
            variable = json.load(file)
        except Exception as e:
            variable = {"day_ranks_message_id": 0, "week_ranks_message_id": 0}
            save_data(variable)
        return variable


async def day_ranks():
    draw = ranks_draw.RanksDraw(ranks['logo'], backdrop=ranks['backdrop'])
    LOGGER.info("【ranks_task】定时任务 正在推送日榜")
    success, movies = await emby.get_emby_report(types='Movie', days=1)
    if not success:
        LOGGER.error('【ranks_task】推送日榜失败，获取Movies数据失败!')
        return
    success, tvs = await emby.get_emby_report(types='Episode', days=1)
    if not success:
        LOGGER.error('【ranks_task】推送日榜失败，获取Episode数据失败!')
        return
    # 绘制海报
    await draw.draw(movies, tvs)
    path = draw.save()

    try:
        json = get_data()
        message_id = json['day_ranks_message_id']
        await bot.unpin_chat_message(chat_id=group[0], message_id=int(message_id))
    except Exception as e:
        LOGGER.warning(f'【ranks_task】unpin day_ranks_message exception {e}')
        pass
    payload = ""
    if movies:
        tmp = "**▎电影:**\n\n"
        for i, movie in enumerate(movies[:10]):
            user_id, item_id, item_type, name, count, duarion = tuple(movie)
            tmp += str(i + 1) + "." + name + "-" + str(count) + "\n"
        payload = tmp
    if tvs:
        tmp = "\n**▎电视剧:**\n\n"
        for i, tv in enumerate(tvs[:10]):
            user_id, item_id, item_type, name, count, duarion = tuple(tv)
            tmp += str(i + 1) + "." + name + "-" + str(count) + "\n"
        payload += tmp
    payload = f"**【{ranks['logo']} 播放日榜】**\n\n" + payload + "\n#DayRanks" + "  " + date.today().strftime(
        '%Y-%m-%d')
    message_info = await bot.send_photo(chat_id=group[0], photo=open(path, "rb"), caption=payload,
                                        parse_mode=enums.ParseMode.MARKDOWN)
    await bot.pin_chat_message(chat_id=message_info.chat.id, message_id=message_info.id)
    data = get_data()
    data['day_ranks_message_id'] = message_info.id
    save_data(data)
    LOGGER.info("【ranks_task】定时任务 推送日榜完成")


async def week_ranks():
    draw = ranks_draw.RanksDraw(ranks['logo'], weekly=True, backdrop=ranks['backdrop'])
    LOGGER.info("【ranks_task】定时任务 正在推送周榜")
    success, movies = await emby.get_emby_report(types='Movie', days=7)
    if not success:
        LOGGER.warning('【ranks_task】推送周榜失败，没有获取到Movies数据!')
        return
    success, tvs = await emby.get_emby_report(types='Episode', days=7)
    if not success:
        LOGGER.error('【ranks_task】推送周榜失败，没有获取到Episode数据!')
        return
    # 绘制海报
    await draw.draw(movies, tvs)
    path = draw.save()

    try:
        json = get_data()
        message_id = json['week_ranks_message_id']
        await bot.unpin_chat_message(chat_id=group[0], message_id=int(message_id))
    except Exception as e:
        LOGGER.warning(f'【ranks_task】unpin day_ranks_message exception {e}')
        pass
    payload = ""
    if movies:
        tmp = "**▎电影:**\n\n"
        for i, movie in enumerate(movies[:10]):
            user_id, item_id, item_type, name, count, duarion = tuple(movie)
            tmp += str(i + 1) + "." + name + "-" + str(count) + "\n"
        payload = tmp
    if tvs:
        tmp = "\n**▎电视剧:**\n\n"
        for i, tv in enumerate(tvs[:10]):
            user_id, item_id, item_type, name, count, duarion = tuple(tv)
            tmp += str(i + 1) + "." + name + "-" + str(count) + "\n"
        payload += tmp
    payload = f"**【{ranks['logo']} 播放周榜】**\n\n" + payload + "\n#WeekRanks" + "  " + date.today().strftime(
        '%Y-%m-%d')
    message_info = await bot.send_photo(chat_id=group[0], photo=open(path, "rb"), caption=payload,
                                        parse_mode=enums.ParseMode.MARKDOWN)
    await bot.pin_chat_message(chat_id=message_info.chat.id, message_id=message_info.id)
    data = get_data()
    data['week_ranks_message_id'] = message_info.id
    save_data(data)
    LOGGER.info("【ranks_task】定时任务 推送周榜完成")


scheduler = Scheduler()
# 添加一个cron任务，每天18点30分执行日榜推送
scheduler.add_job(day_ranks, 'cron', hour=18, minute=30)
# scheduler.add_job(day_ranks, 'cron', minute='*/1')
# 添加一个cron任务，每周日23点59分执行周榜推送
scheduler.add_job(week_ranks, 'cron', day_of_week=0, hour=23, minute=59)


@bot.on_message(filters.command('days_ranks', prefixes) & admins_on_filter)
async def day_r_ranks(_, msg):
    await deleteMessage(msg)
    reply = await msg.reply(msg, '加载中。。。')
    await day_ranks()
    await reply.delete()


@bot.on_message(filters.command('week_ranks', prefixes) & admins_on_filter)
async def week_r_ranks(_, msg):
    await deleteMessage(msg)
    reply = await msg.reply(msg, '加载中。。。')
    await week_ranks()
    await reply.delete()
