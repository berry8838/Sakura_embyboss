from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, UniqueConstraint
from bot.sql_helper import Base, engine, Session
from bot import LOGGER

class EmbyFavorites(Base):
    """Emby收藏记录表"""
    __tablename__ = 'emby_favorites'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    embyid = Column(String(64), nullable=False, comment="Emby用户ID")
    embyname = Column(String(128), nullable=False, comment="Emby用户名")
    item_id = Column(String(64), nullable=False, comment="Emby项目ID")
    item_name = Column(String(256), nullable=False, comment="项目名称")
    created_at = Column(DateTime, default=datetime.now, comment="收藏时间")
    
    # 创建联合唯一索引
    __table_args__ = (
        UniqueConstraint('embyid', 'item_id', name='uix_emby_item'),
    ) 

EmbyFavorites.__table__.create(bind=engine, checkfirst=True)

def sql_add_favorites(embyid: str, embyname: str, item_id: str, item_name: str, is_favorite: bool = True) -> bool:
    """
    添加或删除收藏记录
    以 emby_name 为主要判断依据，因为 emby_id 可能会变化
    
    Args:
        embyid: Emby用户ID
        embyname: Emby用户名
        item_id: 项目ID
        item_name: 项目名称
        is_favorite: True为收藏，False为取消收藏
    """
    try:
        with Session() as session:
            if is_favorite:
                # 收藏操作：以 embyname 为主要标识符（embyname 是唯一且不变的）
                
                # 查找该用户是否已收藏此项目
                existing_list = session.query(EmbyFavorites).filter(
                    EmbyFavorites.embyname == embyname,
                    EmbyFavorites.item_id == item_id
                ).all()
                
                if existing_list:
                    if len(existing_list) > 1:
                        # 如果存在多个重复记录，只保留第一个，删除其余的
                        LOGGER.warning(f"发现 {len(existing_list)} 个重复收藏记录: {embyname} -> {item_name}，清理重复记录")
                        keep_record = existing_list[0]  # 保留第一个记录
                        
                        # 删除其余重复记录
                        for duplicate in existing_list[1:]:
                            session.delete(duplicate)
                            LOGGER.info(f"删除重复收藏记录: {embyname} -> {item_name} (ID: {duplicate.id})")
                    else:
                        keep_record = existing_list[0]
                    
                    # 更新保留的记录
                    old_embyid = keep_record.embyid
                    keep_record.embyid = embyid
                    keep_record.item_name = item_name
                    keep_record.created_at = datetime.now()
                    
                    if old_embyid != embyid:
                        LOGGER.info(f"更新收藏记录: {embyname} -> {item_name} (EmbyID: {old_embyid} -> {embyid})")
                    else:
                        LOGGER.info(f"刷新收藏记录: {embyname} -> {item_name}")
                else:
                    # 不存在收藏记录，创建新记录
                    favorite = EmbyFavorites(
                        embyid=embyid,
                        embyname=embyname,
                        item_id=item_id,
                        item_name=item_name
                    )
                    session.add(favorite)
                    LOGGER.info(f"新增收藏记录: {embyname} -> {item_name} (EmbyID: {embyid})")
                    
            else:
                # 取消收藏操作：根据 embyname 删除记录
                records_to_delete = session.query(EmbyFavorites).filter(
                    EmbyFavorites.embyname == embyname,
                    EmbyFavorites.item_id == item_id
                ).all()
                
                if records_to_delete:
                    if len(records_to_delete) > 1:
                        LOGGER.warning(f"发现 {len(records_to_delete)} 个重复收藏记录，全部删除: {embyname} -> {item_name}")
                    
                    for record in records_to_delete:
                        session.delete(record)
                    
                    LOGGER.info(f"删除收藏记录: {embyname} -> {item_name} (删除了 {len(records_to_delete)} 条记录)")
                else:
                    LOGGER.info(f"未找到要删除的收藏记录: {embyname} -> {item_name}")
                    
            session.commit()
            return True
            
    except Exception as e:
        LOGGER.error(f"操作收藏记录失败: {str(e)}")
        return False
    
def sql_clear_favorites(emby_name: str) -> bool:
    """清除Emby用户的收藏记录"""
    try:
        with Session() as session:
            session.query(EmbyFavorites).filter(EmbyFavorites.embyname == emby_name).delete()
            session.commit()
        return True
    except Exception as e:
        LOGGER.error(f"清除收藏记录失败: {str(e)}")
        return False
def sql_get_favorites(embyid: str, page: int = 1, page_size: int = 20) -> list:
    """获取Emby用户的收藏记录"""
    try:
        with Session() as session:
            return session.query(EmbyFavorites).filter(EmbyFavorites.embyid == embyid).offset((page - 1) * page_size).limit(page_size).all()
    except Exception as e:
        LOGGER.error(f"获取收藏记录失败: {str(e)}")
        return []
    
def sql_update_favorites(condition, **kwargs):
    """
    更新收藏记录，根据condition来匹配，批量更新所有符合条件的记录
    处理唯一约束冲突的情况
    """
    with Session() as session:
        try:
            favorites = session.query(EmbyFavorites).filter(condition).all()
            if not favorites:
                return False

            new_embyid = kwargs.get('embyid')
            if not new_embyid:
                # 如果没有要更新的embyid，使用原来的逻辑
                for favorite in favorites:
                    for k, v in kwargs.items():
                        setattr(favorite, k, v)
                session.commit()
                LOGGER.info(f"收藏记录更新完成，成功更新 {len(favorites)} 条记录")
                return True
            
            # 处理embyid更新的情况，需要特殊处理唯一约束冲突
            success_count = 0
            items_to_update = {}  # 用于跟踪即将更新的 (embyid, item_id) 组合
            
            for favorite in favorites:
                try:
                    item_id = favorite.item_id
                    combination_key = (new_embyid, item_id)
                    
                    # 检查是否已经在当前批次中处理过这个组合
                    if combination_key in items_to_update:
                        LOGGER.warning(f"删除重复收藏记录(批次内重复): {favorite.embyname} -> {favorite.item_name}")
                        session.delete(favorite)
                        continue
                    
                    # 查找数据库中是否已存在相同的 (embyid, item_id) 组合
                    existing = session.query(EmbyFavorites).filter(
                        EmbyFavorites.embyid == new_embyid,
                        EmbyFavorites.item_id == item_id,
                        EmbyFavorites.id != favorite.id  # 排除当前记录
                    ).first()
                    
                    if existing:
                        # 如果存在冲突，删除当前记录，保留已存在的记录
                        LOGGER.warning(f"删除重复收藏记录(数据库冲突): {favorite.embyname} -> {favorite.item_name}")
                        session.delete(favorite)
                    else:
                        # 没有冲突，标记要更新并执行更新
                        items_to_update[combination_key] = favorite
                        for k, v in kwargs.items():
                            setattr(favorite, k, v)
                        success_count += 1
                        
                except Exception as e:
                    LOGGER.error(f"处理单条收藏记录失败: {str(e)}")
                    continue
                    
            session.commit()
            LOGGER.info(f"收藏记录更新完成，成功更新 {success_count} 条记录，删除 {len(favorites) - success_count} 条重复记录")
            return True
            
        except Exception as e:
            session.rollback()
            LOGGER.error(f"更新收藏记录失败: {str(e)}")
            return False