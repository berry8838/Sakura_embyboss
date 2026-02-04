from fastapi import APIRouter, Request, HTTPException
from bot.sql_helper.sql_emby import Emby, sql_get_emby, sql_update_emby
from bot import LOGGER, bot, config
from bot.func_helper.emby import emby
import json
import re
from typing import List, Optional, Tuple
from datetime import datetime
from urllib.parse import urlparse

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


async def get_blocked_clients() -> List[str]:
    """获取被拦截的客户端模式列表"""
    try:
        # 从配置中获取，如果没有则使用默认值
        blocked_agents = getattr(config, "blocked_clients", DEFAULT_BLOCKED_CLIENTS)
        return blocked_agents if blocked_agents else DEFAULT_BLOCKED_CLIENTS
    except Exception as e:
        LOGGER.error(f"获取被拦截客户端列表失败: {str(e)}")
        return DEFAULT_BLOCKED_CLIENTS


async def is_client_blocked(client: str) -> bool:
    """检查客户端是否被拦截"""
    if not client:
        return False

    blocked_clients = await get_blocked_clients()
    client_lower = client.lower()

    for pattern in blocked_clients:
        try:
            if re.search(pattern.lower(), client_lower):
                return True
        except re.error as e:
            LOGGER.error(f"正则表达式错误: {pattern} - {str(e)}")
            continue

    return False


