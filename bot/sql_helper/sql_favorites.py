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
    
    Args:
        embyid: Emby用户ID
        embyname: Emby用户名
        item_id: 项目ID
        item_name: 项目名称
        is_favorite: True为收藏，False为取消收藏
    """
    try:
        with Session() as session:
            # 查找是否存在记录
            existing = session.query(EmbyFavorites).filter(
                EmbyFavorites.embyid == embyid,
                EmbyFavorites.item_id == item_id
            ).first()
            
            if is_favorite:
                if existing:
                    # 更新现有记录
                    existing.embyname = embyname
                    existing.item_name = item_name
                    existing.created_at = datetime.now()
                    LOGGER.info(f"更新收藏记录: {embyname} -> {item_name}")
                else:
                    # 创建新记录
                    favorite = EmbyFavorites(
                        embyid=embyid,
                        embyname=embyname,
                        item_id=item_id,
                        item_name=item_name
                    )
                    session.add(favorite)
                    LOGGER.info(f"新增收藏记录: {embyname} -> {item_name}")
            else:
                if existing:
                    # 删除记录
                    session.delete(existing)
                    LOGGER.info(f"删除收藏记录: {embyname} -> {item_name}")
                    
            session.commit()
            return True
            
    except Exception as e:
        LOGGER.error(f"操作收藏记录失败: {str(e)}")
        return False
    
def sql_clear_favorites(embyid: str) -> bool:
    """清除Emby用户的收藏记录"""
    try:
        with Session() as session:
            session.query(EmbyFavorites).filter(EmbyFavorites.embyid == embyid).delete()
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
    """
    with Session() as session:
        try:
            favorites = session.query(EmbyFavorites).filter(condition).all()
            if not favorites:
                return False
            for favorite in favorites:
                for k, v in kwargs.items():
                    setattr(favorite, k, v)
            session.commit()
            return True
        except Exception as e:
            LOGGER.error(f"更新收藏记录失败: {str(e)}")
            return False