from bot import LOGGER, config
from bot.func_helper.moviepilot import get_download_task, get_history_transfer_task
from bot.sql_helper.sql_request_record import sql_update_request_status, sql_get_request_record_by_transfer_state, sql_get_request_record_by_download_id
from bot.func_helper.scheduler import scheduler
from bot.func_helper.msg_utils import sendMessage

async def sync_download_tasks():
    """同步MoviePilot下载任务状态到数据库"""
    try:
        # 获取所有下载任务
        download_tasks = await get_download_task()
        if not download_tasks:
            return
        download_count = 0
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
        
        # 检查每个记录的转移状态
        for record in transfer_tasks:
            transfer_state = await get_history_transfer_task(record.request_name, record.download_id)
            if transfer_state is not None:
                if transfer_state:
                    await sendMessage(record.tg, f"恭喜您点播的「{record.request_name}」已成功入库！")
                sql_update_request_status(
                    download_id=record.download_id,
                    transfer_state=transfer_state,
                    download_state='completed',
                    progress=100,
                    left_time='0'
                )
                transfer_count += 1

        LOGGER.info(f"同步了 {download_count} 个下载任务状态, {transfer_count} 个转移任务状态")
    except Exception as e:
        LOGGER.error(f"同步下载任务状态时出错: {str(e)}")
# 如果MoviePilot功能开启，添加定时任务
if config.moviepilot.status:
    scheduler.add_job(sync_download_tasks, 'interval',
                     seconds=60, id='sync_download_tasks')