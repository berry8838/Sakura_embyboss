from collections import defaultdict
from datetime import datetime
from typing import List, Set

from bot import partition_libs
from bot.func_helper.emby import emby
from bot.sql_helper.sql_emby import sql_get_emby
from bot.sql_helper.sql_partition import (
    sql_get_active_grants_for_users,
    sql_get_expired_grants,
    sql_mark_grants_expired,
)


async def check_partition_access():
    """
    定时检查分区授权是否到期，过期则收回对应库的访问权限。
    """
    now = datetime.now()
    if not partition_libs:
        return

    expired = sql_get_expired_grants(now)
    if not expired:
        return

    by_user = defaultdict(list)
    for grant in expired:
        by_user[grant.tg].append(grant)

    active_map = sql_get_active_grants_for_users(list(by_user.keys()), now)

    processed_ids: List[int] = []

    for tg_id, grants in by_user.items():
        emby_row = sql_get_emby(tg=tg_id)
        if not emby_row or not emby_row.embyid:
            processed_ids.extend([g.id for g in grants])
            continue

        # 当前仍然有效的分区集合
        active_parts = {g.partition for g in active_map.get(tg_id, [])}
        keep_libs: Set[str] = set()
        for part in active_parts:
            keep_libs.update(partition_libs.get(part, []))

        # 需要撤销的库集合
        revoke_libs: Set[str] = set()
        for grant in grants:
            revoke_libs.update(partition_libs.get(grant.partition, []))

        # 只隐藏那些不再被其它分区授权覆盖的库
        hide_targets = [lib for lib in revoke_libs if lib not in keep_libs]
        if hide_targets:
            await emby.hide_folders_by_names(emby_row.embyid, hide_targets)

        processed_ids.extend([g.id for g in grants])

    sql_mark_grants_expired(processed_ids)
