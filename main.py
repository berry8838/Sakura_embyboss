#! /usr/bin/python3
# -*- coding: utf-8 -*-
import asyncio
import uvloop

uvloop.install()
from bot import bot

# 定时任务与基础


from bot.modules import bot_commands, check_restart, check_ex, leave_delemby, leave_unauth_group, ranks_task, \
    userplays_rank
# 面板
from bot.modules.panel import admin_panel, config_panel, member_panel, server_panel, user_buy, sched_panel
# 细化
from bot.modules.commands import admin, close_it, rmemby, kk, myinfo, pro_rev, renew, restart, renewall, \
    score, start, sync_group, sync_unbound, coins, checkin, emby_libs
from bot.modules.extra import create, urm

bot.run()
