import asyncio
import random
from datetime import datetime, timezone, timedelta

from pyrogram import filters

from bot import bot, _open, sakura_b, LOGGER
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.msg_utils import callAnswer, sendMessage, deleteMessage
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby
from bot.sql_helper.sql_ip import (
    add_checkin_ip_record, 
    is_ip_blacklisted, 
    get_distinct_users_by_ip_today,
    add_ip_to_blacklist
)

# IP签到限制
MAX_USERS_PER_IP = 5  # 每个IP每天最多可签到的不同用户数

@bot.on_callback_query(filters.regex('checkin') & user_in_group_on_filter)
async def user_in_checkin(_, call):
    now = datetime.now(timezone(timedelta(hours=8)))
    today = now.strftime("%Y-%m-%d")
    if ':' not in call.data:
        await callAnswer(call, '📅 这个签到按钮已过期，请重新打开菜单签到。', True)
        return
    else:
        _, date_str = call.data.split(':', 1)
        if date_str != today:
            await callAnswer(call, '📅 这个签到按钮已过期，请重新打开菜单签到。', True)
            return

    # 获取用户IP
    user_ip = None
    if hasattr(call, 'from_peer') and hasattr(call.from_peer, 'ip_address'):
        user_ip = call.from_peer.ip_address
    
    # 记录签到请求
    if user_ip:
        LOGGER.info(f"Callback checkin request from user_id: {call.from_user.id} with IP: {user_ip}")
        
        # 检查IP是否在黑名单中
        if is_ip_blacklisted(user_ip):
            LOGGER.warning(f"IP {user_ip} 在黑名单中，拒绝用户 {call.from_user.id} 的签到请求")
            await callAnswer(call, '⛔ 您的IP已被禁止签到', True)
            return

    if _open.checkin:
        e = sql_get_emby(call.from_user.id)
        if not e:
            await callAnswer(call, '🧮 未查询到数据库', True)
            return

        elif not e.ch or e.ch.strftime("%Y-%m-%d") < today:
            # 如果有IP，检查该IP今天签到的不同用户数
            if user_ip:
                # 获取今天使用该IP签到的所有不同用户
                users = get_distinct_users_by_ip_today(user_ip)
                
                # 检查是否已经达到限制
                if call.from_user.id not in users and len(users) >= MAX_USERS_PER_IP:
                    # 将IP加入黑名单
                    add_ip_to_blacklist(user_ip, f"单日签到用户数超过{MAX_USERS_PER_IP}个")
                    LOGGER.warning(f"IP {user_ip} 当日签到用户数超限，已加入黑名单")
                    await callAnswer(call, '⛔ 此IP今日签到用户数已达上限，IP已被禁止', True)
                    return

            reward = random.randint(_open.checkin_reward[0], _open.checkin_reward[1])
            s = e.iv + reward
            sql_update_emby(Emby.tg == call.from_user.id, iv=s, ch=now)
            
            # 记录签到IP
            if user_ip:
                add_checkin_ip_record(user_ip, call.from_user.id, now)
            
            text = f'🎉 **签到成功** | {reward} {sakura_b}\n💴 **当前持有** | {s} {sakura_b}\n⏳ **签到日期** | {now.strftime("%Y-%m-%d")}'
            await asyncio.gather(deleteMessage(call), sendMessage(call, text=text))

        else:
            await callAnswer(call, '⭕ 您今天已经签到过了，再签到剁掉你的小鸡鸡🐤。', True)
    else:
        await callAnswer(call, '❌ 未开启签到功能，等待！', True)
