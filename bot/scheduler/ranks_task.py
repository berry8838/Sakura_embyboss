"""
定时推送日榜和周榜
"""
from pyrogram import enums
from datetime import date

from bot.func_helper.utils import convert_s
from bot.func_helper.emby import emby
from bot.ranks_helper import ranks_draw
from bot import bot, group, ranks, LOGGER, schedall, save_config


def split_long_message(content, max_length=1000):
    """
    将过长的消息内容分割成多个部分，确保每部分都不超过Telegram的长度限制
    
    Args:
        content (str): 要分割的内容
        max_length (int): 每条消息的最大长度限制，默认1000字符（留缓冲）
    
    Returns:
        list: 分割后的消息列表
    """
    if len(content) <= max_length:
        return [content]
    
    messages = []
    lines = content.split('\n')
    current_message = ""
    
    for line in lines:
        # 检查添加这一行后是否会超长
        test_message = current_message + ('\n' if current_message else '') + line
        
        if len(test_message) <= max_length:
            current_message = test_message
        else:
            # 如果当前消息不为空，保存它
            if current_message:
                messages.append(current_message)
                current_message = line
            else:
                # 如果单行就超长，需要强制分割
                if len(line) > max_length:
                    # 按字符分割超长的单行
                    while len(line) > max_length:
                        messages.append(line[:max_length])
                        line = line[max_length:]
                    if line:
                        current_message = line
                else:
                    current_message = line
    
    # 添加最后一部分
    if current_message:
        messages.append(current_message)
    
    return messages


async def send_multi_message(chat_id, photo_path, caption, parse_mode, pin_first=True):
    """
    发送可能需要分割的长消息，第一条带图片，后续为纯文本
    
    Args:
        chat_id: 聊天ID
        photo_path: 图片路径
        caption: 消息内容
        parse_mode: 解析模式
        pin_first: 是否置顶第一条消息
    
    Returns:
        list: 发送的消息信息列表
    """
    message_parts = split_long_message(caption)
    sent_messages = []
    
    # 发送第一条消息（带图片）
    first_message = await bot.send_photo(
        chat_id=chat_id, 
        photo=open(photo_path, "rb"), 
        caption=message_parts[0],
        parse_mode=parse_mode
    )
    sent_messages.append(first_message)
    
    # 如果需要置顶第一条消息
    if pin_first:
        await bot.pin_chat_message(
            chat_id=first_message.chat.id, 
            message_id=first_message.id, 
            disable_notification=True
        )
    
    # 发送后续消息（纯文本）
    for i, part in enumerate(message_parts[1:], 2):
        message = await bot.send_message(
            chat_id=chat_id,
            text=f"{part}",
            parse_mode=parse_mode
        )
        sent_messages.append(message)
    
    return sent_messages


async def day_ranks(pin_mode=True):
    draw = ranks_draw.RanksDraw(ranks.logo, backdrop=ranks.backdrop)
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
        if pin_mode:
            await bot.unpin_chat_message(chat_id=group[0], message_id=schedall.day_ranks_message_id)
    except Exception as e:
        LOGGER.warning(f'【ranks_task】unpin day_ranks_message exception {e}')
        pass
    payload = ""
    if movies:
        tmp = "**▎电影:**\n\n"
        for i, movie in enumerate(movies[:10]):
            user_id, item_id, item_type, name, count, duarion = tuple(movie)
            time = await convert_s(int(duarion))
            tmp += str(i + 1) + ". " + name + "\n播放次数: " + str(count) + "  时长:" + time + "\n"
        payload = tmp
    if tvs:
        tmp = "\n**▎电视剧:**\n\n"
        for i, tv in enumerate(tvs[:10]):
            user_id, item_id, item_type, name, count, duarion = tuple(tv)
            time = await convert_s(int(duarion))
            tmp += str(i + 1) + ". " + name + "\n播放次数: " + str(count) + "  时长:" + time + "\n"
        payload += tmp
    
    payload = f"**【{ranks.logo} 播放日榜】**\n\n" + payload + "\n#DayRanks" + "  " + date.today().strftime('%Y-%m-%d')
    
    # 使用多消息发送功能
    sent_messages = await send_multi_message(
        chat_id=group[0], 
        photo_path=path, 
        caption=payload,
        parse_mode=enums.ParseMode.MARKDOWN,
        pin_first=pin_mode
    )
    
    # 保存第一条消息的ID用于后续取消置顶
    schedall.day_ranks_message_id = sent_messages[0].id
    save_config()
    LOGGER.info("【ranks_task】定时任务 推送日榜完成")


async def week_ranks(pin_mode=True):
    draw = ranks_draw.RanksDraw(ranks.logo, weekly=True, backdrop=ranks.backdrop)
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
        if pin_mode:
            await bot.unpin_chat_message(chat_id=group[0], message_id=schedall.week_ranks_message_id)
    except Exception as e:
        LOGGER.warning(f'【ranks_task】unpin week_ranks_message exception {e}')
        pass
    
    payload = ""
    if movies:
        tmp = "**▎电影:**\n\n"
        for i, movie in enumerate(movies[:10]):
            user_id, item_id, item_type, name, count, duarion = tuple(movie)
            time = await convert_s(int(duarion))
            tmp += str(i + 1) + ". " + name + "\n播放次数: " + str(count) + "  时长:" + time + "\n"
        payload = tmp
    if tvs:
        tmp = "\n**▎电视剧:**\n\n"
        for i, tv in enumerate(tvs[:10]):
            user_id, item_id, item_type, name, count, duarion = tuple(tv)
            time = await convert_s(int(duarion))
            tmp += str(i + 1) + ". " + name + "\n播放次数: " + str(count) + "  时长:" + time + "\n"
        payload += tmp
    
    payload = f"**【{ranks.logo} 播放周榜】**\n\n" + payload + "\n#WeekRanks" + "  " + date.today().strftime('%Y-%m-%d')
    
    # 使用多消息发送功能
    sent_messages = await send_multi_message(
        chat_id=group[0], 
        photo_path=path, 
        caption=payload,
        parse_mode=enums.ParseMode.MARKDOWN,
        pin_first=pin_mode
    )
    
    # 保存第一条消息的ID用于后续取消置顶
    schedall.week_ranks_message_id = sent_messages[0].id
    save_config()
    LOGGER.info("【ranks_task】定时任务 推送周榜完成")
