from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uvicorn

from app.config.settings import settings
from app.agents.meeting_agent import process_meeting_workflow
from app.models.task import ProcessMeetingResponse


# 初始化FastAPI应用
app = FastAPI(
    title="会议执行闭环Agent API",
    description="基于OpenClaw架构的企业级会议任务自动提取、创建、通知全流程系统",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS，支持跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 接口请求模型
class ProcessMeetingRequest(BaseModel):
    meeting_doc_id: str = Field(description="飞书会议文档ID")
    doc_type: Optional[str] = Field(default="docx", description="文档类型：docx(新版飞书文档)/doc(旧版飞书文档)")


@app.post(
    "/process_meeting",
    response_model=ProcessMeetingResponse,
    summary="处理会议纪要",
    description="输入飞书会议文档ID，自动提取任务、创建飞书任务、发送通知，返回完整处理结果"
)
def process_meeting(request: ProcessMeetingRequest):
    """
    会议处理核心接口
    设计思路：
    1. 标准RESTful接口设计，遵循OpenAPI规范，自动生成接口文档
    2. 参数自动校验，不符合格式的请求会直接返回422错误
    3. 与业务逻辑完全解耦，仅负责请求接收和响应返回，业务逻辑全部在Agent层实现
    4. 全局异常处理，统一错误返回格式
    """
    try:
        result = process_meeting_workflow(
            meeting_doc_id=request.meeting_doc_id,
            doc_type=request.doc_type
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health", summary="健康检查接口", description="用于监控服务运行状态")
def health_check():
    return {"status": "ok", "service": "meeting-execution-agent", "version": "1.0.0"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.service_host,
        port=settings.service_port,
        reload=settings.service_debug
    )
