# Semantic-SQL-Agent

本地 AI 驱动的语义查询引擎，支持自然语言转 SQL 并执行。

## ✨ 最新特性 (2026-03)

### Trace Logging System ✅ 新增
- 完整执行路径追踪
- 每个步骤输入输出可视化
- 前端 Trace 面板展示
- 向量检索相似度分数

### 向量检索 ✅ 新增
- Schema 向量索引 (FAISS)
- Sentence-Transformers  embeddings
- 表描述语义匹配

---

## 版本

### V2 (推荐) - LangGraph Agent 架构
- 🤖 **LangGraph Agent** - 智能工作流编排
- 💬 **多轮对话** - 支持上下文记忆
- 🔧 **Skills 系统** - 模块化 SQL 生成/校验/执行
- 📊 **Trace Logging** - 完整执行路径追踪
- 📈 **向量检索** - Schema 语义匹配
- 🔄 **SQL 自愈** - 自动修复错误 SQL

### V1 - 线性 Pipeline (遗留)
- 自然语言 → SQL → 执行
- 位于 `v1/` 目录

---

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
python -m venv venv2
source venv2/bin/activate

# 安装 Python 依赖
pip install -r v2/requirements.txt

# 向量检索依赖
pip install sentence-transformers faiss-cpu numpy

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
# 启动 PostgreSQL (如果使用 Docker)
docker start postgres

# 启动 V2 后端 (端口 8001)
cd Semantic-SQL-Agent
source venv2/bin/activate
cd v2
PYTHONPATH=/Users/wangjd/Semantic-SQL-Agent \
MINIMAX_API_KEY=your_key \
uvicorn api.server:app --host 0.0.0.0 --port 8001

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

---

## Trace Logging 使用

每条查询都会记录完整执行路径：

1. **schema_retriever** - 向量检索相关表
2. **generate_sql** - SQL 生成
3. **validate_sql** - SQL 校验
4. **route_datasource** - 数据源路由
5. **execute_sql** - SQL 执行

查看 trace：
```bash
# 列出 traces
curl http://localhost:8001/api/traces

# 查看单条 trace
curl http://localhost:8001/api/traces/{trace_id}
```

前端面板：查询结果下方点击 "Show Trace"

---

## API 接口

### V2 推荐接口 - /chat

```bash
curl -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "查询销售订单，按客户分组统计金额"}'
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

---

## 项目结构

```
Semantic-SQL-Agent/
├── v2/                      # V2 Agent 架构 (当前开发)
│   ├── agent/               # LangGraph
│   │   ├── state.py        # Agent 状态
│   │   └── graph.py        # 工作流图
│   ├── skills/              # Skills 系统
│   │   ├── generate_sql.py # SQL 生成
│   │   ├── validate_sql.py # SQL 校验
│   │   ├── execute_sql.py  # SQL 执行
│   │   ├── repair_sql.py   # SQL 修复
│   │   └── route_datasource.py
│   ├── tracing/             # Trace Logging 系统
│   │   ├── trace_models.py
│   │   ├── trace_logger.py
│   │   ├── trace_manager.py
│   │   └── trace_storage.py
│   ├── schema/              # Schema RAG
│   │   ├── schema_loader.py
│   │   ├── schema_retriever.py
│   │   ├── schema_index.py
│   │   └── schema_embedding.py  # 向量嵌入
│   ├── memory/              # 对话记忆
│   ├── prompts/             # 提示词
│   ├── datasource/          # 数据源
│   └── api/
│       └── server.py        # FastAPI 服务
├── v1/                      # V1 遗留代码
├── frontend/                 # React 前端
│   └── src/
│       └── components/
│           └── TracePanel.jsx  # Trace 展示
└── traces/                  # Trace 日志
    └── YYYY-MM-DD/
        └── trace_{id}.json
```

---

## 测试数据

数据库 `sap_mock` 包含光伏串焊机行业模拟数据：

| Schema | 表 | 说明 |
|--------|-----|------|
| md | kna1, lfa1, mara, makt | 主数据 |
| sd | vbak, vbap, likp, lips, vbrk | 销售 |
| mm | ekko, ekpo, mseg, mkpf | 采购 |
| pp | afko, afpo, afvc | 生产 |
| im | mard, matdoc, mchb | 库存 |

---

## 技术栈

- **后端**: FastAPI, LangGraph, LangChain
- **前端**: React, Ant Design, Vite
- **数据库**: PostgreSQL, Trino, SAP HANA
- **LLM**: MiniMax API
- **向量**: sentence-transformers, FAISS

---

## License

MIT
