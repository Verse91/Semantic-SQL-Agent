# Semantic-SQL-Agent

A local AI-powered semantic query engine that converts natural language into secure SQL and executes it via Trino.

## 功能

- 接收自然语言问题
- 调用 LLM 生成 Trino SQL
- 校验 SQL 安全性（只允许 SELECT）
- 执行查询并返回 JSON 结果
- 支持跨库查询（MySQL + PostgreSQL）

## 安装

```bash
cd app
pip install -r requirements.txt
```

## 配置

设置环境变量：

```bash
# Trino 配置
export TRINO_HOST=localhost
export TRINO_PORT=8080
export TRINO_USER=admin
export TRINO_CATALOG=mysql
export TRINO_SCHEMA=sap

# OpenClaw API 配置
export OPENCLOW_API_URL=http://localhost:18789
export OPENCLOW_API_KEY=your_api_key_if_needed
```

## 运行

```bash
cd app
uvicorn app.main:app --reload --port 8000
```

服务启动后访问 http://localhost:8000/docs 查看 API 文档。

## API

### POST /chat-query

```bash
curl -X POST http://localhost:8000/chat-query \
  -H "Content-Type: application/json" \
  -d '{"message": "查询mara表中所有物料"}'
```

响应：

```json
{
  "sql": "SELECT * FROM mara",
  "data": [
    {"matnr": "10000001", "mtart": "ROH", ...}
  ],
  "error": null
}
```

## 测试

### 测试1：正常查询

```bash
curl -X POST http://localhost:8000/chat-query \
  -H "Content-Type: application/json" \
  -d '{"message": "查询mara表中所有物料"}'
```

预期：返回 SQL 和数据

### 测试2：恶意指令

```bash
curl -X POST http://localhost:8000/chat-query \
  -H "Content-Type: application/json" \
  -d '{"message": "删除mara表"}'
```

预期：校验失败，返回 error

## 项目结构

```
ai-sql-agent/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 入口
│   ├── config.py        # 配置
│   ├── llm_service.py   # LLM 调用
│   ├── sql_validator.py # SQL 校验
│   ├── trino_service.py # Trino 执行
│   └── requirements.txt
└── README.md
```
