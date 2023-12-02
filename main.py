#! /usr/bin/python3
# -*- coding: utf-8 -*-
import uvloop

uvloop.install()
from bot import bot

# 定时任务与基础
from bot.modules import (backup_db, bot_commands, check_restart, check_ex, ranks_task, userplays_rank)
# 面板
from bot.modules.panel import (admin_panel, config_panel, kk, member_panel, server_panel, sched_panel)
# 命令
from bot.modules.commands import (admin, coins, exchange, emby_libs, myinfo, pro_rev, renew, rmemby, renewall, start,
                                  score, sync_unbound, sync_group, bindall_id)
# 其他
from bot.modules.extra import (urm, create)
from bot.modules.callback import (checkin, close_it, leave_delemby, leave_unauth_group, on_inline_query)

bot.run()
