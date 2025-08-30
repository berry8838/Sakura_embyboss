import asyncio
import random
from datetime import datetime, timezone, timedelta

from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup
from pyromod.helpers import ikb

from bot import bot, _open, sakura_b
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.msg_utils import callAnswer, sendMessage, deleteMessage, editMessage
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby

# Track users with pending rewards (in-memory set)
pending_rewards = set()


@bot.on_callback_query(filters.regex('checkin') & user_in_group_on_filter)
async def user_in_checkin(_, call):
    now = datetime.now(timezone(timedelta(hours=8)))
    today = now.strftime("%Y-%m-%d")
    if _open.checkin:
        e = sql_get_emby(call.from_user.id)
        if not e:
            await callAnswer(call, '🧮 未查询到数据库', True)
        elif not e.embyid:
            await callAnswer(call, '❌ 您还没有Emby账号，无法签到', True)
        elif not e.ch or e.ch.strftime("%Y-%m-%d") < today:
            # First step: Mark as checked-in but don't give reward yet
            sql_update_emby(Emby.tg == call.from_user.id, ch=now)
            pending_rewards.add(call.from_user.id)
            
            # Show claim reward button
            claim_button = ikb([[('🎁 领取奖励', 'checkin-claim')]])
            text = f'✅ **签到成功！**\n⏳ **签到日期** | {now.strftime("%Y-%m-%d")}\n\n🎁 点击下方按钮领取今日签到奖励：'
            await asyncio.gather(deleteMessage(call), sendMessage(call, text=text, buttons=claim_button))
        elif call.from_user.id in pending_rewards:
            # Show claim reward button if user already checked in but hasn't claimed
            claim_button = ikb([[('🎁 领取奖励', 'checkin-claim')]])
            text = f'✅ **您今天已经签到！**\n⏳ **签到日期** | {today}\n\n🎁 点击下方按钮领取今日签到奖励：'
            await asyncio.gather(deleteMessage(call), sendMessage(call, text=text, buttons=claim_button))
        else:
            await callAnswer(call, '⭕ 您今天已经签到并领取奖励了！签到是无聊的活动哦。', True)
    else:
        await callAnswer(call, '❌ 未开启签到功能，等待！', True)


@bot.on_callback_query(filters.regex('checkin-claim') & user_in_group_on_filter)
async def user_claim_reward(_, call):
    if not _open.checkin:
        await callAnswer(call, '❌ 未开启签到功能，等待！', True)
        return
        
    if call.from_user.id not in pending_rewards:
        await callAnswer(call, '❌ 您今天还没有签到或已经领取过奖励了！', True)
        return
    
    e = sql_get_emby(call.from_user.id)
    if not e:
        await callAnswer(call, '🧮 未查询到数据库', True)
        return
    elif not e.embyid:
        await callAnswer(call, '❌ 您还没有Emby账号，无法领取奖励', True)
        return
    
    # Second step: Give the reward
    reward = random.randint(_open.checkin_reward[0], _open.checkin_reward[1])
    s = e.iv + reward
    sql_update_emby(Emby.tg == call.from_user.id, iv=s)
    
    # Remove from pending rewards
    pending_rewards.discard(call.from_user.id)
    
    now = datetime.now(timezone(timedelta(hours=8)))
    text = f'🎉 **奖励领取成功！** | {reward} {sakura_b}\n💴 **当前持有** | {s} {sakura_b}\n⏳ **签到日期** | {now.strftime("%Y-%m-%d")}'
    await asyncio.gather(deleteMessage(call), sendMessage(call, text=text))
