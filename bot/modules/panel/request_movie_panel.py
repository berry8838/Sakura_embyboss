from pyrogram import filters
from bot import bot, config, moviepilot, bot_photo, LOGGER, sakura_b
from bot.func_helper.msg_utils import callAnswer, editMessage, sendMessage, sendPhoto, callListen
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.fix_bottons import request_media_panel_ikb, back_members_ikb
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby
from bot.sql_helper.sql_request_record import sql_add_request_record, sql_get_request_record
from bot.func_helper.moviepilot import search, add_download_task, get_download_task
import asyncio
import math

@bot.on_callback_query(filters.regex('download_center') & user_in_group_on_filter)
async def call_download_center(_, call):
    if not moviepilot.status:
        return await callAnswer(call, '❌ 管理员未开启求片功能', True)
    await callAnswer(call, '🔍 求片中心')
    await editMessage(call, '🔍 欢迎进入求片中心', buttons=request_media_panel_ikb)

@bot.on_callback_query(filters.regex('download_media') & user_in_group_on_filter)
async def download_media(_, call):
    if not moviepilot.status:
        return await callAnswer(call, '❌ 管理员未开启求片功能', True)
    emby_user = sql_get_emby(tg=call.from_user.id)
    if not emby_user:
        return await editMessage(call, '⚠️ 数据库没有你，请重新 /start录入')
    if emby_user.lv is None or emby_user.lv not in ['a', 'b']:
        return await editMessage(call, '🫡 你没有权限使用此功能')
    await asyncio.gather(callAnswer(call, f'🔍 请输入你想求的资源名称'))
    await editMessage(call,
                        f"当前求片费用为: 1GB 消耗 {moviepilot.price} {sakura_b}\n您当前拥有 {emby_user.iv} {sakura_b}\n请在120s内对我发送你想求的资源名称，\n退出点 /cancel")
    txt = await callListen(call, 120, buttons=request_media_panel_ikb)
    if txt is False:
        return
    if txt.text == '/cancel':
        await asyncio.gather(txt.delete(), editMessage(call, '🔍 已取消操作', buttons=back_members_ikb))
    else:
        await editMessage(call, '🔍 正在搜索，请稍后...', buttons=request_media_panel_ikb)
        success, result = await search(txt.text)
        if success:
            if len(result) <= 0:
                await editMessage(call, '🤷‍♂️ 没有找到相关信息', buttons=request_media_panel_ikb)
                return
            for index, item in enumerate(result, start=1):
                year = item["year"]
                if year is not None and year != "":
                    year = f"\n年份：{year}"
                else:
                    year = ""
                type = item["type"]
                if type is None or type == "未知":
                    type = "\n类型：电影"
                else:
                    type = f"\n类型：{type}"
                size = item["size"]
                if size is not None and size != "":
                    size_in_bytes = int(size)
                    size_in_mb = size_in_bytes / (1024 * 1024)
                    size_in_gb = size_in_mb / 1024
                    if size_in_gb >= 1:
                        size = f"\n大小：{size_in_gb:.2f} GB"
                    else:
                        size = f"\n大小：{size_in_mb:.2f} MB"
                else:
                    size = ""
                labels = item["labels"]
                if labels is not None and labels != "":
                    labels = f"\n标签：{labels}"
                else:
                    labels = ""
                resource_team = item["resource_team"]
                if resource_team is not None and resource_team != "":
                    resource_team = f"\n资源组：{resource_team}"
                else:
                    resource_team = ""
                pix = item["resource_pix"]
                video_encode = item["video_encode"]
                audio_encode = item["audio_encode"]
                resource_info = [pix, video_encode, audio_encode]
                resource_info = [str(info)
                                 for info in resource_info if info is not None and info != ""]
                resource_info = ' | '.join(resource_info)
                if resource_info:
                    resource_info = f"\n媒体信息：{resource_info}"
                description = item["description"]
                if description is not None and description != "":
                    description = f"\n描述：{description}"
                else:
                    description = ""
                text = f"资源编号: `{index}`\n标题：{item['title']}{type}{year}{size}{labels}{resource_team}{resource_info}{description}"
                item["tg_log"] = text
                await sendMessage(call, text, send=True, chat_id=call.from_user.id)
            await sendMessage(call, f"共推送{len(result)}个结果！", send=True, chat_id=call.from_user.id)
            await handle_resource_selection(call, result)
        else:
            await editMessage(call, '🤷‍♂️ 搜索失败，请稍后再试', buttons=re_download_center_ikb)
            return


