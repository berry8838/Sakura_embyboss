#! /usr/bin/python3
# -*- coding: utf-8 -*-
"""
审计命令模块 - 提供 IP、设备名和客户端名审计功能
包含 auditip、auditdevice 和 auditclient 三个管理员专用命令
"""

import re
from datetime import datetime
from pyrogram import filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from bot import bot, LOGGER
from bot.func_helper.emby import emby
from bot.func_helper.filters import admins_on_filter
from bot.func_helper.msg_utils import sendMessage, editMessage
from bot.func_helper.utils import split_long_message
import asyncio


@bot.on_message(filters.command("auditip") & admins_on_filter)
async def audit_ip_command(_, message: Message):
    """
    auditip 命令 - 根据 IP 地址审计用户活动
    用法: /auditip <IP地址> [天数]
    示例: /auditip 192.168.1.100 30
    """
    try:
        # 解析命令参数
        args = message.text.split()
        if len(args) < 2:
            help_text = (
                "**🔍 IP 审计命令使用说明**\n\n"
                "**用法:** `/auditip <IP地址> [天数]`\n\n"
                "**参数说明:**\n"
                "• `IP地址` - 要审计的 IP 地址（必需）\n"
                "• `天数` - 查询天数范围，默认全部时间（可选）\n\n"
                "**示例:**\n"
                "• `/auditip 192.168.1.100` - 查询该 IP 全部时间的用户活动\n"
                "• `/auditip 192.168.1.100 7` - 查询该 IP 最近7天的用户活动\n\n"
                "**功能:**\n"
                "• 查找使用指定 IP 地址的所有用户\n"
                "• 显示用户设备信息和活动统计\n"
                "• 检测潜在的账号共享行为"
            )
            await sendMessage(message, help_text)
            return

        ip_address = args[1]
        days = None  # 默认查询所有
        
        # 解析天数参数
        if len(args) >= 3:
            try:
                days = int(args[2])
                if days <= 0 or days > 3650:
                    await sendMessage(message, "❌ 天数参数必须在 1-3650 之间")
                    return
            except ValueError:
                await sendMessage(message, "❌ 天数参数必须是有效的数字")
                return

        # 验证 IP 地址格式
        ip_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
        if not re.match(ip_pattern, ip_address):
            await sendMessage(message, "❌ 无效的 IP 地址格式，请输入有效的 IPv4 地址")
            return

        # 发送处理中消息
        processing_msg = await message.reply(f"🔍 正在审计 IP 地址 `{ip_address}` {days if days else '所有时间'} 的活动...")

        # 调用审计 API
        success, result = await emby.get_users_by_ip(ip_address, days)
        
        if not success:
            error_text = f"❌ **IP 审计失败**\n\n**错误信息:** {result}"
            await editMessage(processing_msg, error_text)
            return

        if not result:
            no_data_text = (
                f"📊 **IP 审计结果**\n\n"
                f"**IP 地址:** `{ip_address}`\n"
                f"**查询范围:** {days if days else '所有时间'}\n"
                f"**结果:** 未找到任何用户活动记录\n\n"
                f"**可能原因:**\n"
                f"• 该 IP 地址在指定时间内未被使用\n"
                f"• 用户活动记录已过期\n"
                f"• IP 地址输入错误"
            )
            await editMessage(processing_msg, no_data_text)
            return

        # 构建审计报告
        report_text = "📊 **IP 审计报告**\n\n"
        report_text += f"**🌐 IP 地址:** `{ip_address}`\n"
        report_text += f"**📅 查询范围:** {days if days else '所有时间'}\n"
        report_text += f"**👥 发现用户:** {len(result)} 个\n\n"
        
        # 按活动时间排序
        sorted_users = sorted(result, key=lambda x: x['LastActivity'], reverse=True)
        
        report_text += "**📋 用户活动详情:**\n"
        report_text += "=" * 40 + "\n"
        
        for i, user_info in enumerate(sorted_users, 1):
            # 格式化最后活动时间
            try:
                last_activity = datetime.fromisoformat(user_info['LastActivity'].replace('Z', '+00:00'))
                formatted_time = last_activity.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError, KeyError):
                formatted_time = user_info['LastActivity']
            
            report_text += f"**{i}. {user_info['Username']}**\n"
            report_text += f"   • 用户ID: `{user_info['UserId']}`\n"
            report_text += f"   • 设备名: `{user_info['DeviceName']}`\n"
            report_text += f"   • 客户端: `{user_info['ClientName']}`\n"
            report_text += f"   • 最后活动: `{formatted_time}`\n"
            report_text += f"   • 活动次数: `{user_info['ActivityCount']}`\n\n"

        # 添加安全提醒
        if len(result) > 1:
            report_text += "⚠️ **安全提醒:**\n"
            report_text += f"发现 {len(result)} 个用户使用同一 IP 地址，请注意是否存在账号共享行为。\n\n"
        
        report_text += f"**📊 审计完成时间:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
        report_texts = split_long_message(report_text)
        for report_text in report_texts:
            try:
                await bot.send_message(message.chat.id, report_text)
            except FloodWait as f:
                LOGGER.warning(str(f))
                await asyncio.sleep(f.value * 1.2)
        LOGGER.info(f"管理员 {message.from_user.id} 执行了 IP 审计: {ip_address}")

    except Exception as e:
        error_text = f"❌ **IP 审计异常**\n\n**错误信息:** {str(e)}"
        await sendMessage(message, error_text)
        LOGGER.error(f"IP 审计命令异常: {str(e)}")


