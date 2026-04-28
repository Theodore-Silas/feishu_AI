import requests
import time
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from typing import Optional, Dict, Any
from app.config.settings import settings


class FeishuClient:
    """
    飞书API通用客户端
    设计思路：
    1. 统一处理飞书API鉴权，自动获取/刷新tenant_access_token
    2. 内置请求重试机制，处理网络波动、限流等异常场景
    3. 统一错误处理，上层工具不需要关心底层API细节
    4. 完全符合飞书开放平台API规范
    """
    _instance = None
    _tenant_access_token: Optional[str] = None
    _token_expire_time: int = 0

    def __new__(cls):
        """单例模式，全局只有一个飞书客户端实例，避免重复获取token"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_tenant_access_token(self) -> str:
        """获取租户访问凭证，自动缓存和刷新"""
        now = int(time.time())
        # 如果token还有5分钟以上有效期，直接返回缓存的token
        if self._tenant_access_token and now < self._token_expire_time - 300:
            return self._tenant_access_token

        # 调用飞书API获取新token
        url = f"{settings.feishu_api_base_url}/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": settings.feishu_app_id,
            "app_secret": settings.feishu_app_secret
        }
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise Exception(f"获取飞书tenant_access_token失败: {data.get('msg')}")

        self._tenant_access_token = data["tenant_access_token"]
        self._token_expire_time = now + data["expire"]
        return self._tenant_access_token

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((requests.exceptions.RequestException, ConnectionError))
    )
    def request(self, method: str, path: str, **kwargs) -> Dict[str, Any]:
        """
        通用请求方法，自动添加鉴权头，处理错误
        Args:
            method: HTTP方法 GET/POST/PUT/DELETE等
            path: API路径，不需要带base_url
            **kwargs: 其他requests参数
        Returns:
            API返回的JSON数据
        """
        url = f"{settings.feishu_api_base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {self._get_tenant_access_token()}"
        headers["Content-Type"] = "application/json; charset=utf-8"
        kwargs["headers"] = headers
        kwargs["timeout"] = kwargs.get("timeout", 15)

        resp = requests.request(method, url, **kwargs)
        resp.raise_for_status()
        data = resp.json()

        # 处理飞书API错误码
        if data.get("code") != 0:
            # token过期，自动刷新后重试一次
            if data.get("code") == 99991663 or data.get("code") == 99991661:
                self._tenant_access_token = None
                return self.request(method, path, **kwargs)
            raise Exception(f"飞书API请求失败: 错误码={data.get('code')}, 错误信息={data.get('msg')}")

        return data

    def get(self, path: str, **kwargs) -> Dict[str, Any]:
        """GET请求快捷方法"""
        return self.request("GET", path, **kwargs)

    def post(self, path: str, **kwargs) -> Dict[str, Any]:
        """POST请求快捷方法"""
        return self.request("POST", path, **kwargs)


# 全局单例飞书客户端实例
feishu_client = FeishuClient()
