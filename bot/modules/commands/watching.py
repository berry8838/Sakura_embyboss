#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
查看当前Emby播放状态命令模块
"""

from pyrogram import filters
from pyrogram.types import Message
from bot import bot, prefixes
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.utils import split_long_message


@bot.on_message(filters.command(["watching", "playing"], prefixes) & admins_on_filter)
async def watching_command(_, message: Message):
    """
    watching / playing 命令 - 查看当前播放状态（不显示用户名、设备名）
    """
    processing_msg = await message.reply("📊 正在获取 Emby 服务器当前状态...")

    try:
        # 发送请求获取活跃会话
        result = await emby._request("GET", "/emby/Sessions")

        if not result.success:
            error_text = f"**Emby 服务器状态：🔴 OFFLINE**\n\n**错误原因:** {result.error or '连接超时或未知错误'}\n请检查 Emby 服务状态或网络配置。"
            await processing_msg.edit_text(error_text)
            return

        if result.data is None:
            await processing_msg.edit_text("❌ **获取播放数据失败:** 服务器返回空数据")
            return

        # 统计播放信息与在线人数
        playing_sessions = []
        online_users = set()

        for session in result.data:
            # 统计在线人数（拥有UserId的活跃会话数/独特用户数）
            user_id = session.get("UserId")
            if user_id:
                online_users.add(user_id)

            # 统计正在播放的会话
            if session.get("NowPlayingItem"):
                playing_sessions.append(session)

        total_online = len(online_users)
        total_playing = len(playing_sessions)

        # 构建报告文本
        report = "📊 **Emby 服务器当前状态**\n\n"
        report += "🟢 **服务器状态:** ONLINE\n"
        report += f"👥 **当前在线人数:** `{total_online}` 人\n"
        report += f"🎬 **当前播放会话:** `{total_playing}` 个\n\n"

        if total_playing == 0:
            report += "当前没有用户在观看媒体。"
            await processing_msg.edit_text(report)
            return

        # 详细播放列表（完全隐藏用户名、设备名和 IP）
        report += "📝 **当前播放影片列表:**\n"
        for idx, session in enumerate(playing_sessions, 1):

            # 播放媒体信息
            now_playing = session.get("NowPlayingItem", {})
            media_type = now_playing.get("Type", "Unknown")
            name = now_playing.get("Name", "未知")

            # 格式化剧集名称
            if media_type == "Episode":
                series_name = now_playing.get("SeriesName")
                if series_name:
                    season_name = now_playing.get("SeasonName")
                    if season_name:
                        name = f"{series_name} ({season_name}) - {name}"
                    else:
                        name = f"{series_name} - {name}"

            # 中文翻译媒体类型
            media_type_cn = "未知"
            if media_type == "Movie":
                media_type_cn = "电影 🎬"
            elif media_type == "Episode":
                media_type_cn = "剧集 📺"
            elif media_type == "Audio":
                media_type_cn = "音乐 🎵"
            else:
                media_type_cn = f"{media_type} 🎥"

            # 是否暂停
            play_state = session.get("PlayState", {})
            is_paused = play_state.get("IsPaused", False)
            status_tag = "⏸️ 已暂停" if is_paused else "▶️ 播放中"

            report += f"{idx}. 🎬 影片: `{name}`\n"
            report += (
                f"    类型: {media_type_cn} | 状态: {status_tag}\n"
            )

        # 检查消息是否过长并分割发送
        report_texts = split_long_message(report)
        if len(report_texts) > 0:
            await processing_msg.edit_text(report_texts[0])
            for extra_report in report_texts[1:]:
                await message.reply(extra_report)

    except Exception as e:
        await processing_msg.edit_text(f"❌ **发生未知错误:** {str(e)}")
