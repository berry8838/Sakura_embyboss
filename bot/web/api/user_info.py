#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
get_user_info -
Author:susu
Date:2024/8/27
"""

import json
from fastapi import APIRouter, Request
from bot.sql_helper.sql_emby import Emby, sql_get_emby, sql_update_emby
from bot.func_helper.emby import emby
from bot import LOGGER, group, bot

route = APIRouter()


@route.get("/user_info")
async def user_info(tg: str):
    # 从数据库获取用户信息
    user = sql_get_emby(tg)

    if not user:
        return {"code": 404, "message": "用户不存在"}
    return {"code": 200, "data": {"tg": user.tg, "iv": user.iv, "name": user.name, "embyid": user.embyid, "lv": user.lv, "cr": user.cr, "ex": user.ex}}


@route.post("/update_credit")
async def update_credit(request: Request):
    """
    修改用户积分
    :param request: 请求对象
    """
    try:
        content_type = request.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            data = await request.json()
            if isinstance(data, str):
                data = json.loads(data)
        else:
            form_data = await request.form()
            data = json.loads(form_data["data"]) if "data" in form_data else {}

        tg = data.get("tg")
        credit = data.get("credit")
        if not tg or credit is None:
            return {"code": 400, "message": "参数错误"}

        # 获取用户信息
        user = sql_get_emby(tg)
        if not user:
            return {"code": 404, "message": "用户不存在"}

        # 计算新的积分值
        new_iv = user.iv + int(credit)
        if new_iv < 0:
            return {"code": 400, "message": "积分不足"}
        # 更新用户积分
        user.iv = new_iv
        res = sql_update_emby(Emby.tg == tg, iv=new_iv)
        if res:

            return {
                "code": 200,
                "data": {"tg": user.tg, "iv": user.iv, "changed": credit},
            }
        else:
            return {"code": 500, "message": "更新失败"}
    except json.JSONDecodeError:
        return {"code": 400, "message": "无效的JSON格式"}
    except Exception as e:
        return {"code": 500, "message": f"服务器错误: {str(e)}"}

@route.post("/ban")
async def ban_user(request: Request):
    """
    封禁用户
    :param request: 请求对象
    """
    try:
        content_type = request.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            data = await request.json()
            if isinstance(data, str):
                data = json.loads(data)
        else:
            form_data = await request.form()
            data = json.loads(form_data["data"]) if "data" in form_data else {}

        query = data.get("query")
        if not query:
            return {"code": 400, "message": "参数错误"}

        # 获取用户信息 query 可以是 tg 或 embyname 或 embyid
        user = sql_get_emby(tg = query)
        if not user or not user.embyid:
            return {"code": 404, "message": "用户不存在"}
        
        disable_emby = await emby.emby_change_policy(emby_id=user.embyid, disable=True)
        
        if disable_emby:
            # 更新用户等级为封禁状态
            user.lv = 'c'  # 封禁状态
            sql_update_emby(Emby.tg == user.tg, lv='c')
            send_notification = f"#BAN通告\n用户 {user.name} (TG: #{user.tg}, EmbyID: {user.embyid}) 已被封禁。"
            LOGGER.info(send_notification)
            await bot.send_message(chat_id=group[0], text=send_notification)
            return {
                "code": 200,
                "data": {"tg": user.tg,"embyid": user.embyid, "name": user.name, "lv": user.lv},
            }
        else:
            return {"code": 500, "message": "封禁失败"}
    except json.JSONDecodeError:
        return {"code": 400, "message": "无效的JSON格式"}
    except Exception as e:
        return {"code": 500, "message": f"服务器错误: {str(e)}"}