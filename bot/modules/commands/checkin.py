import asyncio
from datetime import datetime, timezone, timedelta

from pyrogram import filters

from bot import bot, _open, bot_photo, sakura_b
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.fix_bottons import checkin_button, back_start_ikb
from bot.func_helper.msg_utils import callAnswer, editMessage, call_dice_Listen, sendPhoto
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby


@bot.on_callback_query(filters.regex('checkin') & user_in_group_on_filter)
async def user_in_checkin(_, call):
    now = datetime.now(timezone(timedelta(hours=8)))
    now_i = now.strftime("%Y-%m-%d")
    if _open["checkin"]:
        e = sql_get_emby(tg=call.from_user.id)
        if e.ch is None or e.ch.strftime("%Y-%m-%d") < now_i:
            await editMessage(call,
                              f'🎯 **签到说明**：\n\n在120s内发送「🎲」「🎳」「🎯」三个emoji表情里任意表情。随机获得1-6积分')
            d = await call_dice_Listen(call, timer=120, buttons=checkin_button)
            # print(d)
            if d is False:
                return
            if d.dice.emoji == '🎰':
                iv = e.iv - int(d.dice.value)
            else:
                iv = e.iv + int(d.dice.value)
            sql_update_emby(Emby.tg == call.from_user.id, iv=iv, ch=now)
            await asyncio.gather(call.message.delete(), sendPhoto(call, photo=bot_photo,
                                                                  caption=f'⭕ **今日签到** | {d.dice.value} c\n🪙 **当前{sakura_b} | {iv} c**',
                                                                  buttons=back_start_ikb))
        else:
            await callAnswer(call, '⭕ 您今天已经签到过了！签到是无聊的活动哦。', True)
    else:
        await callAnswer(call, '❌ 未开启签到系统，等待！', True)
