"""
服务器讯息打印

"""
from pyrogram import filters
from pyrogram.errors import BadRequest, Forbidden
from pyromod.helpers import ikb, array_chunk
from datetime import datetime
from _mysql import sqlhelper
from bot.reply import nezha_res
from config import bot, config, tz, tz_api
from cacheout import Cache

cache = Cache()


@bot.on_callback_query(filters.regex('server'))
async def server(_, call):
    # print(call.data)
    try:
        j = call.data.split(':')[1]
    except IndexError:
        if len(config["tz_id"]) == 0:
            try:
                await bot.edit_message_caption(
                    call.from_user.id,
                    call.message.id,
                    caption="**▎🌐查询中...\n\nο(=•ω＜=)ρ⌒☆ 发送bibo电波~bibo~ \n⚡ 卡住请等待即可.**")
            except BadRequest:
                await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
                return
            except Forbidden:
                await call.answer("Forbidden - 时间太久远，请重新召唤面板！", show_alert=True)
                return
            else:
                sever = ''
                keyboard = ikb([[('🔙 - 用户', 'members'), ('❌ - 关闭', 'closeit')]])
        elif len(config["tz_id"]) == 1:
            try:
                await bot.edit_message_caption(
                    call.from_user.id,
                    call.message.id,
                    caption="**▎🌐查询中...\n\nο(=•ω＜=)ρ⌒☆ 发送bibo电波~bibo~ \n⚡ 卡住请等待即可.**")
                j = config["tz_id"][0]
                keyboard, sever = await cr_page_server()
                sever = sever[j]
            except BadRequest:
                await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
                return
            except Forbidden:
                await call.answer("Forbidden - 时间太久远，请重新召唤面板！", show_alert=True)
                return
            else:
                keyboard = ikb([[('🔙 - 用户', 'members'), ('❌ - 关闭', 'closeit')]])
        else:
            j = config["tz_id"][0]
            keyboard, sever = await cr_page_server()
            sever = sever[j]
    else:
        keyboard, sever = await cr_page_server()
        sever = sever[j]
    # 服务器此前运行，当前带宽，（探针
    embyid, pwd1, lv = sqlhelper.select_one("select embyid,pwd,lv from emby where tg=%s", call.from_user.id)
    if lv == "d" or lv == "c" or lv == "e":
        x = '\n**无权查看**'
    else:
        x = '\n' + config["line"]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        await bot.edit_message_caption(
            call.from_user.id,
            call.message.id,
            caption=f'**▎目前线路 & 用户密码 `{pwd1}`**\n{x}\n\n' + sever + f'**· 🌏  {now}**',
            reply_markup=keyboard)
    except BadRequest:
        await call.answer("慢速模式开启，切勿多点\n慢一点，慢一点，生活更有趣 - zztai", show_alert=True)
    except Forbidden:
        await call.answer("Forbidden - 时间太久远，请重新召唤面板！", show_alert=True)


@cache.memoize(ttl=120)
async def cr_page_server():
    # i 总数，j是当前页数
    a = {}
    b = []
    for x in config["tz_id"]:
        # l = a.get(x, {})  # 获取或创建一个空字典
        name, sever = nezha_res.sever_info(tz, tz_api, x)
        b.append([f'{name}', f'server:{x}'])
        a[x] = f"{sever}"
    # print(a, b)
    lines = array_chunk(b, 3)
    lines.append([['🔙 - 用户', 'members'], ['❌ - 关闭', 'closeit']])
    b = ikb(lines)
    # a = a[j]
    # b是键盘，a是sever
    return b, a
