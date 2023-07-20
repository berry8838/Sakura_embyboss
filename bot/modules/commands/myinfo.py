""""
myinfo - 个人信息
"""
from pyrogram import filters

from bot import bot, prefixes, Now
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.fix_bottons import group_f, cr_kk_ikb
from bot.func_helper.msg_utils import sendMessage, editMessage, deleteMessage
from bot.func_helper.utils import members_info


# 查看自己的信息
@bot.on_message(filters.command('myinfo', prefixes) & user_in_group_on_filter)
async def my_info(_, msg):
    await deleteMessage(msg)
    text, keyboard = await cr_kk_ikb(uid=msg.from_user.id, first=msg.from_user.first_name)
    await sendMessage(msg, text, timer=60)
