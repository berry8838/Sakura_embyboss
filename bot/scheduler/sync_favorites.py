from bot import LOGGER
from bot.sql_helper.sql_favorites import sql_add_favorites, sql_clear_favorites
from bot.sql_helper.sql_emby import get_all_emby, Emby
from bot.func_helper.emby import emby


async def sync_favorites():
    """
    同步所有用户的Emby收藏记录到数据库
    """
    LOGGER.info("开始同步用户Emby收藏记录...")
    try:
        # 获取所有Emby用户
        users = get_all_emby(Emby.embyid is not None)
        if not users:
            LOGGER.warning("没有找到Emby用户")
            return

        for user in users:
            # 获取用户的收藏列表
            favorites = await emby.get_favorite_items(emby_id=user.embyid)
            if not favorites:
                continue
            #  清除数据库中该用户的收藏记录
            sql_clear_favorites(user.embyid)
            # 遍历收藏项目并添加到数据库
            for item in favorites.get("Items", []):
                item_id = item.get("Id")
                if not item_id:
                    continue

                # 获取项目名称
                item_name = item.get("Name", "")
                if not item_name:
                    item_name = await emby.item_id_name(emby_id=user.embyid, item_id=item_id) or "未知"

                # 添加到数据库
                sql_add_favorites(
                    embyid=user.embyid,
                    embyname=user.name,
                    item_id=item_id,
                    item_name=item_name,
                )

        LOGGER.info("Emby收藏记录同步完成")

    except Exception as e:
        LOGGER.error(f"同步Emby收藏记录时出错: {str(e)}")
