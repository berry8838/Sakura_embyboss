#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
checkin.py - 签到验证API路由
"""
import random
import aiohttp
import json
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends, Header
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from pydantic import BaseModel
from typing import Optional

from bot import _open, bot_token, LOGGER, api as config_api, sakura_b 
from bot.sql_helper.sql_emby import sql_get_emby, sql_update_emby, Emby

# 创建路由
route = APIRouter(prefix="/checkin")

# 设置模板路径
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

# 从配置中获取 Cloudflare Turnstile 密钥
TURNSTILE_SITE_KEY = config_api.cloudflare_turnstile.site_key or "YOUR_TURNSTILE_SITE_KEY"
TURNSTILE_SECRET_KEY = config_api.cloudflare_turnstile.secret_key or "YOUR_TURNSTILE_SECRET_KEY"

class CheckinVerifyRequest(BaseModel):
    token: str
    user_id: int
    chat_id: Optional[int] = None
    message_id: Optional[int] = None

@route.get("/web", response_class=HTMLResponse)
async def checkin_page(request: Request):
    """签到页面 - 直接返回HTML，在前端通过Telegram WebApp API获取用户ID"""
    # 直接返回签到页面，不进行预先检查，由前端JS处理验证
    return templates.TemplateResponse(
        "checkin.html", 
        {"request": request, "site_key": TURNSTILE_SITE_KEY}
    )

@route.post("/verify")
async def verify_checkin(request: CheckinVerifyRequest, user_agent: str = Header(None)):
    """验证签到"""
    LOGGER.info(f"Checkin request from user_id: {request.user_id} with User-Agent: {user_agent}")
    
    if not _open.checkin:
        raise HTTPException(status_code=403, detail="签到功能未开启")
    
    # 检查用户是否存在
    e = sql_get_emby(request.user_id)
    if not e:
        raise HTTPException(status_code=404, detail="未查询到用户数据，请先注册账号")
    
    # 验证 Cloudflare Turnstile
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://challenges.cloudflare.com/turnstile/v0/siteverify",
            data={
                "secret": TURNSTILE_SECRET_KEY,
                "response": request.token,
                "remoteip": "0.0.0.0"  # 可选，可以从请求中获取
            }
        ) as response:
            result = await response.json()
            if not result.get("success", False):
                LOGGER.warning(f"Turnstile verification failed: {result}")
                raise HTTPException(status_code=400, detail="人机验证失败，请重试")
    
    # 处理签到逻辑
    now = datetime.now(timezone(timedelta(hours=8)))
    today = now.strftime("%Y-%m-%d")
    
    # 检查今天是否已经签到
    if e.ch and e.ch.strftime("%Y-%m-%d") >= today:
        raise HTTPException(status_code=409, detail="您今天已经签到过了！签到是无聊的活动哦。")
    
    # 处理签到奖励
    reward = random.randint(_open.checkin_reward[0], _open.checkin_reward[1])
    new_balance = e.iv + reward
    
    # 保存上次签到时间，用于计算连续签到天数
    last_checkin_time = e.ch
    
    # 更新emby表
    sql_update_emby(Emby.tg == request.user_id, iv=new_balance, ch=now)
    
    LOGGER.info(f"Successful checkin for user_id: {request.user_id}, reward: {reward}")
    
    # 构建签到成功消息
    checkin_text = f'🎉 **签到成功** | {reward} {sakura_b}\n💴 **当前持有** | {new_balance} {sakura_b}\n⏳ **签到日期** | {now.strftime("%Y-%m-%d")}'
    
    try:
        from bot import bot
        
        # 如果提供了面板消息的chat_id和message_id，尝试删除它
        if request.chat_id and request.message_id:
            try:
                await bot.delete_messages(
                    chat_id=request.chat_id,
                    message_ids=request.message_id
                )
                LOGGER.info(f"已删除签到面板消息: chat_id={request.chat_id}, message_id={request.message_id}")
            except Exception as e:
                LOGGER.error(f"删除签到面板消息时出错: {str(e)}")
        
        # 发送签到成功私聊消息
        await bot.send_message(
            chat_id=request.user_id,
            text=checkin_text
        )
        LOGGER.info(f"已发送签到成功消息给用户 {request.user_id}")
    except Exception as e:
        LOGGER.error(f"发送私聊消息给用户 {request.user_id} 时出错: {str(e)}")
    
    # 返回结果给WebApp，让它关闭
    return JSONResponse({
        "success": True,
        "message": "签到成功",
        "reward": f"获得 {reward} {sakura_b}，当前持有 {new_balance} {sakura_b}",
        "should_close": True
    }) 