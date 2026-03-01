from datetime import datetime


from bot import LOGGER, partition_libs
from bot.func_helper.emby import emby
from bot.sql_helper.sql_emby import sql_get_emby
from bot.sql_helper.sql_partition import (
    sql_get_partition_code,
    sql_redeem_partition_code_atomic,
)


async def _redeem_partition_code(code: str, tg_id: int):
    now = datetime.now()

    record = sql_get_partition_code(code)
    if not record:
        return False, "❌ 分区码无效。"

    libs = partition_libs.get(record.partition, []) if partition_libs else []
    if not libs:
        LOGGER.warning("分区码对应分区未配置库: %s", record.partition)
        return False, "⚠️ 分区未配置库，请联系管理员。"

    emby_row = sql_get_emby(tg=tg_id)
    if not emby_row or not emby_row.embyid:
        return False, "⚠️ 未找到您的 Emby 账户，请先完成注册绑定。"

    ok, partition, expires_at = sql_redeem_partition_code_atomic(
        code=code,
        tg=tg_id,
        embyid=emby_row.embyid,
        now=now,
    )
    if not ok or not partition or not expires_at:
        return False, "❌ 分区码无效或已被使用。"

    await emby.show_folders_by_names(emby_row.embyid, libs)
    libs_text = "、".join(libs)
    return (
        True,
        f"✅ 已激活分区 {partition}\n"
        f"已激活媒体库：{libs_text}\n"
        f"可访问至：{expires_at:%Y-%m-%d %H:%M:%S}",
    )
