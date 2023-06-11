"""
服务器讯息打印

"""
from pyrogram import filters
from pyrogram.errors import BadRequest
from pyromod.helpers import ikb

from _mysql import sqlhelper
from bot.func import nezha_res
from config import bot, config


@bot.on_callback_query(filters.regex('server'))
async def server(_, call):
    # print(call)
    try:
        await bot.edit_message_caption(
            call.from_user.id,
            call.message.id,
            caption="**▎🌐查询中...\n\nο(=•ω＜=)ρ⌒☆ 发送bibo电波~bibo~ \n⚡ 卡住请等待即可.**")
    except BadRequest:
        return
    # 服务器此前运行，当前带宽，（探针
    embyid, pwd1, lv = sqlhelper.select_one("select embyid,pwd,lv from emby where tg=%s", call.from_user.id)
    sever = nezha_res.sever_info()
    if lv == "d" or lv == "c":
        x = '**无权查看**'
    else:
        x = config["line"]
    await bot.edit_message_caption(
        call.from_user.id,
        call.message.id,
        caption=f'**▎⚡ 线路：**\n{x}\n\n**· 💌 用户密码 | ** `{pwd1}`\n\n' + sever + f'**· 🌏 - {call.message.date}**',
        reply_markup=ikb([[('🔙 - 用户', 'memembers'), ('❌ - 关闭', 'closeit')]]))

