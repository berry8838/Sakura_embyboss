# 面板的购买键
from bot import bot, user_buy
from pyrogram import filters

from bot.func_helper.fix_bottons import buy_sth_ikb
from bot.func_helper.msg_utils import callAnswer, editMessage


@bot.on_callback_query(filters.regex('buy_account'))
async def buy_some(_, call):
    u = await editMessage(call, '🛒请选择购买对应时长的套餐：\n网页付款后会发邀请码连接，点击跳转到bot开始注册和续期程式。',
                          buttons=buy_sth_ikb())
    if u is False:
        await callAnswer(call, '🚫 按钮设置错误，请上报管理', True)

    await callAnswer(call, "🔖 进入购买")