async def handle_resource_selection(call, result):
    while True:
        emby_user = sql_get_emby(tg=call.from_user.id)
        msg = await sendPhoto(call, photo=bot_photo, caption = "【选择资源编号】：\n请在120s内对我发送你的资源编号，\n退出点 /cancel", send=True, chat_id=call.from_user.id)
        txt = await callListen(call, 120, buttons=re_download_center_ikb)
        if txt is False:
            await asyncio.gather(editMessage(msg, '🔍 已取消操作', buttons=back_members_ikb))
            return
        elif txt.text == '/cancel':
            await asyncio.gather(editMessage(msg, '🔍 已取消操作', buttons=back_members_ikb))
            return
        else:
            try:
                await editMessage(msg, '🔍 正在处理，请稍后')
                index = int(txt.text)
                size = result[index-1]['size'] / (1024 * 1024 * 1024)
                need_cost = math.ceil(size) * moviepilot.price
                if need_cost > emby_user.iv:
                    await editMessage(msg, f"❌ 您的{sakura_b}不足，此资源需要 {need_cost}{sakura_b}\n请选择其他资源编号", buttons=re_download_center_ikb)
                    continue
                success, download_id = await add_download_task(result[index-1]['torrent_info'])
                if success:
                    log = f"【下载任务】：[{call.from_user.first_name}](tg://user?id={call.from_user.id}) 已成功添加到下载队列，下载ID：{download_id}\n此次消耗 {need_cost}{sakura_b}"
                    download_log = f"{log}\n详情：{result[index-1]['tg_log']}"
                    LOGGER.info(log)
                    sql_update_emby(Emby.tg == call.from_user.id,
                                    iv=emby_user.iv - need_cost)
                    sql_add_request_record(call.from_user.id, download_id, result[index-1]['title'], download_log, need_cost)
                    if moviepilot.download_log_chatid:
                        await sendMessage(call, download_log, send=True, chat_id=moviepilot.download_log_chatid)
                    await editMessage(msg, f"🎉 已成功添加到下载队列，下载ID：{download_id}，此次消耗 {need_cost}{sakura_b}", buttons=request_media_panel_ikb)
                    return
                else:
                    LOGGER.error(f"【下载任务】：{call.from_user.id} 添加下载任务失败!")
                    await editMessage(msg, f"❌ 添加下载任务失败!", buttons=request_media_panel_ikb)
                    return
            except IndexError:
                await editMessage(msg, '❌ 输入错误，请重新输入，退出点 /cancel', buttons=request_media_panel_ikb)
                continue
            except ValueError:
                await editMessage(msg, '❌ 输入错误，请重新输入，退出点 /cancel', buttons=request_media_panel_ikb)
                continue
            except:
                await editMessage(msg, '❌ 呜呜呜，出错了', buttons=request_media_panel_ikb)
                return


user_data = {}

@bot.on_callback_query(filters.regex('rate') & user_in_group_on_filter)
async def call_rate(_, call):
    if not moviepilot.status:
        return await callAnswer(call, '❌ 管理员未开启求片功能', True)
    await callAnswer(call, '📈 查看求片下载任务')
    request_record, has_prev, has_next = sql_get_request_record(call.from_user.id)
    if request_record is None:
        return await editMessage(call, '🤷‍♂️ 您还没有求过片，快去求片吧', buttons=request_media_panel_ikb)
    download_tasks = await get_download_task()
    text = get_download_text(download_tasks, request_record)
    user_data[call.from_user.id] = {'page_request_record': 1}
    await editMessage(call, text, buttons=page_request_record_ikb(has_prev, has_next))
@bot.on_callback_query(filters.regex('pre_page_request_record') & user_in_group_on_filter)
async def pre_page_request_record(_, call):
    if user_data.get(call.from_user.id) is None:
        user_data[call.from_user.id] = {'page_request_record': 1}
    page = user_data[call.from_user.id]['page_request_record'] - 1
    if page <= 0:
        page = 1
    request_record, has_prev, has_next = sql_get_request_record(call.from_user.id, page=page)
    user_data[call.from_user.id]['page_request_record'] = page
    download_tasks = await get_download_task()
    text = get_download_text(download_tasks, request_record)
    await editMessage(call, text, buttons=page_request_record_ikb(has_prev, has_next))
@bot.on_callback_query(filters.regex('next_page_request_record') & user_in_group_on_filter)
async def next_page_request_record(_, call):
    if user_data.get(call.from_user.id) is None:
        user_data[call.from_user.id] = {'page_request_record': 1}
    page = user_data[call.from_user.id]['page_request_record'] + 1
    request_record, has_prev, has_next = sql_get_request_record(call.from_user.id, page=page)
    user_data[call.from_user.id]['page_request_record'] = page
    download_tasks = await get_download_task()
    text = get_download_text(download_tasks, request_record)
    await editMessage(call, text, buttons=page_request_record_ikb(has_prev, has_next))
def get_download_text(download_tasks, request_record):
    text = '📈 求片任务\n'
    for index, item in enumerate(request_record, start=1):
        for download_task in download_tasks:
            if download_task['download_id'] == item.download_id:
                progress = download_task['progress']
                progress_text = ''
                if progress is None:
                    progress_text = '未知'
                else:
                    progress = round(progress, 1)
                    left_progress = '🟩' * int(progress/10)
                    right_progress = '⬜️' * (10 - int(progress // 10))
                    progress_text = f"{left_progress}{right_progress} {progress}%"
                text += f"「{index}」：{item.request_name} \n状态：{'正在下载' if download_task['state'] == 'downloading' else ''} {progress_text}\n"
                break
        else:
            left_progress = '🟩' * 10
            progress_text = f"{left_progress} 100%"
            text += f"「{index}」：{item.request_name} \n状态：已完成 {progress_text}\n"
    return text