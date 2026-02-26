from datetime import datetime, timedelta

from pyrogram import filters

from bot import bot, prefixes, LOGGER, partition_libs
from bot.func_helper.emby import emby
from bot.func_helper.filters import user_in_group_on_filter
from bot.func_helper.msg_utils import sendMessage, deleteMessage
from bot.sql_helper.sql_emby import sql_get_emby
from bot.sql_helper.sql_partition import (
    sql_consume_partition_code,
    sql_get_partition_code,
    sql_upsert_partition_grant,
)


@bot.on_message(filters.command('partcode', prefixes) & user_in_group_on_filter)
async def redeem_partition_code(_, msg):
    try:
        code = msg.command[1].strip()
    except (IndexError, AttributeError):
        return await sendMessage(msg, "🔔 使用格式：/partcode 分区码", timer=60)

    record = sql_get_partition_code(code)
    now = datetime.now()
    if not record:
        return await sendMessage(msg, "❌ 分区码无效。", timer=60)
    if record.uses_left <= 0:
        return await sendMessage(msg, "❌ 分区码已用完。", timer=60)
    if record.expires_at and record.expires_at < now:
        return await sendMessage(msg, "❌ 分区码已过期。", timer=60)

    libs = partition_libs.get(record.partition, []) if partition_libs else []
    if not libs:
        LOGGER.warning("分区码对应分区未配置库: %s", record.partition)
        return await sendMessage(msg, "⚠️ 分区未配置库，请联系管理员。", timer=60)

    emby_row = sql_get_emby(tg=msg.from_user.id)
    if not emby_row or not emby_row.embyid:
        return await sendMessage(msg, "⚠️ 未找到您的 Emby 账户，请先完成注册绑定。", timer=60)

    expires_at = now + timedelta(hours=record.duration_hours)

    if not sql_consume_partition_code(code):
        return await sendMessage(msg, "❌ 分区码已无可用次数。", timer=60)

    ok = sql_upsert_partition_grant(
        tg=msg.from_user.id,
        embyid=emby_row.embyid,
        partition=record.partition,
        expires_at=expires_at,
        code=record.code,
    )
    if not ok:
        return await sendMessage(msg, "❌ 更新授权失败，请稍后重试。", timer=60)

    await emby.show_folders_by_names(emby_row.embyid, libs)
    await deleteMessage(msg)
    return await sendMessage(
        msg,
        f"✅ 已激活分区 {record.partition}\n可访问至：{expires_at:%Y-%m-%d %H:%M:%S}",
        timer=120,
    )
