from datetime import datetime, timedelta


from bot import LOGGER, partition_libs
from bot.func_helper.emby import emby
from bot.sql_helper.sql_emby import sql_get_emby
from bot.sql_helper.sql_partition import (
    sql_delete_partition_code,
    sql_get_partition_code,
    sql_get_active_grants_by_user,
    sql_upsert_partition_grant,
)


async def _redeem_partition_code(code: str, tg_id: int):
    now = datetime.now()

    record = sql_get_partition_code(code)
    if not record:
        return False, "❌ 分区码无效。"
    if record.expires_at and record.expires_at < now:
        return False, "❌ 分区码已过期。"

    libs = partition_libs.get(record.partition, []) if partition_libs else []
    if not libs:
        LOGGER.warning("分区码对应分区未配置库: %s", record.partition)
        return False, "⚠️ 分区未配置库，请联系管理员。"

    emby_row = sql_get_emby(tg=tg_id)
    if not emby_row or not emby_row.embyid:
        return False, "⚠️ 未找到您的 Emby 账户，请先完成注册绑定。"

    # 若已有同分区未过期授权，则基于原到期时间累加；否则从现在起算
    active_grants = sql_get_active_grants_by_user(tg_id, now)
    same = next((g for g in active_grants if g.partition == record.partition), None)
    start_from = same.expires_at if same and same.expires_at > now else now
    expires_at = start_from + timedelta(days=record.duration_days)

    if not sql_delete_partition_code(code):
        return False, "❌ 分区码无效或已被使用。"

    ok = sql_upsert_partition_grant(
        tg=tg_id,
        embyid=emby_row.embyid,
        partition=record.partition,
        expires_at=expires_at,
        code=record.code,
    )
    if not ok:
        return False, "❌ 更新授权失败，请稍后重试。"

    await emby.show_folders_by_names(emby_row.embyid, libs)
    return True, f"✅ 已激活分区 {record.partition}\n可访问至：{expires_at:%Y-%m-%d %H:%M:%S}"
