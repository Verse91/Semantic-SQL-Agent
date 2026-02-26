from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import router as api_router

app = FastAPI(
    title="Semantic SQL Agent API",
    description="自然语言转 SQL 查询服务 API",
    version="0.2.0"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册 API 路由
app.include_router(api_router, prefix="/api", tags=["SQL Agent"])


@app.get("/")
def root():
    """健康检查"""
    return {
        "status": "ok",
        "service": "Semantic SQL Agent",
        "version": "0.2.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
