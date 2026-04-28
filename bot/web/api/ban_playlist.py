#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
get_user_ban - 
Author:susu
Date:2024/8/27
"""
from fastapi import APIRouter
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby
from bot import LOGGER, group, bot
from bot.func_helper.emby import emby
from datetime import datetime

route = APIRouter()


@route.get("/ban_playlist")
async def ban_playlist(eid: str):
    """
    获取传入的embyid，然后执行查询，删除，发送消息至tg群组
    """
    if not eid:
        return {"user_id": None, "embyid": None, "is_baned": False}

    user = sql_get_emby(eid)
    lv_display = {'a': '白名单', 'b': '普通用户', 'c': '封禁用户', 'd': '未注册'}
    if user is None:
        details = ''
        if await emby.emby_change_policy(emby_id=eid, disable=True):
            details += "已拦截到疑似敏感操作播放列表，未在emby数据库中找到此数据，但已斩杀该用户（封禁）"
        else:
            details += "已拦截到疑似敏感操作播放列表，未在emby数据库中找到此数据，未能斩杀该用户（封禁）。详细时间见log记录，请手动斩杀。"
        info = {"user_id": None, "embyid": None, "is_baned": False, "details": details}
        text = (
            f"🚫 新建播放列表拦截\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 用户: Unknown\n"
            f"🆔 Emby ID: {eid}\n"
            f"📱 TG ID: Unknown\n"
            f"🏷️ 用户等级: 未注册\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚨 处理措施: {details}\n"
            f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        await bot.send_message(chat_id=group[0], text=text)
        LOGGER.warning(text)
        return info

    if await emby.emby_change_policy(emby_id=eid, disable=True):
        action = "✅ 已封禁用户"
        info = {"user_id": user.tg, "emby_name": user.name, "embyid": eid, "is_baned": True,
                "details": "已拦截疑似敏感操作播放列表，用户已被斩杀（封禁）。请向权限管理员描述信息。"}
        text = (
            f"🚫 新建播放列表拦截\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 用户: {user.name}\n"
            f"🆔 Emby ID: {eid}\n"
            f"📱 TG ID: [{user.tg}](tg://user?id={user.tg})\n"
            f"🏷️ 用户等级: {lv_display.get(user.lv, '未知')}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚨 处理措施: {action}\n"
            f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        try:
            out = await bot.send_message(group[0], text)
            await out.forward(user.tg)
            sql_update_emby(Emby.tg == info["user_id"], lv='c')
        except Exception as e:
            text += str(e)

    else:
        action = "❌ 封禁失败，请手动处理"
        info = {"user_id": user.tg, "emby_name": user.name, "embyid": eid, "is_baned": False,
                "details": "已拦截疑似敏感操作播放列表，斩杀（封禁）失败，请手动处理。"}
        text = (
            f"🚫 新建播放列表拦截\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 用户: {user.name}\n"
            f"🆔 Emby ID: {eid}\n"
            f"📱 TG ID: [{user.tg}](tg://user?id={user.tg})\n"
            f"🏷️ 用户等级: {lv_display.get(user.lv, '未知')}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚨 处理措施: {action}\n"
            f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        try:
            out = await bot.send_message(group[0], text)
            await out.forward(user.tg)
        except Exception as e:
            text += str(e)
    LOGGER.warning(text)
    return info
