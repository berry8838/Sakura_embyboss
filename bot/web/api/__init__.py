#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
__init__.py - 
Author:susu
Date:2024/8/27
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from .ban_playlist import route as ban_playlist_route
from .webhook.favorites import router as favorites_router
from .webhook.media import router as media_router
from .webhook.client_filter import router as client_filter_router
from .user_info import route as user_info_route
from .login import router as login_router
from bot import bot_token, LOGGER

emby_api_route = APIRouter(prefix="/emby", tags=["对接Emby的接口"])
user_api_route = APIRouter(prefix="/user", tags=["对接用户信息的接口"])
auth_api_route = APIRouter(prefix="/auth", tags=["用户认证接口"])

async def verify_token(request: Request):
    """验证API请求的token"""
    try:
        # 从URL参数中获取token
        token = request.query_params.get("token")
        if not token:
            raise HTTPException(status_code=401, detail="No token provided")
        # 验证token是否与bot token匹配
        if token != bot_token:
            LOGGER.warning(f"Invalid token attempt: {token[:10]}...")
            raise HTTPException(status_code=403, detail="Invalid token")
        return True
    except HTTPException:
        raise
    except Exception as e:
        LOGGER.error(f"Token verification error: {str(e)}")
        raise HTTPException(status_code=500, detail="Token verification failed")

emby_api_route.include_router(
    ban_playlist_route,
)
emby_api_route.include_router(
    favorites_router,
    dependencies=[Depends(verify_token)]
)
emby_api_route.include_router(
    media_router,
    dependencies=[Depends(verify_token)]
)
emby_api_route.include_router(
    client_filter_router,
    dependencies=[Depends(verify_token)]
)
user_api_route.include_router(
    user_info_route,
    dependencies=[Depends(verify_token)]
)
auth_api_route.include_router(
    login_router,
    dependencies=[Depends(verify_token)]
)

