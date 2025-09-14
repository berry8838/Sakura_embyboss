from fastapi import APIRouter, Request
from bot.sql_helper.sql_favorites import sql_add_favorites
from bot.sql_helper.sql_emby import Emby
from bot.sql_helper import Session
from bot import LOGGER, bot
import json

router = APIRouter()

async def send_favorite_notification(tg_id: int, embyname: str, item_name: str, is_favorite: bool):
    """发送收藏通知到Telegram"""
    try:
        action = "收藏" if is_favorite else "取消收藏"
        message = f"📢 您的Emby账号 {embyname} {action}了《{item_name}》"
        
        await bot.send_message(
            chat_id=tg_id,
            text=message
        )
        LOGGER.info(f"已发送{action}通知到用户 {tg_id}")
    except Exception as e:
        LOGGER.error(f"发送通知失败: {str(e)}")

@router.post("/webhook/favorites")
async def handle_favorite_webhook(request: Request):
    """处理Emby服务器发送的收藏变更webhook"""
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
            return {
                "status": "error",
                "message": "No data received"
            }
            
        # 提取用户和项目信息
        user_data = webhook_data.get("User", {})
        item_data = webhook_data.get("Item", {})
        
        # 获取关键数据
        embyid = user_data.get("Id", "")
        embyname = user_data.get("Name", "")
        item_id = item_data.get("Id", "")
        item_name = item_data.get("Name", "")
        
        # 检查收藏状态
        is_favorite = item_data.get("UserData", {}).get("IsFavorite", False)
        
        # 构建返回数据
        response_data = {
            "user": {
                "name": embyname,
                "id": embyid
            },
            "item": {
                "name": item_name,
                "id": item_id
            },
            "is_favorite": is_favorite,
            "event": webhook_data.get("Event", ""),
            "date": webhook_data.get("Date", "")
        }
        # 保存到数据库
        save_result = sql_add_favorites(
            embyid=embyid,
            embyname=embyname,
            item_id=item_id,
            item_name=item_name,
            is_favorite=is_favorite
        )
        
        if save_result:
            action = "收藏" if is_favorite else "取消收藏"
            LOGGER.info(f"用户 {embyname} {action}了项目 {item_name}")
            
            # 创建新的session来查询用户
            session = Session()
            try:
                user = session.query(Emby).filter(
                    Emby.name == embyname
                ).first()
                
                if user and user.tg:
                    # 发送Telegram通知
                    await send_favorite_notification(
                        tg_id=user.tg,
                        embyname=embyname,
                        item_name=item_name,
                        is_favorite=is_favorite
                    )
            finally:
                session.close()  # 确保session被关闭
        else:
            LOGGER.error(f"操作收藏记录失败")
            
        return {
            "status": "success",
            "message": "Favorite event processed",
            "data": response_data
        }
        
    except Exception as e:
        LOGGER.error(f"处理Webhook失败: {str(e)}")
        return {
            "status": "error",
            "message": str(e)
        }