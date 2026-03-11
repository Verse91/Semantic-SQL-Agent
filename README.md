# Semantic-SQL-Agent

本地 AI 驱动的语义查询引擎，支持自然语言转 SQL 并执行。

## 版本

### V2 (推荐) - LangGraph Agent 架构
- 多轮对话支持
- Skills 模块化设计
- PostgreSQL 连接池
- 连接 Chat 接口，一次完成生成+执行

### V1 - 线性 Pipeline
- 自然语言 → SQL → 执行
- 需要分开调用 generate_sql 和 execute_sql

## 功能

### V2 新特性
- 🤖 **LangGraph Agent** - 智能工作流编排
- 💬 **多轮对话** - 支持上下文记忆
- 🔧 **Skills 系统** - 模块化 SQL 生成/校验/执行
- 🔄 **SQL 自愈** - 自动修复错误 SQL (开发中)
- 📊 **Schema RAG** - 向量检索相关表结构
- 🗃️ **多数据源** - PostgreSQL / HANA / Trino

### 核心能力
- 自然语言转 SQL
- SQL 安全校验（仅允许 SELECT）
- 多轮对话支持
- 中文/英文双语支持

## 快速开始

### 前置要求
- Python 3.10+
- PostgreSQL (测试数据库)
- Node.js + npm (前端)
- MiniMax API Key

### 1. 安装依赖

```bash
# Python 虚拟环境
cd Semantic-SQL-Agent
python -m venv venv
source venv/bin/activate

# 安装 Python 依赖
pip install -r app/requirements.txt
pip install psycopg2-binary langgraph langchain faiss-cpu

# 安装前端依赖
cd frontend
npm install
```

### 2. 配置环境变量

创建 `v2/.env` 文件：

```bash
MINIMAX_API_KEY=your_api_key_here
```

### 3. 启动服务

```bash
# 启动 V2 后端 (端口 8001)
cd Semantic-SQL-Agent
source venv/bin/activate
cd v2
PYTHONPATH=/path/to/project uvicorn api.server:app --reload --port 8001

# 启动前端 (端口 3000)
cd frontend
npm run dev
```

访问 http://localhost:3000

### 4. 测试数据库

已内置光伏行业测试数据 (PostgreSQL)：

```bash
# 连接测试数据库
docker exec -it postgres psql -U postgres -d sap_mock

# 查看表
\d
```

## API 接口

### V2 推荐接口 - /chat

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询销售订单，按客户分组统计金额"
  }'
```

响应：
```json
{
  "session_id": "xxx",
  "sql": "SELECT ...",
  "result": {
    "data": [...],
    "columns": [...],
    "row_count": 10
  },
  "error": null
}
```

### V1 兼容接口

```bash
# 生成 SQL
curl -X POST http://localhost:8001/api/generate_sql \
  -H "Content-Type: application/json" \
  -d '{"question": "查询客户"}'

# 执行 SQL
curl -X POST http://localhost:8001/api/execute_sql \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM md.kna1 LIMIT 10"}'
```

## 项目结构

```
Semantic-SQL-Agent/
├── v2/                      # V2 Agent 架构
│   ├── agent/
│   │   ├── state.py        # Agent 状态定义
│   │   └── graph.py        # LangGraph 工作流
│   ├── skills/
│   │   ├── generate_sql.py # SQL 生成
│   │   ├── validate_sql.py # SQL 校验
│   │   ├── execute_sql.py # SQL 执行
│   │   ├── repair_sql.py   # SQL 修复
│   │   └── route_datasource.py
│   ├── memory/
│   │   ├── conversation_memory.py
│   │   └── session_store.py
│   ├── schema/
│   │   ├── schema_loader.py
│   │   └── schema_retriever.py
│   ├── datasource/
│   │   ├── hana_executor.py
│   │   └── trino_executor.py
│   ├── prompts/
│   │   ├── generate_sql_prompt.py
│   │   └── repair_sql_prompt.py
│   ├── api/
│   │   └── server.py       # FastAPI 服务
│   └── config/
│       └── schema.yaml     # Schema 配置
├── app/                     # V1 原始代码
├── frontend/                # React 前端
└── docs/                   # 文档
```

## 测试数据说明

数据库 `sap_mock` 包含光伏串焊机行业模拟数据：

| Schema | 表 | 说明 |
|--------|-----|------|
| md | kna1, lfa1, mara, makt | 主数据 |
| sd | vbak, vbap, likp, lips, vbrk | 销售 |
| mm | ekko, ekpo, mseg, mkpf | 采购 |
| pp | afko, afpo, afvc | 生产 |
| im | mard, matdoc, mchb | 库存 |

## 技术栈

- **后端**: FastAPI, LangGraph, LangChain
- **前端**: React, Ant Design, Vite
- **数据库**: PostgreSQL, Trino, SAP HANA
- **LLM**: MiniMax API

## License

MIT
