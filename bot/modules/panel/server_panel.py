"""
服务器讯息打印

"""
import asyncio
from datetime import datetime, timezone, timedelta
from pyrogram import filters
from bot import bot, emby_line, emby_whitelist_line, LOGGER
from bot.func_helper.emby import emby, EmbyConnectError
from bot.func_helper.filters import user_in_group_on_filter
from bot.sql_helper.sql_emby import sql_get_emby
from bot.func_helper.fix_bottons import cr_page_server
from bot.func_helper.msg_utils import callAnswer, editMessage


@bot.on_callback_query(filters.regex('server') & user_in_group_on_filter)
async def server(_, call):
    data = sql_get_emby(tg=call.from_user.id)
    if not data:
        return await editMessage(call, '⚠️ 数据库没有你，请重新 /start录入')
    await callAnswer(call, '🌐查询中...')
    await editMessage(call, "**▎🌐查询中...\n\nο(=•ω＜=)ρ⌒☆ 发送bibo电波~bibo~ \n⚡ 点击按钮查看相应服务器状态**")

    try:
        online, page_server = await asyncio.gather(
            asyncio.to_thread(emby.get_current_playing_count),
            cr_page_server(),
            return_exceptions=True
        )

        if isinstance(online, Exception):
            LOGGER.error(f"获取在线人数失败: {online}")
            online = 'Emby服务器断连 | 0'
        else:
            online = f"{online}"

        if isinstance(page_server, Exception):
            keyboard, sever = None, []
        else:
            keyboard, sever = page_server
    except Exception as e:
        LOGGER.error(f"处理服务器面板时发生未知错误: {e}")
        return await editMessage(call, "❌ 处理请求时发生了一个未知错误。")

    try:
        j = int(call.data.split(':')[1])
        server_info = ''.join([item['server'] for item in sever if item['id'] == j])
    except IndexError:
        server_info = sever[0]['server'] if sever else ''

    pwd = '空' if not data.pwd else data.pwd
    line = ''
    if data.lv == 'b':
        line = f'{emby_line}'
    elif data.lv == 'a':
        line = f'{emby_line}'
        if emby_whitelist_line:
            line += f'\n{emby_whitelist_line}'
    else:
        line = ' - **无权查看**'

    text = (f'**▎↓目前线路 & 用户密码：**`{pwd}`\n'
            f'{line}\n\n'
            f'{server_info}'
            f'· 🎬 在线 | **{online}** 人\n\n'
            f'**· 🌏 [{(datetime.now(timezone(timedelta(hours=8)))).strftime("%Y-%m-%d %H:%M:%S")}]**')
    
    await editMessage(call, text, buttons=keyboard)