@bot.on_message(filters.command("auditdevice") & admins_on_filter)
async def audit_device_name_command(_, message: Message):
    """
    auditdevice 命令 - 根据设备名 审计用户
    用法: /auditdevice <设备名关键词> [天数]
    示例: /auditdevice Chrome 30
    """
    try:
        # 解析命令参数
        args = message.text.split(None, 2)  # 使用 None 和限制分割次数，支持包含空格的设备名
        if len(args) < 2:
            help_text = (
                "**🔍 设备名 审计命令使用说明**\n\n"
                "**用法:** `/auditdevice <设备名关键词> [天数]`\n\n"
                "**参数说明:**\n"
                "• `设备名关键词` - 要搜索的设备名 关键词（必需）\n"
                "• `天数` - 查询天数范围，默认全部时间（可选）\n\n"
                "**示例:**\n"
                "• `/auditdevice Chrome` - 查询使用 Chrome 浏览器的用户的活动\n"
                "• `/auditdevice Android 7` - 查询最近7天使用 Android 设备的用户的活动\n"
                "• `/auditdevice Emby` - 查询使用 Emby 客户端的用户的活动\n\n"
                "**功能:**\n"
                "• 根据设备名 查找相关用户\n"
                "• 分析设备使用情况\n"
                "• 检测异常或可疑的设备"
            )
            await sendMessage(message, help_text)
            return

        device_keyword = args[1]
        days = None
        # 解析天数参数
        if len(args) >= 3:
            try:
                days = int(args[2])
                if days <= 0 or days > 3650:
                    await sendMessage(message, "❌ 天数参数必须在 1-3650 之间")
                    return
            except ValueError:
                await sendMessage(message, "❌ 天数参数必须是有效的数字")
                return

        # 发送处理中消息
        processing_msg = await message.reply(f"🔍 正在审计包含 `{device_keyword}` 的设备名 {days if days else '所有时间'} 的使用情况...")

        # 调用设备名 审计 API
        success, result = await emby.get_users_by_device_name(device_keyword, days)
        
        if not success:
            error_text = f"❌ **设备名审计失败**\n\n**错误信息:** {result}"
            await editMessage(processing_msg, error_text)
            return

        if not result:
            no_data_text = (
                f"📊 **设备名审计结果**\n\n"
                f"**关键词:** `{device_keyword}`\n"
                f"**查询范围:** {days if days else '所有时间'}\n"
                f"**结果:** 未找到任何匹配的用户活动记录\n\n"
                f"**可能原因:**\n"
                f"• 该设备名在指定时间内未被使用\n"
                f"• 关键词不匹配任何现有的设备名\n"
                f"• 用户活动记录已过期"
            )
            await editMessage(processing_msg, no_data_text)
            return

        # 构建设备名审计报告
        report_text = "📊 **设备名审计报告**\n\n"
        report_text += f"**🔍 搜索关键词:** `{device_keyword}`\n"
        report_text += f"**📅 查询范围:** {days if days else '所有时间'}\n"
        report_text += f"**👥 发现用户:** {len(result)} 个\n\n"
        
        # 按活动时间排序
        sorted_users = sorted(result, key=lambda x: x['LastActivity'], reverse=True)
        
        report_text += "**📋 用户详情:**\n"
        report_text += "=" * 40 + "\n"
        
        # 统计不同的设备名
        unique_device_names = set()
        
        for i, user_info in enumerate(sorted_users, 1):
            # 格式化最后活动时间
            try:
                last_activity = datetime.fromisoformat(user_info['LastActivity'].replace('Z', '+00:00'))
                formatted_time = last_activity.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError, KeyError):
                formatted_time = user_info['LastActivity']
            
            device_name_value = user_info.get('DeviceName', '未知')
            unique_device_names.add(device_name_value)
            
            report_text += f"**{i}. {user_info['Username']}**\n"
            report_text += f"   • 用户ID: `{user_info['UserId']}`\n"
            report_text += f"   • 设备名: `{user_info['DeviceName']}`\n"
            report_text += f"   • 客户端: `{user_info['ClientName']}`\n"
            report_text += f"   • IP地址: `{user_info['RemoteAddress']}`\n"
            report_text += f"   • 最后活动: `{formatted_time}`\n"
            report_text += f"   • 活动次数: `{user_info['ActivityCount']}`\n\n"

        # 添加统计信息
        report_text += "**📊 统计摘要:**\n"
        report_text += f"• 匹配用户数: `{len(result)}`\n"
        report_text += f"• 不同设备名数: `{len(unique_device_names)}`\n\n"
        
        # 显示所有不同的设备名
        if len(unique_device_names) <= 10:  # 如果数量不多，显示所有
            report_text += "**🔍 发现的设备名:**\n"
            for i, device_name in enumerate(sorted(unique_device_names), 1):
                truncated_device_name = device_name[:80] + '...' if len(device_name) > 80 else device_name
                report_text += f"{i}. `{truncated_device_name}`\n"
            report_text += "\n"
        
        # 添加安全提醒
        if len(result) > 10:
            report_text += "⚠️ **注意:**\n"
            report_text += f"发现 {len(result)} 个用户使用包含 '{device_keyword}' 的设备，请注意是否存在异常使用模式。\n\n"
        
        report_text += f"**📊 审计完成时间:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
        report_texts = split_long_message(report_text)
        for report_text_part in report_texts:
            try:
                await bot.send_message(message.chat.id, report_text_part)
            except FloodWait as f:
                LOGGER.warning(str(f))
                await asyncio.sleep(f.value * 1.2)
        LOGGER.info(f"管理员 {message.from_user.id} 执行了设备名审计: {device_keyword}")

    except Exception as e:
        error_text = f"❌ **设备名审计异常**\n\n**错误信息:** {str(e)}"
        await sendMessage(message, error_text)
        LOGGER.error(f"设备名审计命令异常: {str(e)}")


