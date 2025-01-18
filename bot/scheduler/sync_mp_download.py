from bot import LOGGER, config, bot
from bot.func_helper.moviepilot import get_download_task, get_history_transfer_task_by_title_download_id
from bot.sql_helper.sql_request_record import sql_update_request_status, sql_get_request_record_by_transfer_state, sql_get_request_record_by_download_id
from bot.func_helper.scheduler import scheduler
async def sync_download_tasks():
    """同步MoviePilot下载任务状态到数据库"""
    try:
        # 获取所有下载任务
        download_tasks = await get_download_task()
        download_count = 0
        if download_tasks is not None:
            # 更新每个任务的状态
            for task in download_tasks:
                record = sql_get_request_record_by_download_id(task['download_id'])
                if record is None:
                    continue
                download_id = task['download_id']
                download_state = task['state']
                progress = task['progress']
                left_time = task.get('left_time', '未知')

                # 根据状态更新数据库
                if download_state == 'downloading':
                    # 正在下载中
                    sql_update_request_status(
                        download_id=download_id,
                        download_state='downloading',
                        progress=progress,
                        left_time=left_time
                    )
                elif download_state == 'completed':
                    # 下载完成
                    sql_update_request_status(
                        download_id=download_id,
                        download_state='completed',
                        progress=100,
                        left_time='0'
                    )
                elif download_state == 'failed':
                    # 下载失败
                    sql_update_request_status(
                        download_id=download_id,
                        download_state='failed',
                        progress=progress,
                        left_time='失败'
                    )
                elif download_state == 'pending':
                    # 等待下载
                    sql_update_request_status(
                        download_id=download_id,
                        download_state='pending',
                        progress=0,
                        left_time='等待中'
                    )
                download_count += 1
        # 获取需要检查转移状态的记录
        transfer_tasks = sql_get_request_record_by_transfer_state()
        transfer_count = 0
        if transfer_tasks is not None:
            # 检查每个记录的转移状态
            for record in transfer_tasks:
                transfer_state = await get_history_transfer_task_by_title_download_id("", record.download_id, count=100)
                if transfer_state is not None:
                    if transfer_state:
                        try:
                            await bot.send_message(chat_id=record.tg, text = f"💯恭喜您点播的「{record.request_name}」已成功入库！")
                        except Exception as e:
                            LOGGER.error(f"[MoviePilot] 发送通知到{record.tg}失败: {str(e)}")
                    sql_update_request_status(
                        download_id=record.download_id,
                        transfer_state=transfer_state,
                        download_state='completed',
                        progress=100,
                        left_time='0'
                    )
                    transfer_count += 1
        if download_count > 0 or transfer_count > 0:
            LOGGER.info(f"[MoviePilot] 同步了 {download_count} 个下载任务状态, {transfer_count} 个转移任务状态")
    except Exception as e:
        LOGGER.error(f"[MoviePilot] 同步下载任务状态时出错: {str(e)}")
# 如果MoviePilot功能开启，添加定时任务
if config.moviepilot.status:
    scheduler.add_job(sync_download_tasks, 'interval',
                     seconds=60, id='sync_download_tasks')