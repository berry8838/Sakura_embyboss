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

route = APIRouter()


@route.get("/ban_playlist")
async def ban_playlist(eid: str):
    """
    获取传入的embyid，然后执行查询，删除，发送消息至tg群组
    """
    if not eid:
        return {"user_id": None, "embyid": None, "is_baned": False}

    user = sql_get_emby(eid)
    if user is None:
        details = ''
        if await emby.emby_change_policy(emby_id=eid, disable=True):
            details += "已拦截到疑似敏感操作播放列表，未在emby数据库中找到此数据，但已斩杀该用户（封禁）"
        else:
            details += "已拦截到疑似敏感操作播放列表，未在emby数据库中找到此数据，未能斩杀该用户（封禁）。详细时间见log记录，请手动斩杀。"
        info = {"user_id": None, "embyid": None, "is_baned": False, "details": details}
        text = ("【新建播放列表拦截】\n\n"
                f"{eid} - {info['details']}\n")
        await bot.send_message(chat_id=group[0], text=text)
        LOGGER.info(text)
        return info

    if await emby.emby_change_policy(emby_id=eid, disable=True):
        info = {"user_id": user.tg, "emby_name": user.name, "embyid": eid, "is_baned": True,
                "details": "已拦截疑似敏感操作播放列表，用户已被斩杀（封禁）。请向权限管理员描述信息。"}
        text = (f"【新建播放列表拦截】\n\n"
                f"[你](tg://user?id={user.tg}) 已被检测到新封禁用户\n"
                f"Emby：{user.name}  |  ID：`{user.tg}`\n"
                f'封禁原因：{info["details"]}')
        try:
            out = await bot.send_message(group[0], text)
            await out.forward(user.tg)
            sql_update_emby(Emby.tg == info["user_id"], lv='c')
        except Exception as e:
            text += e

    else:
        info = {"user_id": user.tg, "emby_name": user.name, "embyid": eid, "is_baned": False,
                "details": "已拦截疑似敏感操作播放列表，斩杀（封禁）失败，请手动处理。"}
        text = ("【新建播放列表拦截】\n\n"
                f"[你](tg://user?id={user.tg}) 已被检测到新封禁用户\n"
                f"Emby：{user.name}  |  ID：`{user.tg}`\n"
                f'封禁原因：{info["details"]}')
        try:
            await bot.send_message(group[0], text)
        except Exception as e:
            text += e
    LOGGER.info(text)
    return info
