# Semantic-SQL-Agent

本地 AI 驱动的语义查询引擎，支持自然语言转 SQL 并执行。

## ✨ 最新特性 (2026-03)

### SQL 自愈机制 ✅ 新增
- execute_sql 失败后自动调用 repair_sql 修复 SQL
- 最多重试 2 次（3 次执行机会）
- 基于 MiniMax LLM 的 SQL 修复

### Schema 查询缓存 ✅ 新增
- 同进程内相同 query 命中缓存，避免重复向量搜索
- 提升响应速度

### 用户友好错误消息 ✅ 新增
- 数据库连接失败、LLM 超时、SQL 语法错误等分类处理
- 不暴露内部实现细节
- 返回中文提示

### Trace Logging System
- 完整执行路径追踪（13 步 workflow）
- 前端 Trace 面板展示，支持按日期筛选
- 支持 /chat 和 /api/upload_fs 双端点

### 向量检索
- Schema 向量索引 (FAISS)
- Sentence-Transformers embeddings
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

# 启动 V2 后端 (端口 8000)
cd Semantic-SQL-Agent
source venv2/bin/activate
cd v2
PYTHONPATH=/Users/wangjd/Semantic-SQL-Agent \
MINIMAX_API_KEY=your_key \
uvicorn api.server:app --host 0.0.0.0 --port 8000

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
# 列出最近7天的traces（默认）
curl http://localhost:8000/api/traces?limit=20

# 查看单条 trace（需指定trace创建日期）
curl http://localhost:8000/api/traces/{trace_id}?date=2026-03-26
```

前端面板：查询结果下方点击 "Show Trace"

---

## API 接口

### V2 推荐接口 - /chat

```bash
curl -X POST http://localhost:8000/chat \
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
│   │   ├── state.py        # Agent 状态定义
│   │   └── graph.py        # 工作流图（13步）
│   ├── skills/              # Skills 系统（8个skill）
│   │   ├── parse_fs.py         # FS报表解析
│   │   ├── generate_query_plan.py # 查询计划生成
│   │   ├── generate_sql.py      # SQL生成
│   │   ├── validate_sql.py      # SQL校验
│   │   ├── route_datasource.py # 数据源路由
│   │   ├── execute_sql.py       # SQL执行（factory模式）
│   │   ├── repair_sql.py       # SQL自愈修复（带重试）
│   │   └── format_result.py    # 结果格式化
│   ├── tracing/             # Trace Logging 系统
│   ├── schema/              # Schema RAG（含查询缓存）
│   │   ├── schema_retriever.py # 向量检索+缓存
│   │   └── schema_embedding.py # 向量嵌入
│   ├── memory/              # 对话记忆
│   ├── prompts/             # 提示词模板
│   ├── documents/           # FS文档加载
│   └── api/
│       └── server.py        # FastAPI 服务
├── v1/                      # V1 遗留代码
├── frontend/                 # React 前端
│   └── src/
│       └── components/
│           └── TracePanel.jsx  # Trace 展示
└── traces/                  # Trace 日志（已加入.gitignore）
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
