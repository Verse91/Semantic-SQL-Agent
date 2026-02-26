# Semantic-SQL-Agent

A local AI-powered semantic query engine that converts natural language into secure SQL and executes it via Trino.

## V0.3 新功能 (Report DSL)

- 支持自然语言查询
- 支持 Report DSL 报表定义（Markdown 格式）
- 结构化报表生成

## 功能

- 接收自然语言问题
- 调用 LLM 生成 Trino SQL
- 校验 SQL 安全性（只允许 SELECT）
- 执行查询并返回 JSON 结果
- 支持跨库查询（MySQL + PostgreSQL）
- Markdown 报表定义解析

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
```

## 运行

```bash
cd app
uvicorn app.main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

服务启动后访问 http://localhost:3000

## API

### 自然语言查询

```bash
curl -X POST http://localhost:8000/api/generate_sql \
  -H "Content-Type: application/json" \
  -d '{"question": "查询前10个物料"}'
```

### 上传 Markdown 报表定义

```bash
curl -X POST http://localhost:8000/api/upload_report_spec \
  -F "file=@report.md"
```

### 从 ReportSpec 生成 SQL

```bash
curl -X POST http://localhost:8000/api/generate_sql_from_spec \
  -H "Content-Type: application/json" \
  -d '{"report_spec": {...}}'
```

### 执行 SQL

```bash
curl -X POST http://localhost:8000/api/execute_sql \
  -H "Content-Type: application/json" \
  -d '{"sql": "SELECT * FROM mara LIMIT 10"}'
```

## Report DSL 格式

```markdown
# 报表名称
## 数据源
表1
表2
## 关联关系
table1.id = table2.id
## 统计指标
- 指标名: sum(table.field)
## 分组维度
- dimension1
## 过滤条件
- field = 'value'
```

## 项目结构

```
Semantic-SQL-Agent/
├── app/
│   ├── main.py
│   ├── api/
│   │   ├── routes.py
│   │   └── upload_report.py
│   ├── services/
│   │   ├── llm_service.py
│   │   ├── sql_validator.py
│   │   ├── trino_service.py
│   │   ├── markdown_parser.py
│   │   └── report_sql_generator.py
│   └── models/
│       ├── report_spec.py
│       └── request_models.py
├── frontend/
│   └── src/
│       └── App.jsx
└── examples/
    └── 物料汇总报表.md
```
