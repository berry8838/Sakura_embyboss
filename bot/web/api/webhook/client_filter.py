from fastapi import APIRouter, Request, HTTPException
from bot.sql_helper.sql_emby import Emby, sql_get_emby, sql_update_emby
from bot import LOGGER, bot, config
from bot.func_helper.emby import emby
import json
import re
from typing import List
from datetime import datetime

router = APIRouter()

# 默认的被拦截的客户端模式列表
DEFAULT_BLOCKED_CLIENTS = [
    r".*curl.*",
    r".*wget.*",
    r".*python.*",
    r".*spider.*",
    r".*crawler.*",
    r".*scraper.*",
    r".*downloader.*",
    r".*aria2.*",
    r".*youtube-dl.*",
    r".*yt-dlp.*",
    r".*ffmpeg.*",
    r".*vlc.*",
]


def get_client_filter_mode() -> str:
    """获取客户端过滤模式"""
    mode = getattr(config, "client_filter_mode", "blacklist")
    mode = str(mode).lower()
    if mode not in ("blacklist", "whitelist"):
        LOGGER.error(f"客户端过滤模式错误: {mode}，已使用黑名单模式")
        return "blacklist"
    return mode


async def get_blocked_clients() -> List[str]:
    """获取被拦截的客户端模式列表"""
    try:
        # 从配置中获取，如果没有则使用默认值
        blocked_agents = getattr(config, "blocked_clients", DEFAULT_BLOCKED_CLIENTS)
        return blocked_agents if blocked_agents else DEFAULT_BLOCKED_CLIENTS
    except Exception as e:
        LOGGER.error(f"获取被拦截客户端列表失败: {str(e)}")
        return DEFAULT_BLOCKED_CLIENTS


async def get_allowed_clients() -> List[str]:
    """获取被允许的客户端模式列表"""
    try:
        allowed_agents = getattr(config, "allowed_clients", None)
        return allowed_agents if allowed_agents else []
    except Exception as e:
        LOGGER.error(f"获取被允许客户端列表失败: {str(e)}")
        return []


def match_client_patterns(client: str, patterns: List[str]) -> bool:
    """检查客户端是否匹配任意正则模式"""
    client_lower = client.lower()

    for pattern in patterns:
        try:
            if re.search(pattern.lower(), client_lower):
                return True
        except re.error as e:
            LOGGER.error(f"正则表达式错误: {pattern} - {str(e)}")
            continue

    return False


async def is_client_blocked(client: str) -> bool:
    """检查客户端是否被拦截"""
    if not client:
        return False

    mode = get_client_filter_mode()

    if mode == "whitelist":
        allowed_clients = await get_allowed_clients()
        return not match_client_patterns(client, allowed_clients)

    blocked_clients = await get_blocked_clients()
    return match_client_patterns(client, blocked_clients)


