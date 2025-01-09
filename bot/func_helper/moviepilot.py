import requests
import json
from bot import LOGGER, moviepilot
import aiohttp
import asyncio

# 添加配置类
class MoviePilot:
    def __init__(self):
        self.url = moviepilot.url
        self.username = moviepilot.username 
        self.password = moviepilot.password
        self.access_token = moviepilot.access_token

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
                LOGGER.error("MP Token expired, attempting to re-login.")
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
        LOGGER.info("MP Login successful, token stored")
        return True
    else:
        LOGGER.error(f"MP Login failed: {result}")
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
                result = {
                    "title": meta_info.get("title", ""),
                    "year": meta_info.get("year", ""),
                    "type": meta_info.get("type", ""),
                    "resource_pix": meta_info.get("resource_pix", ""),
                    "video_encode": meta_info.get("video_encode", ""),
                    "audio_encode": meta_info.get("audio_encode", ""),
                    "resource_team": meta_info.get("resource_team", ""),
                    "seeders": torrent_info.get("seeders", ""),
                    "size": torrent_info.get("size", ""),
                    "labels": torrent_info.get("labels", ""),
                    "description": torrent_info.get("description", ""),
                    "torrent_info": torrent_info,
                }
                results.append(result)
                
        # 按做种数排序并限制返回数量
        results.sort(key=lambda x: int(x["seeders"]), reverse=True)
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
            LOGGER.info(f"MP add download task successful, ID: {result['data']['download_id']}")
            return True, result["data"]["download_id"]
        else:
            LOGGER.error(f"MP add download task failed: {result.get('message')}")
            return False, None
    except Exception as e:
        LOGGER.error(f"MP add download task failed: {e}")
        return False, None

async def get_download_task():
    url = f"{mp.url}/api/v1/download"
    headers = {'Authorization': mp.access_token}
    request = {'method': 'GET', 'url': url, 'headers': headers}
    try:
        result = await _do_request(request)
        data = []
        for item in result:
            data.append({'download_id': item['hash'], 'state': item['state'], 'progress': item['progress']})
        return data
    except Exception as e:
        LOGGER.error(f"MP get download task failed: {e}")
        return None