from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from typing import List
from app.config.settings import settings
from app.models.task import ActionItem, ActionItemExtractResult


# 初始化LLM客户端，支持所有兼容OpenAI协议的大模型服务
llm_client = OpenAI(
    api_key=settings.llm_api_key,
    base_url=settings.llm_api_base
)


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def extract_action_items(doc_content: str) -> List[ActionItem]:
    """
    【OpenClaw Tool】从会议纪要文本中提取任务项
    设计思路：
    1. 完全遵循Structured Output规范，强制LLM返回符合Pydantic模型的JSON结构
    2. 内置3次重试机制，处理LLM返回格式错误、调用失败等异常
    3. 自动进行数据校验，不符合格式的输出会自动重试
    4. 单一职责，仅负责任务提取能力，上层可灵活复用

    Args:
        doc_content: 会议纪要的纯文本内容

    Returns:
        提取到的任务项列表，每个任务包含task/owner/deadline/priority字段
    """
    try:
        # --------------------------
        # 【开发调试用Mock，上线删除】
        # 如果需要本地调试，放开下面的注释，直接返回测试任务数据
        # return [
        #     ActionItem(
        #         task="完成用户中心模块开发",
        #         owner="张三",
        #         deadline="2024-05-10",
        #         priority="高"
        #     ),
        #     ActionItem(
        #         task="完成支付接口对接",
        #         owner="李四",
        #         deadline="2024-05-15",
        #         priority="中"
        #     ),
        #     ActionItem(
        #         task="搭建测试环境",
        #         owner="王五",
        #         deadline="2024-05-05",
        #         priority="高"
        #     )
        # ]
        # --------------------------

        # 构造提取任务的Prompt
        prompt = f"""
        你是一个专业的会议纪要处理助手，请从下面的会议纪要内容中提取所有的行动项（Action Items）。
        每个行动项必须包含以下字段：
        1. task: 任务具体内容，描述要清晰完整
        2. owner: 任务负责人，提取明确的负责人姓名，如果没有明确负责人则填"待分配"
        3. deadline: 任务截止时间，统一格式为YYYY-MM-DD，如果没有明确截止时间则填空字符串
        4. priority: 任务优先级，只能是"高"/"中"/"低"三个值，没有明确说明则默认为"中"

        注意：
        - 只提取明确需要执行的任务，不要提取会议讨论的背景信息
        - 确保每个任务的信息准确，不要编造内容
        - 严格按照要求的JSON格式返回，不要添加任何额外说明

        会议纪要内容：
        {doc_content}
        """

        # 调用LLM，强制返回结构化数据
        response = llm_client.beta.chat.completions.parse(
            model=settings.llm_model_name,
            messages=[
                {"role": "system", "content": "你是专业的会议任务提取助手，严格按照要求返回结构化JSON数据。"},
                {"role": "user", "content": prompt}
            ],
            response_format=ActionItemExtractResult,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens
        )

        # 解析并校验返回结果
        result = response.choices[0].message.parsed
        if not result or not result.items:
            return []

        return result.items

    except Exception as e:
        raise Exception(f"提取任务项失败: {str(e)}")
