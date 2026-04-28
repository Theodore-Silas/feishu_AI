from typing import List
import logging
from app.tools.feishu_docs import get_meeting_doc
from app.tools.task_extractor import extract_action_items
from app.tools.feishu_task import create_feishu_task
from app.tools.feishu_message import send_notification
from app.models.task import TaskCreateResult, ProcessMeetingResponse


logger = logging.getLogger(__name__)


def process_meeting_workflow(meeting_doc_id: str, doc_type: str = "docx") -> ProcessMeetingResponse:
    """
    【OpenClaw 主控Agent】会议执行闭环核心工作流编排
    设计思路：
    1. 完全遵循OpenClaw架构规范：Agent仅负责编排调度，所有能力都通过调用工具实现，自身不实现任何业务逻辑
    2. 明确体现Tool Calling思维：每个步骤都经历"思考决策->调用工具->处理结果->下一步决策"的完整流程
    3. 全链路可观测：每个步骤都有日志记录，方便调试和问题排查
    4. 异常容错设计：单个任务处理失败不影响整体流程，核心链路有完善的异常捕获
    5. 高可扩展性：后续新增能力（如任务审核、风险识别、群同步等）仅需插入新的工具调用即可，无需修改核心架构

    Args:
        meeting_doc_id: 飞书会议文档ID
        doc_type: 文档类型，docx(新版)/doc(旧版)，默认docx

    Returns:
        完整的处理结果，包含任务提取数量、成功/失败数量、每个任务的详情
    """
    logger.info(f"启动会议闭环处理流程，文档ID：{meeting_doc_id}")
    results: List[TaskCreateResult] = []

    # ======================================
    # Agent 决策1：我需要先获取会议文档内容，才能进行后续处理
    # 调用工具：get_meeting_doc
    # ======================================
    try:
        logger.info("[Agent 思考] 第一步：获取会议文档内容")
        doc_content = get_meeting_doc(meeting_doc_id, doc_type)
        
        if not doc_content.strip():
            logger.warning("会议文档内容为空，流程结束")
            return ProcessMeetingResponse(
                meeting_doc_id=meeting_doc_id,
                total_tasks_extracted=0,
                success_tasks=0,
                failed_tasks=0,
                results=[]
            )
        logger.info(f"成功获取文档内容，共{len(doc_content)}字符")
    except Exception as e:
        logger.error(f"获取文档失败：{str(e)}")
        raise Exception(f"会议处理失败：无法读取会议文档，{str(e)}")

    # ======================================
    # Agent 决策2：已有文档内容，现在需要提取结构化任务项
    # 调用工具：extract_action_items
    # ======================================
    try:
        logger.info("[Agent 思考] 第二步：从文档中提取结构化任务项")
        action_items = extract_action_items(doc_content)
        total_tasks = len(action_items)
        logger.info(f"LLM提取完成，共获取到{total_tasks}个任务项")
        
        if total_tasks == 0:
            return ProcessMeetingResponse(
                meeting_doc_id=meeting_doc_id,
                total_tasks_extracted=0,
                success_tasks=0,
                failed_tasks=0,
                results=[]
            )
    except Exception as e:
        logger.error(f"任务提取失败：{str(e)}")
        raise Exception(f"会议处理失败：无法提取任务项，{str(e)}")

    # ======================================
    # Agent 决策3：已有任务列表，现在逐个创建飞书任务并通知负责人
    # 调用工具：create_feishu_task、send_notification
    # ======================================
    logger.info("[Agent 思考] 第三步：批量创建飞书任务并发送通知")
    success_count = 0
    failed_count = 0

    for item in action_items:
        logger.info(f"处理任务：{item.task}，负责人：{item.owner}")
        # 创建飞书任务
        create_result = create_feishu_task(item)
        results.append(create_result)

        if create_result.status == "成功":
            success_count += 1
            logger.info(f"任务创建成功，ID：{create_result.task_id}")
            # 给负责人发送通知（非待分配任务才发送）
            if item.owner and item.owner != "待分配":
                # TODO: 【后续优化】此处可增加姓名转飞书OpenID的工具调用
                send_notification(item.owner, create_result)
                logger.info(f"已发送通知给负责人：{item.owner}")
        else:
            failed_count += 1
            logger.error(f"任务创建失败：{create_result.error_msg}")

    # ======================================
    # Agent 决策4：所有任务处理完成，汇总结果返回
    # ======================================
    logger.info(f"流程执行完成：提取{total_tasks}个任务，成功{success_count}个，失败{failed_count}个")
    return ProcessMeetingResponse(
        meeting_doc_id=meeting_doc_id,
        total_tasks_extracted=total_tasks,
        success_tasks=success_count,
        failed_tasks=failed_count,
        results=results
    )
