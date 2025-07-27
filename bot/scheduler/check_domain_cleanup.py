"""
定时检测用户等级，删除不符合条件账户的专属域名
"""
from datetime import datetime
from sqlalchemy import and_
from asyncio import sleep
from pyrogram.errors import FloodWait

from bot import bot, group, LOGGER, cloudflare
from bot.func_helper.cloudflare_api import delete_user_domain
from bot.sql_helper.sql_emby import Emby, get_all_emby


async def check_domain_cleanup(send_report=False, chat_id=None):
    """
    检测用户等级，删除不符合条件账户的专属域名
    
    删除规则：
    1. 等级为 'c' (已禁用) 的账户
    2. 等级为 'd' (未注册) 的账户
    3. 没有 embyid 的账户
    
    :param send_report: 是否发送清理报告，默认 False（定时任务不发送）
    :param chat_id: 报告发送的目标聊天ID，如果为None则发送到管理群组
    """
    if not cloudflare.status:
        LOGGER.info('【域名清理】- Cloudflare 功能未启用，跳过域名清理')
        return
    
    LOGGER.info('【域名清理】- 开始检测需要清理域名的账户')
    
    # 获取所有需要清理域名的用户（等级为 c 或 d，或者没有 embyid）
    users_to_cleanup = get_all_emby(
        and_(
            Emby.name.isnot(None),  # 有用户名的账户才可能有域名
            (Emby.lv.in_(['c', 'd']) | Emby.embyid.is_(None))  # 等级为 c/d 或没有 embyid
        )
    )
    
    if not users_to_cleanup:
        LOGGER.info('【域名清理】- 没有找到需要清理域名的账户')
        return
    
    # 详细记录需要清理的用户信息
    LOGGER.info(f'【域名清理】- 找到 {len(users_to_cleanup)} 个需要清理域名的账户:')
    for user in users_to_cleanup:
        if user.name and user.pwd2:
            reason = "已禁用" if user.lv == 'c' else "未注册" if user.lv == 'd' else "无Emby账户"
            domain_prefix = f"{user.name}-{user.pwd2}"
            LOGGER.info(f'【域名清理】- 待清理: 用户 {user.name} (TG:{user.tg}) | 等级:{user.lv} | 状态:{reason} | 域名前缀:{domain_prefix}')
    
    cleanup_count = 0
    error_count = 0
    
    for user in users_to_cleanup:
        if not user.name or not user.pwd2:
            continue
            
        try:
            # 根据用户名+安全码构建域名前缀（与创建时保持一致）
            domain_prefix = f"{user.name}-{user.pwd2}"
            # 删除用户的专属域名
            success, error_msg = await delete_user_domain(domain_prefix)
            
            if success:
                cleanup_count += 1
                
                # 记录清理结果
                reason = "已禁用" if user.lv == 'c' else "未注册" if user.lv == 'd' else "无Emby账户"
                log_msg = f'【域名清理】- 用户 {user.name} (TG:{user.tg}) 状态: {reason}，已删除域名'
                LOGGER.info(log_msg)
            else:
                if error_msg and "未找到域名记录" not in error_msg:
                    error_count += 1
                    LOGGER.warning(f'【域名清理】- 删除用户 {user.name} 的域名失败: {error_msg}')
                else:
                    # 域名记录不存在，不算错误
                    LOGGER.info(f'【域名清理】- 用户 {user.name} 的域名记录不存在，跳过')
                    
        except Exception as e:
            error_count += 1
            LOGGER.error(f'【域名清理】- 处理用户 {user.name} 时发生异常: {e}')
            
        # 避免频繁调用API
        await sleep(1)
    
        # 总结报告
    summary_msg = f'【域名清理】- 任务完成，成功清理 {cleanup_count} 个域名'
    if error_count > 0:
        summary_msg += f'，失败 {error_count} 个'
    summary_msg += f'，执行时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
    LOGGER.info(summary_msg)