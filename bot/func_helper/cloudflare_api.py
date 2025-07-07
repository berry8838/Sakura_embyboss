"""
Cloudflare API 辅助函数
用于管理三级域名的创建和删除
"""
import aiohttp
import asyncio
from bot import cloudflare, LOGGER
from typing import Optional, Tuple


class CloudflareAPI:
    def __init__(self):
        self.api_token = cloudflare.api_token
        self.zone_id = cloudflare.zone_id
        self.domain = cloudflare.domain
        self.target_ip = cloudflare.target_ip
        self.base_url = "https://api.cloudflare.com/client/v4"
        self.headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

    async def create_subdomain(self, username: str) -> Tuple[bool, Optional[str]]:
        """
        创建三级域名
        :param username: 用户名，用作子域名前缀
        :return: (是否成功, 域名或错误信息)
        """
        if not cloudflare.status:
            LOGGER.info("Cloudflare API 未启用，跳过域名创建")
            return True, None
            
        if not all([self.api_token, self.zone_id, self.domain, self.target_ip]):
            LOGGER.error("Cloudflare API 配置不完整")
            return False, "Cloudflare 配置不完整"

        subdomain = f"{username}.{self.domain}"
        
        # 构建 DNS 记录数据
        dns_record = {
            "type": "A",
            "name": subdomain,
            "content": self.target_ip,
            "ttl": 300,
            "proxied": False
        }

        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/zones/{self.zone_id}/dns_records"
                
                async with session.post(url, json=dns_record, headers=self.headers) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get("success"):
                        record_id = result["result"]["id"]
                        LOGGER.info(f"成功创建域名: {subdomain} -> {self.target_ip}")
                        return True, subdomain
                    else:
                        error_msg = result.get("errors", [{"message": "未知错误"}])[0]["message"]
                        LOGGER.error(f"创建域名失败: {subdomain}, 错误: {error_msg}")
                        return False, error_msg
                        
        except Exception as e:
            LOGGER.error(f"Cloudflare API 请求异常: {str(e)}")
            return False, str(e)

    async def delete_subdomain(self, username: str) -> Tuple[bool, Optional[str]]:
        """
        删除三级域名
        :param username: 用户名，用于构建要删除的域名
        :return: (是否成功, 错误信息)
        """
        if not cloudflare.status:
            LOGGER.info("Cloudflare API 未启用，跳过域名删除")
            return True, None
            
        if not all([self.api_token, self.zone_id, self.domain]):
            LOGGER.error("Cloudflare API 配置不完整")
            return False, "Cloudflare 配置不完整"

        subdomain = f"{username}.{self.domain}"
        
        try:
            # 首先查找 DNS 记录
            record_id = await self._find_dns_record(subdomain)
            if not record_id:
                LOGGER.warning(f"未找到域名记录: {subdomain}")
                return True, None  # 如果记录不存在，视为删除成功
            
            # 删除 DNS 记录
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/zones/{self.zone_id}/dns_records/{record_id}"
                
                async with session.delete(url, headers=self.headers) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get("success"):
                        LOGGER.info(f"成功删除域名: {subdomain}")
                        return True, None
                    else:
                        error_msg = result.get("errors", [{"message": "未知错误"}])[0]["message"]
                        LOGGER.error(f"删除域名失败: {subdomain}, 错误: {error_msg}")
                        return False, error_msg
                        
        except Exception as e:
            LOGGER.error(f"Cloudflare API 删除请求异常: {str(e)}")
            return False, str(e)

    async def _find_dns_record(self, domain_name: str) -> Optional[str]:
        """
        查找指定域名的 DNS 记录 ID
        :param domain_name: 完整域名
        :return: 记录 ID 或 None
        """
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/zones/{self.zone_id}/dns_records"
                params = {
                    "name": domain_name,
                    "type": "A"
                }
                
                async with session.get(url, params=params, headers=self.headers) as response:
                    result = await response.json()
                    
                    if response.status == 200 and result.get("success"):
                        records = result.get("result", [])
                        if records:
                            return records[0]["id"]
                    return None
                    
        except Exception as e:
            LOGGER.error(f"查找 DNS 记录异常: {str(e)}")
            return None


# 创建全局实例
cf_api = CloudflareAPI()


async def create_user_domain(username: str) -> Tuple[bool, Optional[str]]:
    """
    为用户创建三级域名的便捷函数
    :param username: 用户名
    :return: (是否成功, 域名或错误信息)
    """
    return await cf_api.create_subdomain(username)


async def delete_user_domain(username: str) -> Tuple[bool, Optional[str]]:
    """
    删除用户三级域名的便捷函数
    :param username: 用户名
    :return: (是否成功, 错误信息)
    """
    return await cf_api.delete_subdomain(username) 