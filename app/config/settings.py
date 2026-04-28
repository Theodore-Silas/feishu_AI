from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """
    全局配置管理类
    基于pydantic-settings实现，自动从环境变量加载配置，支持类型校验
    设计思路：
    1. 所有配置项都有默认值和类型约束，启动时自动校验，避免配置错误
    2. 敏感信息全部从环境变量加载，不硬编码到代码中
    3. 支持.env文件加载，方便开发环境使用
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # FastAPI 服务配置
    service_host: str = "0.0.0.0"
    service_port: int = 8000
    service_debug: bool = False

    # 飞书开放平台配置
    feishu_app_id: str
    feishu_app_secret: str
    feishu_tenant_key: Optional[str] = None
    feishu_api_base_url: str = "https://open.feishu.cn"

    # LLM 配置（支持OpenAI协议的大模型，比如DeepSeek、通义千问、GPT等）
    llm_api_base: str = "https://api.openai.com/v1"
    llm_api_key: str
    llm_model_name: str = "gpt-4o"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 2000

    # 业务配置
    feishu_task_project_id: Optional[str] = None  # 飞书任务默认项目ID
    feishu_notification_template_id: Optional[str] = None  # 通知卡片模板ID


# 全局单例配置实例
settings = Settings()
