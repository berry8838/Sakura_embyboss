#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
__init__.py - 
Author:susu
Date:2024/8/27
"""
import asyncio
import errno

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from .api import emby_api_route, user_api_route
from bot import api as config_api, LOGGER


class Web:

    """
    Web 类用于初始化和管理 FastAPI 应用程序。
    """

    def __init__(self):
        """
        初始化 Web 类实例。
        """
        self.app: FastAPI = FastAPI()
        self.web_api = None
        self.start_api = None

    def init_api(self):
        """
        初始化 API 路由和 CORS 中间件。
        """
        # 添加路由 /
        self.app.include_router(emby_api_route)
        self.app.include_router(user_api_route)
        # 配字 CORS 的中间件
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=config_api.allow_origins,  # 来源，可能有多个服务器的nginx，懒得写入配置会直接全梭了，需要的可以自己在字段里面加
            allow_credentials=True,  # 允许使用证书
            allow_methods=["*"],  # 允许跨域的方法
            allow_headers=["*"])  # 允许的请求头

    async def start(self):
        """
        启动 Web API 服务。
        """
        if not config_api.status:
            LOGGER.info("【API服务】未配置，跳过...")
            return
        LOGGER.info("【API服务】检测有配置，马上启动服务...")
        import uvicorn

        self.init_api()
        self.web_api = uvicorn.Server(
            config=uvicorn.Config(self.app, host=config_api.http_url, port=config_api.http_port)
        )
        server_config = self.web_api.config
        if not server_config.loaded:
            server_config.load()  # 加载配置
        self.web_api.lifespan = server_config.lifespan_class(server_config)
        try:
            await self.web_api.startup()
        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                LOGGER.error(f"【API服务】端口 {config_api.http_port} 被占用，请修改配置文件.")
            LOGGER.error("【API服务】启动失败，退出ing...")
            raise SystemExit from None
        if self.web_api.should_exit:
            LOGGER.error("【API服务】启动失败，退出ing...")
            raise SystemExit from None

        LOGGER.info("【API服务】 启动成功!")

    def stop(self):
        """
        停止 Web API 服务。
        """
        if self.start_api:
            LOGGER.info("正在停止 API 服务...")
            try:
                self.start_api.cancel()
                # 等待任务结束
                asyncio.run(self.start_api)
            except asyncio.CancelledError:
                pass
            finally:
                LOGGER.info("API 服务已停止。")


check = Web()

# 初始化
loop = asyncio.get_event_loop()
loop.create_task(check.start())
