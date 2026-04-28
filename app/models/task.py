from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
import re


class ActionItem(BaseModel):
    """
    任务项数据模型，定义LLM提取任务的结构化输出格式
    设计思路：
    1. 严格定义每个字段的类型和约束，确保LLM输出符合预期格式
    2. 内置字段校验逻辑，自动修正不规范的输出
    3. 完全匹配OpenClaw Structured Output规范
    """
    task: str = Field(description="任务具体内容，描述清晰明确，包含执行要求")
    owner: str = Field(description="任务负责人，飞书用户姓名或用户ID")
    deadline: str = Field(description="任务截止时间，格式为YYYY-MM-DD，没有明确截止时间则为空字符串")
    priority: str = Field(description="任务优先级，可选值：高/中/低，默认中")

    @validator("priority")
    def validate_priority(cls, v):
        """校验优先级，自动修正不规范值"""
        priority_map = {"高": "高", "中": "中", "低": "低", "high": "高", "medium": "中", "low": "低", "H": "高", "M": "中", "L": "低"}
        return priority_map.get(v.strip() if v else "中", "中")

    @validator("deadline")
    def validate_deadline(cls, v):
        """校验截止时间格式，自动修正不规范的日期"""
        if not v or v.strip() == "":
            return ""
        # 尝试匹配常见日期格式
        v = v.strip()
        # 匹配YYYY-MM-DD
        if re.match(r'^\d{4}-\d{2}-\d{2}$', v):
            try:
                datetime.strptime(v, "%Y-%m-%d")
                return v
            except:
                pass
        # 匹配YYYY/MM/DD
        if re.match(r'^\d{4}/\d{2}/\d{2}$', v):
            return v.replace("/", "-")
        # 匹配MM/DD
        if re.match(r'^\d{1,2}/\d{1,2}$', v):
            current_year = datetime.now().year
            try:
                return f"{current_year}-{v.replace('/', '-')}"
            except:
                pass
        # 其他格式统一返回空，后续可扩展支持自然语言日期解析
        return ""


class ActionItemExtractResult(BaseModel):
    """LLM提取任务的返回结果模型"""
    items: List[ActionItem] = Field(description="提取到的任务项列表")


class TaskCreateResult(BaseModel):
    """飞书任务创建结果模型"""
    task_id: str = Field(description="飞书任务ID")
    task_name: str = Field(description="任务名称")
    owner: str = Field(description="负责人")
    status: str = Field(description="创建状态：成功/失败")
    error_msg: Optional[str] = Field(description="错误信息，创建失败时返回")


class ProcessMeetingResponse(BaseModel):
    """会议处理接口返回结果"""
    meeting_doc_id: str = Field(description="会议文档ID")
    total_tasks_extracted: int = Field(description="提取到的任务总数")
    success_tasks: int = Field(description="成功创建的任务数")
    failed_tasks: int = Field(description="创建失败的任务数")
    results: List[TaskCreateResult] = Field(description="每个任务的创建结果")