@bot.on_message(filters.command("auditclient") & admins_on_filter)
async def audit_client_name_command(_, message: Message):
    """
    auditclient 命令 - 根据客户端名审计用户
    用法: /auditclient <客户端名关键词> [天数]
    示例: /auditclient Chrome 30
    """
    try:
        # 解析命令参数
        args = message.text.split(None, 2)  # 使用 None 和限制分割次数，支持包含空格的客户端名
        if len(args) < 2:
            help_text = (
                "**🔍 客户端名审计命令使用说明**\n\n"
                "**用法:** `/auditclient <客户端名关键词> [天数]`\n\n"
                "**参数说明:**\n"
                "• `客户端名关键词` - 要搜索的客户端名关键词（必需）\n"
                "• `天数` - 查询天数范围，默认查询所有时间（可选）\n\n"
                "**示例:**\n"
                "• `/auditclient Chrome` - 查询使用 Chrome 浏览器的用户\n"
                "• `/auditclient Android 7` - 查询最近7天使用 Android 客户端的用户\n"
                "• `/auditclient Emby` - 查询使用 Emby 客户端的用户\n"
                "• `/auditclient Web` - 查询使用 Web 客户端的用户\n\n"
                "**功能:**\n"
                "• 根据客户端名查找相关用户\n"
                "• 分析客户端使用情况\n"
                "• 检测异常或可疑的客户端"
            )
            await sendMessage(message, help_text)
            return

        client_keyword = args[1]
        days = None
        # 解析天数参数
        if len(args) >= 3:
            try:
                days = int(args[2])
                if days <= 0 or days > 3650:
                    await sendMessage(message, "❌ 天数参数必须在 1-3650 之间")
                    return
            except ValueError:
                await sendMessage(message, "❌ 天数参数必须是有效的数字")
                return

        # 发送处理中消息
        processing_msg = await message.reply(f"🔍 正在审计包含 `{client_keyword}` 的客户端名 {days if days else '所有时间'} 的使用情况...")

        # 调用客户端名审计 API
        success, result = await emby.get_users_by_client_name(client_keyword, days)
        
        if not success:
            error_text = f"❌ **客户端名审计失败**\n\n**错误信息:** {result}"
            await editMessage(processing_msg, error_text)
            return

        if not result:
            no_data_text = (
                f"📊 **客户端名审计结果**\n\n"
                f"**关键词:** `{client_keyword}`\n"
                f"**查询范围:** {days if days else '所有时间'}\n"
                f"**结果:** 未找到任何匹配的用户活动记录\n\n"
                f"**可能原因:**\n"
                f"• 该客户端名在指定时间内未被使用\n"
                f"• 关键词不匹配任何现有的客户端名\n"
                f"• 用户活动记录已过期"
            )
            await editMessage(processing_msg, no_data_text)
            return

        # 构建客户端名审计报告
        report_text = "📊 **客户端名审计报告**\n\n"
        report_text += f"**🔍 搜索关键词:** `{client_keyword}`\n"
        report_text += f"**📅 查询范围:** {days if days else '所有时间'}\n"
        report_text += f"**👥 发现用户:** {len(result)} 个\n\n"
        
        # 按活动时间排序
        sorted_users = sorted(result, key=lambda x: x['LastActivity'], reverse=True)
        
        report_text += "**📋 用户详情:**\n"
        report_text += "=" * 40 + "\n"
        
        # 统计不同的客户端名
        unique_client_names = set()
        
        for i, user_info in enumerate(sorted_users, 1):
            # 格式化最后活动时间
            try:
                last_activity = datetime.fromisoformat(user_info['LastActivity'].replace('Z', '+00:00'))
                formatted_time = last_activity.strftime('%Y-%m-%d %H:%M:%S')
            except (ValueError, TypeError, KeyError):
                formatted_time = user_info['LastActivity']
            
            client_name_value = user_info.get('ClientName', '未知')
            unique_client_names.add(client_name_value)
            
            report_text += f"**{i}. {user_info['Username']}**\n"
            report_text += f"   • 用户ID: `{user_info['UserId']}`\n"
            report_text += f"   • 设备名: `{user_info['DeviceName']}`\n"
            report_text += f"   • 客户端: `{user_info['ClientName']}`\n"
            report_text += f"   • IP地址: `{user_info['RemoteAddress']}`\n"
            report_text += f"   • 最后活动: `{formatted_time}`\n"
            report_text += f"   • 活动次数: `{user_info['ActivityCount']}`\n\n"

        # 添加统计信息
        report_text += "**📊 统计摘要:**\n"
        report_text += f"• 匹配用户数: `{len(result)}`\n"
        report_text += f"• 不同客户端名数: `{len(unique_client_names)}`\n\n"
        
        # 显示所有不同的客户端名
        if len(unique_client_names) <= 10:  # 如果数量不多，显示所有
            report_text += "**🔍 发现的客户端名:**\n"
            for i, client_name in enumerate(sorted(unique_client_names), 1):
                truncated_client_name = client_name[:80] + '...' if len(client_name) > 80 else client_name
                report_text += f"{i}. `{truncated_client_name}`\n"
            report_text += "\n"
        
        # 添加安全提醒
        if len(result) > 10:
            report_text += "⚠️ **注意:**\n"
            report_text += f"发现 {len(result)} 个用户使用包含 '{client_keyword}' 的客户端，请注意是否存在异常使用模式。\n\n"
        
        report_text += f"**📊 审计完成时间:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"
        report_texts = split_long_message(report_text)
        for report_text_part in report_texts:
            try:
                await bot.send_message(message.chat.id, report_text_part)
            except FloodWait as f:
                LOGGER.warning(str(f))
                await asyncio.sleep(f.value * 1.2)
        LOGGER.info(f"管理员 {message.from_user.id} 执行了客户端名审计: {client_keyword}")

    except Exception as e:
        error_text = f"❌ **客户端名审计异常**\n\n**错误信息:** {str(e)}"
        await sendMessage(message, error_text)
        LOGGER.error(f"客户端名审计命令异常: {str(e)}")