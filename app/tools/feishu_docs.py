from typing import Optional
from app.services.feishu_client import feishu_client
from app.config.settings import settings


def get_meeting_doc(doc_id: str, doc_type: str = "docx") -> str:
    """
    【OpenClaw Tool】获取飞书文档内容
    设计思路：
    1. 严格遵循OpenClaw Tool规范：单一职责、明确输入输出、内置异常处理
    2. 封装飞书文档读取逻辑，上层Agent不需要关心API细节
    3. 支持飞书新版文档(docx)和旧版文档(doc)
    4. 内置Mock能力，开发阶段无飞书权限时可返回测试内容

    Args:
        doc_id: 飞书文档ID
        doc_type: 文档类型，可选值：docx(默认，新版飞书文档)/doc(旧版飞书文档)

    Returns:
        文档的纯文本内容
    """
    try:
        # --------------------------
        # 【开发调试用Mock，上线删除】
        # 如果需要本地调试，放开下面的注释，直接返回测试会议纪要内容
        # return """
        # 2024年Q2项目规划会议纪要
        # 参会人：张三、李四、王五
        # 会议时间：2024-04-26
        #
        # 决议内容：
        # 1. 张三负责完成用户中心模块开发，截止5月10日，优先级高
        # 2. 李四负责完成支付接口对接，截止5月15日，优先级中
        # 3. 王五负责测试环境搭建，截止5月5日，优先级高
        # 4. 全体成员下周五之前提交个人季度工作总结
        # """
        # --------------------------

        if doc_type == "docx":
            # 获取新版飞书文档内容
            resp = feishu_client.get(
                f"/open-apis/docx/v1/documents/{doc_id}/raw_content"
            )
            return resp.get("data", {}).get("content", "")
        else:
            # 获取旧版飞书文档内容
            resp = feishu_client.get(
                f"/open-apis/doc/v2/{doc_id}/content"
            )
            return resp.get("data", {}).get("content", "")

    except Exception as e:
        raise Exception(f"读取飞书文档失败: {str(e)}")
