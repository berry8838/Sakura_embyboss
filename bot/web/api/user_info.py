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

route = APIRouter()


@route.get("/user_info")
async def user_info(tg: str):
    # 从数据库获取用户信息
    user = await sql_get_emby(tg)

    if not user:
        return {"code": 404, "message": "用户不存在"}
    return {"code": 200, "data": {"tg": user.tg, "iv": user.iv}}


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