async def log_blocked_request(
    user_id: str = None,
    user_name: str = None,
    session_id: str = None,
    client_name: str = None,
    tg_id: int = None,
    block_success: bool = False,
):
    """记录被拦截的请求"""
    try:
        action = "拦截可疑请求"
        block_action = "封禁用户" if block_success else "不封禁用户"
        log_message = (
            f"🚫 {action}\n"
            f"用户ID: {user_id or 'Unknown'}\n"
            f"用户名称: {user_name or 'Unknown'}\n"
            f"会话ID: {session_id or 'Unknown'}\n"
            f"客户端: {client_name or 'Unknown'}\n"
            f"TG ID: {tg_id or 'Unknown'}\n"
            f"是否封禁用户: {block_action}\n"
            f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        LOGGER.warning(log_message)

        # 如果配置了管理员群组，发送通知
        if hasattr(config, "group") and config.group:
            try:
                await bot.send_message(chat_id=config.group[0], text=log_message)
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


# ==================== 线路权限控制 ====================

def extract_host_port(url: str) -> Tuple[Optional[str], Optional[int]]:
    """从URL中提取主机名和端口"""
    try:
        if not url:
            return None, None
        # 如果没有协议前缀，添加默认的
        if not url.startswith(('http://', 'https://')):
            url = f"http://{url}"
        parsed = urlparse(url)
        host = parsed.hostname
        port = parsed.port
        return host, port
    except Exception as e:
        LOGGER.error(f"解析URL失败: {url} - {str(e)}")
        return None, None


def normalize_line_url(url: str) -> str:
    """标准化线路URL，用于比较"""
    if not url:
        return ""
    # 移除协议前缀和尾部斜杠
    url = url.lower().strip()
    url = re.sub(r'^https?://', '', url)
    url = url.rstrip('/')
    return url


def is_whitelist_line(session_server_address: str) -> bool:
    """
    检查会话使用的是否是白名单线路
    :param session_server_address: 会话中的服务器地址
    :return: True 如果是白名单线路
    """
    whitelist_line = getattr(config, "emby_whitelist_line", None)
    if not whitelist_line:
        return False
    
    # 标准化比较
    session_normalized = normalize_line_url(session_server_address)
    whitelist_normalized = normalize_line_url(whitelist_line)
    
    if not session_normalized or not whitelist_normalized:
        return False
    
    # 检查是否匹配白名单线路
    return whitelist_normalized in session_normalized or session_normalized in whitelist_normalized


def is_user_whitelisted(user_details: Emby) -> bool:
    """
    检查用户是否是白名单用户
    :param user_details: 用户详情
    :return: True 如果是白名单用户 (lv='a')
    """
    if not user_details:
        return False
    return user_details.lv == 'a'


async def get_session_server_address(session_id: str) -> Optional[str]:
    """
    通过 Emby API 获取会话的服务器地址
    :param session_id: 会话ID
    :return: 服务器地址或None
    """
    try:
        # 调用 Emby API 获取所有会话
        result = await emby._request('GET', '/emby/Sessions')
        if not result.success or not result.data:
            LOGGER.error(f"获取会话信息失败: {result.error}")
            return None
        
        # 查找指定的会话
        for session in result.data:
            if session.get("Id") == session_id:
                # 记录完整的会话信息用于调试
                LOGGER.debug(f"Session详情: {json.dumps(session, ensure_ascii=False, indent=2)}")
                
                # Emby 会话中没有直接的 ServerAddress
                # 实际的服务器地址需要从 webhook 数据中获取
                return None
        
        return None
    except Exception as e:
        LOGGER.error(f"获取会话服务器地址异常: {str(e)}")
        return None


async def log_line_violation(
    user_id: str = None,
    user_name: str = None,
    session_id: str = None,
    client_name: str = None,
    device_name: str = None,
    remote_endpoint: str = None,
    server_address: str = None,
    tg_id: int = None,
    user_lv: str = None,
    action_taken: str = None,
):
    """记录线路权限违规"""
    try:
        lv_display = {'a': '白名单', 'b': '普通用户', 'c': '封禁用户', 'd': '未注册'}.get(user_lv, '未知')
        
        log_message = (
            f"⚠️ 线路权限违规\n"
            f"━━━━━━━━━━━━━━━\n"
            f"👤 用户: {user_name or 'Unknown'}\n"
            f"🆔 Emby ID: {user_id or 'Unknown'}\n"
            f"📱 TG ID: {tg_id or 'Unknown'}\n"
            f"🏷️ 用户等级: {lv_display}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🌐 使用线路: {server_address or 'Unknown'}\n"
            f"📍 远程IP: {remote_endpoint or 'Unknown'}\n"
            f"📺 客户端: {client_name or 'Unknown'}\n"
            f"💻 设备: {device_name or 'Unknown'}\n"
            f"🔑 会话ID: {session_id or 'Unknown'}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🚨 处理措施: {action_taken or '无'}\n"
            f"⏰ 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        LOGGER.warning(log_message)

        # 发送群组通知
        if hasattr(config, "group") and config.group:
            try:
                await bot.send_message(chat_id=config.group[0], text=log_message)
            except Exception as e:
                LOGGER.error(f"发送线路违规通知失败: {str(e)}")

    except Exception as e:
        LOGGER.error(f"记录线路违规失败: {str(e)}")


async def handle_line_violation(
    emby_id: str,
    user_name: str,
    session_id: str,
    client_name: str,
    device_name: str,
    remote_endpoint: str,
    server_address: str,
    user_details: Emby,
) -> dict:
    """
    处理线路权限违规
    :return: 处理结果字典
    """
    action_taken_list = []
    block_success = False
    terminate_success = False
    
    # 获取配置的处理策略
    terminate_session_enabled = getattr(config, "line_filter_terminate_session", True)
    block_user_enabled = getattr(config, "line_filter_block_user", False)
    
    # 1. 终止会话
    if terminate_session_enabled:
        reason = "您使用的线路与您的账户等级不匹配，请使用正确的线路"
        terminate_success = await emby.terminate_session(session_id, reason)
        if terminate_success:
            action_taken_list.append("✅ 已终止会话")
            LOGGER.info(f"成功终止违规会话 {session_id}")
        else:
            action_taken_list.append("❌ 终止会话失败")
            LOGGER.error(f"终止违规会话失败 {session_id}")
    
    # 2. 封禁用户
    if block_user_enabled:
        block_success = await emby.emby_change_policy(emby_id=emby_id, disable=True)
        if block_success:
            # 更新数据库中的用户状态
            if user_details:
                sql_update_emby(Emby.tg == user_details.tg, lv="c")
            action_taken_list.append("✅ 已封禁用户")
            LOGGER.info(f"成功封禁违规用户 {emby_id}")
        else:
            action_taken_list.append("❌ 封禁用户失败")
            LOGGER.error(f"封禁违规用户失败 {emby_id}")
    
    action_taken = " | ".join(action_taken_list) if action_taken_list else "仅记录，未采取行动"
    
    # 记录违规并发送通知
    await log_line_violation(
        user_id=emby_id,
        user_name=user_name,
        session_id=session_id,
        client_name=client_name,
        device_name=device_name,
        remote_endpoint=remote_endpoint,
        server_address=server_address,
        tg_id=user_details.tg if user_details else None,
        user_lv=user_details.lv if user_details else None,
        action_taken=action_taken,
    )
    
    return {
        "terminate_success": terminate_success,
        "block_success": block_success,
        "action_taken": action_taken,
    }


async def check_line_permission(
    emby_id: str,
    user_name: str,
    session_id: str,
    client_name: str,
    device_name: str,
    remote_endpoint: str,
    server_address: str,
) -> Tuple[bool, Optional[dict]]:
    """
    检查用户是否有权限使用当前线路
    :return: (是否允许, 违规处理结果或None)
    """
    # 如果没有配置白名单线路，跳过检查
    whitelist_line = getattr(config, "emby_whitelist_line", None)
    if not whitelist_line:
        LOGGER.debug("未配置白名单线路，跳过线路权限检查")
        return True, None
    
    # 如果没有服务器地址信息，跳过检查
    if not server_address:
        LOGGER.debug("无法获取服务器地址，跳过线路权限检查")
        return True, None
    
    # 获取用户详情
    user_details = sql_get_emby(emby_id)
    
    # 检查是否使用白名单线路
    using_whitelist_line = is_whitelist_line(server_address)
    
    # 检查用户是否是白名单用户
    is_whitelist_user = is_user_whitelisted(user_details)
    
    LOGGER.debug(
        f"线路权限检查: user={user_name}, emby_id={emby_id}, "
        f"server={server_address}, using_whitelist={using_whitelist_line}, "
        f"is_whitelist_user={is_whitelist_user}"
    )
    
    # 白名单用户可以使用任何线路
    if is_whitelist_user:
        return True, None
    
    # 普通用户使用白名单线路 -> 违规
    if using_whitelist_line and not is_whitelist_user:
        LOGGER.warning(
            f"线路权限违规: 普通用户 {user_name}({emby_id}) 尝试使用白名单线路 {server_address}"
        )
        
        # 处理违规
        result = await handle_line_violation(
            emby_id=emby_id,
            user_name=user_name,
            session_id=session_id,
            client_name=client_name,
            device_name=device_name,
            remote_endpoint=remote_endpoint,
            server_address=server_address,
            user_details=user_details,
        )
        
        return False, result
    
    # 允许访问
    return True, None


@router.post("/webhook/client-filter")
async def handle_client_filter_webhook(request: Request):
    """处理Emby用户代理拦截webhook"""
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
        server_info = webhook_data.get("Server", {})
        
        user_name = user_info.get("Name", "")
        emby_id = user_info.get("Id", "")
        session_id = session_info.get("Id", "")
        client_name = session_info.get("Client", "")
        device_name = session_info.get("DeviceName", "")
        remote_endpoint = session_info.get("RemoteEndPoint", "")
        
        # 获取服务器地址信息（用于线路权限检查）
        # 优先从 Server 中获取，如果没有则尝试从请求头获取
        server_address = server_info.get("PublicAddress") or server_info.get("LocalAddress", "")
        
        # 尝试从请求头获取实际访问的地址
        x_forwarded_host = request.headers.get("X-Forwarded-Host", "")
        x_forwarded_proto = request.headers.get("X-Forwarded-Proto", "")
        host_header = request.headers.get("Host", "")
        
        # 构建完整的访问地址
        if x_forwarded_host:
            proto = x_forwarded_proto or "https"
            server_address = f"{proto}://{x_forwarded_host}"
        elif not server_address and host_header:
            server_address = f"http://{host_header}"
        
        LOGGER.debug(
            f"Webhook 数据: event={event}, user={user_name}, emby_id={emby_id}, "
            f"client={client_name}, device={device_name}, remote_ip={remote_endpoint}, "
            f"server_address={server_address}"
        )

        if not client_name:
            return {"status": "ignored", "message": "No Client info found"}

        # ==================== 1. 检查客户端是否被拦截 ====================
        is_blocked = await is_client_blocked(client_name)

        if is_blocked:
            # 根据配置决定是否终止会话
            if getattr(config, "client_filter_terminate_session", True):
                await terminate_blocked_session(session_id, client_name)
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
                    "user_details": user_details,
                    "event": event,
                    "timestamp": datetime.now().isoformat(),
                },
            }

        # ==================== 2. 检查线路权限 ====================
        # 仅在登录和播放事件时检查线路权限
        if event in ["user.authenticated", "playback.start", "playback.progress", "session.start"]:
            line_allowed, line_result = await check_line_permission(
                emby_id=emby_id,
                user_name=user_name,
                session_id=session_id,
                client_name=client_name,
                device_name=device_name,
                remote_endpoint=remote_endpoint,
                server_address=server_address,
            )
            
            if not line_allowed:
                return {
                    "status": "line_blocked",
                    "message": "User not allowed to use this line",
                    "data": {
                        "user_id": emby_id,
                        "user_name": user_name,
                        "session_id": session_id,
                        "client_name": client_name,
                        "device_name": device_name,
                        "remote_endpoint": remote_endpoint,
                        "server_address": server_address,
                        "event": event,
                        "action_result": line_result,
                        "timestamp": datetime.now().isoformat(),
                    },
                }

        return {
            "status": "allowed",
            "message": "Client and line allowed",
            "data": {
                "client": client_name,
                "user_id": emby_id,
                "user_name": user_name,
                "device_name": device_name,
                "remote_endpoint": remote_endpoint,
                "server_address": server_address,
                "event": event,
            },
        }

    except Exception as e:
        LOGGER.error(f"处理Client拦截webhook失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Webhook处理失败: {str(e)}")
