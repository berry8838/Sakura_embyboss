"""
服务器讯息打印

"""
from datetime import datetime, timezone, timedelta

from pyrogram import filters
from bot import bot, emby_line, tz_id
from bot.func_helper.emby import emby
from bot.func_helper.filters import user_in_group_on_filter
from bot.sql_helper.sql_emby import sql_get_emby
from bot.func_helper.fix_bottons import cr_page_server
from bot.func_helper.msg_utils import callAnswer, editMessage


@bot.on_callback_query(filters.regex('server') & user_in_group_on_filter)
async def server(_, call):
    """
    显示账户名密码,线路和设置好服务器信息
    :param _:
    :param call:
    :return:
    """
    try:
        j = call.data.split(':')[1]
    except IndexError:
        # 第一次查看
        send = await editMessage(call, "**▎🌐查询中...\n\nο(=•ω＜=)ρ⌒☆ 发送bibo电波~bibo~ \n⚡ 卡住请等待即可.**")
        if send is False:
            return

        keyboard, sever = await cr_page_server()
        # print(keyboard, sever)
        if len(tz_id) > 1:
            sever = sever[tz_id[0]]
    else:
        keyboard, sever = await cr_page_server()
        sever = sever[j]

    await callAnswer(call, '🌐查询中...')
    data = sql_get_emby(tg=call.from_user.id)
    if data is None:
        return await editMessage(call, '⚠️ 数据库没有你，请重新 /start录入')
    lv = data.lv
    pwd = data.pwd
    if lv == "d" or lv == "c" or lv == "e":
        x = ' - **无权查看**'
    else:
        x = f'{emby_line}'
    try:
        online = emby.get_current_playing_count()
    except:
        online = 'Emby服务器断连 ·0'
    text = f'**▎目前线路 & 用户密码 `{pwd}`**\n\n{x}\n\n{sever}· 🎬 在线 | **{online}** 人\n\n **· 🌏 [{(datetime.now(timezone(timedelta(hours=8)))).strftime("%Y-%m-%d %H:%M:%S")}]**'
    await editMessage(call, text, buttons=keyboard)
