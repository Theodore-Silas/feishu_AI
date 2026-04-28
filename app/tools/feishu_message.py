from typing import Dict
from app.services.feishu_client import feishu_client
from app.models.task import TaskCreateResult


def send_notification(owner_open_id: str, task_info: TaskCreateResult) -> bool:
    """
    【OpenClaw Tool】给任务负责人发送飞书通知卡片
    设计思路：
    1. 单一职责，仅负责消息发送能力，上层可灵活触发
    2. 使用飞书卡片消息，信息展示更清晰，支持直接跳转任务详情
    3. 异常安全，发送失败不影响主流程，仅返回成功/失败状态
    4. 后续可扩展支持消息模板、群通知、@提醒等能力

    Args:
        owner_open_id: 任务负责人的飞书open_id
        task_info: 任务创建结果信息

    Returns:
        发送是否成功
    """
    try:
        # --------------------------
        # 【开发调试用Mock，上线删除】
        # 如果需要本地调试，放开下面的注释，直接返回发送成功
        # return True
        # --------------------------

        # 构造飞书消息卡片内容
        card_content = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": "📋 新任务通知"
                },
                "template": "blue"
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**任务名称：** {task_info.task_name}\n**优先级：** {task_info.priority if hasattr(task_info, 'priority') else '中'}\n**截止时间：** {task_info.deadline if hasattr(task_info, 'deadline') else '无'}\n**任务ID：** {task_info.task_id}"
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "查看任务详情"
                            },
                            "type": "primary",
                            "url": f"https://applink.feishu.cn/client/task/detail?taskId={task_info.task_id}"
                        }
                    ]
                }
            ]
        }

        # 调用飞书发送消息API
        feishu_client.post(
            "/open-apis/im/v1/messages",
            params={"receive_id_type": "open_id"},
            json={
                "receive_id": owner_open_id,
                "msg_type": "interactive",
                "content": str(card_content).replace("'", '"')
            }
        )

        return True

    except Exception as e:
        # 消息发送失败不抛出异常，仅返回失败状态，避免影响主流程
        print(f"发送飞书通知失败: {str(e)}")
        return False
