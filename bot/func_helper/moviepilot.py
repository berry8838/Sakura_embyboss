import requests
import json
from bot import LOGGER, moviepilot, save_config
import aiohttp
import asyncio

# 添加配置类
class MoviePilot:
    def __init__(self):
        self.url = moviepilot.url
        self.username = moviepilot.username 
        self.password = moviepilot.password
        self.access_token = moviepilot.access_token or ''

mp = MoviePilot()

TIMEOUT = 30
# aiohttp重试装饰器
def aiohttp_retry(retry_count):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            for i in range(retry_count):
                try:
                    return await func(*args, **kwargs)
                except aiohttp.ClientError:
                    await asyncio.sleep(3)  # 延迟 3 秒后进行重试
            return None

        return wrapper

    return decorator
@aiohttp_retry(3)
async def _do_request(request):
    async with aiohttp.ClientSession() as session:
        async with session.request(method=request['method'], url=request['url'], headers=request['headers'], data=request.get('data')) as response:
            if response.status == 401 or response.status == 403:
                LOGGER.error("MP Token过期, 尝试重新登录.")
                success = await login()
                if success:
                    request['headers']['Authorization'] = mp.access_token
                    return await _do_request(request)
                return None
            return await response.json()
async def login():
    url = f"{mp.url}/api/v1/login/access-token"
    payload = f"username={mp.username}&password={mp.password}"
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    response = requests.post(url, data=payload, headers=headers, timeout=TIMEOUT)
    result = response.json()
    if 'access_token' in result:
        mp.access_token = result['token_type'] + ' ' + result['access_token']
        moviepilot.access_token = mp.access_token # 保存到config
        save_config()
        LOGGER.info("MP 登录成功, token已保存")
        return True
    else:
        LOGGER.error(f"MP 登录失败: {result}")
        return False

async def search(title):
    """
    搜索资源
    Args:
        title: 搜索关键词
    Returns:
        (success, results)
        success: bool 是否成功
        results: list 搜索结果列表
    """
    if title is None:
        return False, []
        
    url = f"{mp.url}/api/v1/search/title?keyword={title}"
    headers = {'Authorization': mp.access_token}
    request = {'method': 'GET', 'url': url, 'headers': headers}
    try:
        data = await _do_request(request)
        results = []
        if data.get("success", False):
            data = data["data"]
            for item in data:
                meta_info = item.get("meta_info", {})
                torrent_info = item.get("torrent_info", {})
                
                seeders = torrent_info.get("seeders", "0")
                try:
                    seeders = int(seeders) if seeders else 0
                except (ValueError, TypeError):
                    seeders = 0
                result = {
                    "title": meta_info.get("title", ""),
                    "year": meta_info.get("year", ""),
                    "type": meta_info.get("type", ""),
                    "resource_pix": meta_info.get("resource_pix", ""),
                    "video_encode": meta_info.get("video_encode", ""),
                    "audio_encode": meta_info.get("audio_encode", ""),
                    "resource_team": meta_info.get("resource_team", ""),
                    "seeders": seeders,
                    "size": torrent_info.get("size", "0"),
                    "labels": torrent_info.get("labels", ""),
                    "description": torrent_info.get("description", ""),
                    "torrent_info": torrent_info,
                }
                results.append(result)
                
        # 按做种数排序并限制返回数量
        results.sort(key=lambda x: x["seeders"], reverse=True)  # 现在 seeders 一定是数字
        if len(results) > 10:
            results = results[:10]
            
        LOGGER.info("MP Search successful!")
        return True, results
    except Exception as e:
        LOGGER.error(f"MP Search failed: {str(e)}")
        return False, []


async def add_download_task(param):
    if param is None:
        return False, None
    url = f"{mp.url}/api/v1/download/add"
    headers = {'Content-Type': 'application/json',
               'Authorization': mp.access_token}
    jsonData = json.dumps(param)
    request = {'method': 'POST', 'url': url,
               'headers': headers, 'data': jsonData}
    try:
        result = await _do_request(request)
        if result.get("success", False):
            LOGGER.info(f"MP 添加下载任务成功, ID: {result['data']['download_id']}")
            return True, result["data"]["download_id"]
        else:
            LOGGER.error(f"MP 添加下载任务失败: {result.get('message')}")
            return False, None
    except Exception as e:
        LOGGER.error(f"MP 添加下载任务失败: {e}")
        return False, None

async def get_download_task():
    url = f"{mp.url}/api/v1/download"
    headers = {'Authorization': mp.access_token}
    request = {'method': 'GET', 'url': url, 'headers': headers}
    try:
        result = await _do_request(request)
        data = []
        for item in result:
            data.append(
                {'download_id': item['hash'],
                 'state': item['state'],
                 'progress': item['progress'],
                 'left_time': item['left_time']
                 })
        return data
    except Exception as e:
        LOGGER.error(f"MP 获取下载任务失败: {e}")
        return None
async def get_history_transfer_task(title, download_id, page = 1, count = 50):
    url = f"{mp.url}/api/v1/history/transfer?title={title}&page={page}&count={count}"
    headers = {'Authorization': mp.access_token}
    request = {'method': 'GET', 'url': url, 'headers': headers}
    try:
        result = await _do_request(request)
        if result.get("success", False) and result.get("data", []):
            for item in result["data"]["list"]:
                if item['download_hash'] == download_id:
                    return item['status']
            return None
        else:
            LOGGER.error(f"MP 获取历史转移任务失败: {result.get('message')}")
            return None
    except Exception as e:
        LOGGER.error(f"MP 获取历史转移任务失败: {e}")
        return None
