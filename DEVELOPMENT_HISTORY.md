# Semantic-SQL-Agent 开发历史

## 项目概述

- **项目名称**: Semantic-SQL-Agent
- **GitHub**: https://github.com/Verse91/Semantic-SQL-Agent
- **作者**: wangjd
- **功能**: 自然语言转 SQL 查询引擎，通过 Trino 执行，支持跨库查询

---

## 版本历史

### V0.1 - MVP (2026-02-25)
**Commit**: `3255ca5f`

**功能**:
- 自然语言转 SQL (通过 LLM)
- SQL 安全校验 (仅允许 SELECT)
- Trino 查询执行
- 支持 MySQL + PostgreSQL 跨库查询

**文件变更**:
- `app/config.py` - 配置管理
- `app/llm_service.py` - LLM 调用
- `app/sql_validator.py` - SQL 校验
- `app/trino_service.py` - Trino 执行器
- `app/main.py` - FastAPI 入口

---

### V0.2 - Query Studio (2026-02-26)
**Commit**: `75efa638`

**功能**:
- 新增 API: `generate_sql`, `execute_sql`
- React 前端 (Ant Design)
- 自然语言转 SQL
- SQL 校验与执行
- 结果表格展示

**新增文件**:
- `app/api/routes.py` - API 路由
- `frontend/` - React 前端项目

---

### V0.3 - Report DSL (2026-02-26)
**Commit**: `5b2a0e63`

**功能**:
- Markdown 报表定义解析 (ReportSpec)
- 从 ReportSpec 生成 SQL
- 新增 `upload_report` API
- 前端模式选择器
- 示例 Markdown 文件

**新增文件**:
- `app/api/upload_report.py`
- `app/models/report_spec.py`
- `app/services/markdown_parser.py`
- `app/services/report_sql_generator.py`
- `examples/物料汇总报表.md`

**代码统计**: 723 行新增, 74 行修改

---

### V0.3.1 - SAP HANA 支持 (2026-03-07)
**Commit**: `0641fd34`

**功能**:
- SAP HANA JDBC 查询支持
- Query Router 自动路由
- 自动检测 SAP 表 (MARA, VBAK, VBAP 等)
- SAP 表查询路由到 HANA
- 其他查询继续使用 Trino

**新增文件**:
- `app/datasource/__init__.py`
- `app/datasource/hana_executor.py` - HANA JDBC 执行器
- `app/datasource/router.py` - 查询路由器
- `app/datasource_integration.py` - 数据源集成
- `config/database.yaml` - HANA 配置
- `drivers/README.md` - JDBC 驱动说明

**代码统计**: 565 行新增

---

## 技术架构

### 当前架构
```
用户请求 → FastAPI → routes.py
                        ↓
              ┌─────────┴─────────┐
              ↓                   ↓
        llm_service.py      datasource/router.py
        (SQL生成)            (多数据源路由)
              ↓                   ↓
        sql_validator      ┌──────┴──────┐
        (SQL校验)          ↓             ↓
                          ↓             ↓
                    hana_executor   trino_service
                    (HANA查询)      (Trino查询)
```

### 数据源路由规则
- **SAP 表** (MARA, VBAK, VBAP, BKPF, BSEG, EKKO, EKPO, LFA1, KNA1, MAKT, T001, T001W, T003T) → HANA
- **其他表** → Trino (MySQL/PostgreSQL)

---

## 依赖项

### Python
- fastapi
- uvicorn
- trino
- requests
- pydantic
- pyyaml
- jpype1 (HANA JDBC 支持)

### Frontend
- React
- Ant Design
- Vite

---

## 本地运行

```bash
# 后端
cd app
pip install -r requirements.txt
PYTHONPATH=/path/to/project uvicorn app.main:app --reload --port 8000

# 前端
cd frontend
npm install
npm run dev
```

---

## API 端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/generate_sql` | POST | 自然语言生成 SQL |
| `/api/execute_sql` | POST | 执行 SQL |
| `/api/upload_report_spec` | POST | 上传 Markdown 报表定义 |
| `/api/generate_sql_from_spec` | POST | 从 ReportSpec 生成 SQL |

---

## 待办事项 (Agent 化改造)

- [ ] 模块 Skill 化 (sql-generator, sql-validator, datasource-router)
- [ ] 引入 Agent 编排层
- [ ] 多轮对话/上下文支持
- [ ] 错误自愈能力
- [ ] Skill 触发优化

---

*最后更新: 2026-03-11*
