import asyncio
import random
from datetime import datetime, timezone, timedelta

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot, _open, sakura_b
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.msg_utils import callAnswer, sendMessage, deleteMessage
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby

# Helper to check if user has checked in today
def has_checked_in_today(e, today):
    return e.ch and e.ch.strftime("%Y-%m-%d") == today

@bot.on_callback_query(filters.regex('checkin') & user_in_group_on_filter)
async def user_in_checkin(_, call):
    now = datetime.now(timezone(timedelta(hours=8)))
    today = now.strftime("%Y-%m-%d")
    if not _open.checkin:
        await callAnswer(call, '❌ 未开启签到功能，等待！', True)
        return

    e = sql_get_emby(call.from_user.id)
    if not e:
        await callAnswer(call, '🧮 未查询到数据库', True)
        return

    if has_checked_in_today(e, today):
        await callAnswer(call, '⭕ 您今天已经签到过了！签到是无聊的活动哦。', True)
        return

    # First check-in: offer both options
    reward = random.randint(_open.checkin_reward[0], _open.checkin_reward[1])
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ 领取奖励", callback_data=f"confirm_checkin_reward:{reward}"),
                InlineKeyboardButton("🔄 再签到一次", callback_data="redo_checkin"),
            ]
        ]
    )
    text = (
        f"🎉 **签到成功**，请确认是否领取本次奖励：\n\n"
        f"本次签到奖励为：{reward} {sakura_b}\n\n"
        "点击【领取奖励】获得本次签到奖励，签到流程结束；\n"
        "点击【再签到一次】可重新签到并获得新的随机奖励（只能再签到一次）。"
    )
    await asyncio.gather(deleteMessage(call), sendMessage(call, text=text, reply_markup=markup))


@bot.on_callback_query(filters.regex(r"^redo_checkin$") & user_in_group_on_filter)
async def redo_checkin(_, call):
    now = datetime.now(timezone(timedelta(hours=8)))
    today = now.strftime("%Y-%m-%d")
    e = sql_get_emby(call.from_user.id)
    if not e:
        await callAnswer(call, '🧮 未查询到数据库', True)
        return
    # Only allow re-checkin if user hasn't checked in yet
    if has_checked_in_today(e, today):
        await callAnswer(call, '⭕ 您今天已经签到过了！签到是无聊的活动哦。', True)
        return

    # After re-sign-in, must get reward, cannot re-sign-in again
    reward = random.randint(_open.checkin_reward[0], _open.checkin_reward[1])
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("✅ 领取奖励", callback_data=f"confirm_checkin_reward:{reward}"),
            ]
        ]
    )
    text = (
        f"🎉 **重新签到成功**，请领取本次奖励：\n\n"
        f"本次签到奖励为：{reward} {sakura_b}\n\n"
        "点击【领取奖励】获得本次签到奖励，签到流程结束。\n"
        "（只能重新签到一次）"
    )
    await asyncio.gather(deleteMessage(call), sendMessage(call, text=text, reply_markup=markup))


@bot.on_callback_query(filters.regex(r"^confirm_checkin_reward:(\d+)$") & user_in_group_on_filter)
async def confirm_checkin_reward(_, call):
    import re
    m = re.match(r"^confirm_checkin_reward:(\d+)$", call.data)
    if not m:
        await callAnswer(call, "参数错误，无法领取奖励。", True)
        return
    reward = int(m.group(1))

    now = datetime.now(timezone(timedelta(hours=8)))
    today = now.strftime("%Y-%m-%d")
    e = sql_get_emby(call.from_user.id)
    if not e:
        await callAnswer(call, '🧮 未查询到数据库', True)
        return

    if has_checked_in_today(e, today):
        await callAnswer(call, '⭕ 您今天已经签到过了！签到是无聊的活动哦。', True)
        return

    s = e.iv + reward
    sql_update_emby(Emby.tg == call.from_user.id, iv=s, ch=now)
    text = (
        f'🎉 **奖励已领取** | {reward} {sakura_b}\n'
        f'💴 **当前持有** | {s} {sakura_b}\n'
        f'⏳ **签到日期** | {now.strftime("%Y-%m-%d")}'
    )
    await asyncio.gather(deleteMessage(call), sendMessage(call, text=text))