async def log_blocked_request(
    user_id: str = None,
    user_name: str = None,
    session_id: str = None,
    client_name: str = None,
    tg_id: int = None,
    user_lv: str = None,
    terminate_success: bool = False,
    block_success: bool = False,
):
    """记录被拦截的请求"""
    try:
        lv_display = {'a': '白名单', 'b': '普通用户', 'c': '封禁用户', 'd': '未注册'}.get(user_lv, '未知')
        action_list = []
        if terminate_success:
            action_list.append("✅ 已终止会话")
        elif terminate_success is False and session_id:
            action_list.append("❌ 终止会话失败")
        if block_success:
            action_list.append("✅ 已封禁用户")
        action = " | ".join(action_list) if action_list else "仅记录，未采取行动"
        log_message = (
            f"🚫 拦截非法客户端\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 用户: {user_name or 'Unknown'}\n"
            f"🆔 Emby ID: {user_id or 'Unknown'}\n"
            f"📱 TG ID: {f'[{tg_id}](tg://user?id={tg_id})' if tg_id else 'Unknown'}\n"
            f"🏷️ 用户等级: {lv_display}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📺 客户端: {client_name or 'Unknown'}\n"
            f"🔑 会话ID: {session_id or 'Unknown'}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚨 处理措施: {action}\n"
            f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        LOGGER.warning(log_message)

        # 如果配置了管理员群组，发送通知并转发给用户
        if hasattr(config, "group") and config.group:
            try:
                out = await bot.send_message(chat_id=config.group[0], text=log_message)
                if tg_id:
                    await out.forward(tg_id)
            except Exception as e:
                LOGGER.error(f"发送拦截通知失败: {str(e)}")

    except Exception as e:
        LOGGER.error(f"记录拦截请求失败: {str(e)}")


async def terminate_blocked_session(session_id: str, client_name: str) -> bool:
    """终止被拦截的会话"""
    try:
        reason = f"检测到可疑客户端: {client_name}"
        success = await emby.terminate_session(session_id, reason)
        if success:
            LOGGER.info(f"成功终止可疑会话 {session_id}")
        else:
            LOGGER.error(f"终止会话失败 {session_id}")
        return success
    except Exception as e:
        LOGGER.error(f"终止会话异常 {session_id}: {str(e)}")
        return False


@router.post("/webhook/client-filter")
async def handle_client_filter_webhook(request: Request):
    """处理Emby用户代理拦截webhook"""

    # 检查客户端过滤是否开启
    if not getattr(config, "client_filter_enabled", False):
        return {"status": "skipped", "message": "Client filter disabled"}
    try:
        # 检查Content-Type
        content_type = request.headers.get("content-type", "").lower()

        if "application/json" in content_type:
            # 处理JSON格式
            webhook_data = await request.json()
        else:
            # 处理form-data格式
            form_data = await request.form()
            form = dict(form_data)
            webhook_data = json.loads(form["data"]) if "data" in form else None

        if not webhook_data:
            return {"status": "error", "message": "No data received"}

        # 获取事件类型
        event = webhook_data.get("Event", "")

        # 只处理播放相关事件
        if event not in [
            "user.authenticated",
            "user.authenticationfailed",
            "playback.start",
            "playback.progress",
            "playback.stop",
            "session.start",
        ]:
            return {
                "status": "ignored",
                "message": "Not listen event",
                "event": event,
            }

        # 获取会话信息
        session_info = webhook_data.get("Session", {})
        user_info = webhook_data.get("User", {})
        user_name = user_info.get("Name", "")
        emby_id = user_info.get("Id", "")
        session_id = session_info.get("Id", "")
        client_name = session_info.get("Client", "")

        if not client_name:
            return {"status": "ignored", "message": "No Client info found"}

        # 检查Client是否被拦截
        is_blocked = await is_client_blocked(client_name)
        filter_mode = get_client_filter_mode()

        if is_blocked:
            terminate_success = False
            # 根据配置决定是否终止会话
            if getattr(config, "client_filter_terminate_session", True):
                terminate_success = await terminate_blocked_session(session_id, client_name)
            block_success = False

            user_details = sql_get_emby(emby_id)
            if getattr(config, "client_filter_block_user", False):
                block_success = await emby.emby_change_policy(emby_id=emby_id, disable=True)
                if block_success:
                    if user_details:
                        sql_update_emby(Emby.tg == user_details.tg, lv="c")

            # 记录拦截信息
            await log_blocked_request(
                user_id=emby_id,
                user_name=user_name,
                session_id=session_id,
                client_name=client_name,
                tg_id=user_details.tg if user_details else None,
                user_lv=user_details.lv if user_details else None,
                terminate_success=terminate_success,
                block_success=block_success,
            )

            return {
                "status": "blocked",
                "message": "Client blocked",
                "data": {
                    "user_id": emby_id,
                    "user_name": user_name,
                    "session_id": session_id,
                    "client_name": client_name,
                    "user_details": {
                        "tg": user_details.tg,
                        "embyid": user_details.embyid,
                        "name": user_details.name,
                        "lv": user_details.lv,
                    } if user_details else None,
                    "event": event,
                    "filter_mode": filter_mode,
                    "timestamp": datetime.now().isoformat(),
                },
            }

        return {
            "status": "allowed",
            "message": "Client allowed",
            "data": {
                "client": client_name,
                "user_id": emby_id,
                "event": event,
                "filter_mode": filter_mode,
            },
        }

    except Exception as e:
        LOGGER.error(f"处理Client拦截webhook失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook处理失败: {str(e)}")
