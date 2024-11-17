#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
__init__.py - 
Author:susu
Date:2024/8/27
"""
from fastapi import APIRouter
from .ban_playlist import route as ban_playlist_route
from .favorites import router as favorites_router

emby_api_route = APIRouter(prefix="/emby", tags=["对接Emby的接口"])

emby_api_route.include_router(ban_playlist_route)
emby_api_route.include_router(favorites_router)
