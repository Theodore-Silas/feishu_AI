from datetime import datetime
from typing import Optional
from app.services.feishu_client import feishu_client
from app.config.settings import settings
from app.models.task import ActionItem, TaskCreateResult


def create_feishu_task(action_item: ActionItem) -> TaskCreateResult:
    """
    【OpenClaw Tool】在飞书任务中创建任务
    设计思路：
    1. 严格遵循OpenClaw Tool规范，输入为结构化ActionItem，输出为结构化创建结果
    2. 内置字段转换逻辑，自动适配飞书任务API的参数要求
    3. 异常安全，创建失败时返回错误信息而不是抛出异常，上层可灵活处理
    4. 支持配置默认项目ID，任务自动归属到指定项目下

    Args:
        action_item: 结构化的任务项对象

    Returns:
        任务创建结果，包含任务ID、状态、错误信息等
    """
    try:
        # --------------------------
        # 【开发调试用Mock，上线删除】
        # 如果需要本地调试，放开下面的注释，直接返回模拟创建结果
        # return TaskCreateResult(
        #     task_id=f"mock_task_{int(datetime.now().timestamp())}",
        #     task_name=action_item.task,
        #     owner=action_item.owner,
        #     status="成功",
        #     error_msg=None
        # )
        # --------------------------

        # 优先级映射：飞书任务优先级 1=高 2=中 3=低
        priority_map = {"高": 1, "中": 2, "低": 3}

        # 构造请求参数
        payload = {
            "name": action_item.task,
            "description": f"来源：会议纪要自动提取\n负责人：{action_item.owner}\n截止时间：{action_item.deadline if action_item.deadline else '无'}",
            "priority": priority_map.get(action_item.priority, 2),
            "mode": "task"
        }

        # 处理截止时间：转换为毫秒时间戳
        if action_item.deadline:
            try:
                dt = datetime.strptime(action_item.deadline, "%Y-%m-%d")
                payload["deadline"] = int(dt.timestamp() * 1000)
            except:
                pass

        # 添加到指定项目（如果配置了项目ID）
        if settings.feishu_task_project_id:
            payload["project_id"] = settings.feishu_task_project_id

        # TODO: 【后续优化】如果owner是姓名，需要先调用飞书用户搜索接口转换为用户open_id
        # 现在假设传入的owner是飞书用户open_id，如果是姓名这里会创建失败
        if action_item.owner and action_item.owner != "待分配":
            payload["role_list"] = [
                {
                    "role": "assignee",
                    "member_key": action_item.owner
                }
            ]

        # 调用飞书任务创建API
        resp = feishu_client.post(
            "/open-apis/task/v2/tasks",
            json=payload
        )

        task_id = resp.get("data", {}).get("task", {}).get("guid", "")
        return TaskCreateResult(
            task_id=task_id,
            task_name=action_item.task,
            owner=action_item.owner,
            status="成功",
            error_msg=None
        )

    except Exception as e:
        return TaskCreateResult(
            task_id="",
            task_name=action_item.task,
            owner=action_item.owner,
            status="失败",
            error_msg=str(e)
        )
