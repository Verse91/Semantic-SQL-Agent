# Semantic-SQL-Agent V2 开发方案 (Develop Solution)

> 文档版本: 1.0
> 创建时间: 2026-03-11
> 状态: 已接收

---

## 1. 目标

将当前 Semantic-SQL-Agent（线性 SQL pipeline）升级为 v2 Data Agent 架构，新增能力：

- 多轮对话
- Skills / Tools 系统
- SQL 自动修复
- Schema 检索 (RAG)
- 多数据源路由
- LangGraph Workflow Agent

**保持现有 SQL 执行模块可复用。**

---

## 2. 当前系统改造原则

### 2.1 保留 (Keep)
- SQL executor
- HANA / Trino connector
- SQL validator

### 2.2 重构 (Refactor)
- QueryRouter
- 主执行流程

### 2.3 新增 (New)
- Agent Workflow
- Skills System
- Schema Retrieval
- Memory System

---

## 3. 新项目目录结构

```
semantic_sql_agent/
│
├── agent/
│   ├── graph.py           # LangGraph 工作流
│   ├── state.py           # Agent 状态定义
│   └── workflow.py        # 工作流编排
│
├── skills/
│   ├── base.py            # Skill 基类
│   ├── registry.py        # Skill 注册表
│   ├── generate_sql.py    # SQL 生成
│   ├── validate_sql.py    # SQL 校验
│   ├── execute_sql.py     # SQL 执行
│   ├── repair_sql.py      # SQL 自愈
│   ├── route_datasource.py  # 数据源路由
│   └── format_result.py   # 结果格式化
│
├── memory/
│   ├── conversation_memory.py  # 对话记忆
│   └── session_store.py        # 会话存储
│
├── schema/
│   ├── schema_loader.py    # Schema 加载
│   ├── schema_index.py     # Schema 索引
│   └── schema_retriever.py # Schema 检索 (RAG)
│
├── datasource/
│   ├── hana_executor.py   # HANA 执行器 (复用现有)
│   ├── trino_executor.py # Trino 执行器 (复用现有)
│   └── router.py          # 数据源路由
│
├── prompts/
│   ├── generate_sql_prompt.py
│   ├── repair_sql_prompt.py
│   └── system_prompt.py
│
└── api/
    └── server.py          # FastAPI 服务
```

---

## 4. 核心模块设计

### 4.1 Agent State

**文件**: `agent/state.py`

```python
from typing import TypedDict, List

class AgentState(TypedDict):
    user_query: str                    # 用户查询
    conversation_history: list          # 对话历史
    schema_context: str                 # Schema 上下文
    generated_sql: str                  # 生成的 SQL
    validated_sql: str                  # 校验后的 SQL
    datasource: str                     # 数据源
    execution_result: str               # 执行结果
    error: str                         # 错误信息
    retry_count: int                   # 重试次数
```

**State 在所有 workflow 节点之间传递。**

---

## 5. Skills System

### 5.1 Base Skill

**文件**: `skills/base.py`

```python
class BaseSkill:
    name = ""
    
    def run(self, state):
        raise NotImplementedError
```

### 5.2 Skill Registry

**文件**: `skills/registry.py`

```python
class SkillRegistry:
    def __init__(self):
        self.skills = {}
    
    def register(self, skill):
        self.skills[skill.name] = skill
    
    def get(self, name):
        return self.skills[name]
```

---

## 6. Skills 实现

### 6.1 generate_sql

| 项目 | 内容 |
|------|------|
| 输入 | user_query, schema_context, conversation_history |
| 输出 | generated_sql |
| 功能 | 调用 LLM 生成 SQL |

### 6.2 validate_sql

**检查项**:
- 禁止 DROP
- 禁止 DELETE
- 禁止 UPDATE

**返回**: validated_sql 或 error

### 6.3 route_datasource

**规则**:
- SAP 表 (MARA, VBAK, VBAP, BKPF...) → HANA
- 业务表 → Trino

**更新**: `state.datasource`

### 6.4 execute_sql

**流程**:
1. 根据 datasource 选择 executor
2. 调用 HANAExecutor 或 TrinoExecutor
3. 成功 → `state.execution_result`
4. 失败 → `state.error`

**复用现有**: `datasource/hana_executor.py`, `trino_service.py`

### 6.5 repair_sql

**触发条件**: execute_sql 失败

**输入**:
- original_sql
- error_message
- schema

**输出**: fixed_sql (LLM 生成)

**更新**: `state.generated_sql`

### 6.6 format_result

**功能**: 将 SQL 结果转换为 JSON / table 格式

---

## 7. Schema Retrieval (RAG)

### 7.1 目标

根据用户问题检索相关表结构，作为 SQL prompt 的上下文。

### 7.2 模块

| 模块 | 功能 |
|------|------|
| schema_loader | 加载表结构 |
| schema_index | 构建向量索引 |
| schema_retriever | 检索相关表 |

### 7.3 流程

```
user_query
    ↓
embedding (生成向量)
    ↓
vector search (FAISS)
    ↓
top_k tables
    ↓
schema_context
    ↓
用于 SQL prompt
```

### 7.4 向量库建议

- **FAISS** (Facebook)

---

## 8. Memory System

### 8.1 文件

**memory/conversation_memory.py**

### 8.2 存储内容

```python
{
    "session_id": "xxx",
    "history": [
        {"role": "user", "content": "查询库存"},
        {"role": "assistant", "content": "SELECT ..."}
    ],
    "last_sql": "SELECT ..."
}
```

### 8.3 多轮对话示例

**第一轮**:
- User: 查询库存
- Agent: SELECT ... (存历史)

**第二轮**:
- User: 只看上海仓
- 生成 SQL 时附带 history → "SELECT ... WHERE warehouse='上海'"

---

## 9. LangGraph Workflow

### 9.1 文件

**agent/graph.py**

### 9.2 节点

| 序号 | 节点 | 功能 |
|------|------|------|
| 1 | retrieve_schema | Schema 检索 |
| 2 | generate_sql | SQL 生成 |
| 3 | validate_sql | SQL 校验 |
| 4 | route_datasource | 数据源路由 |
| 5 | execute_sql | SQL 执行 |
| 6 | repair_sql | SQL 自愈 (可选) |
| 7 | format_result | 结果格式化 |

### 9.3 流程图

```
retrieve_schema
        ↓
generate_sql
        ↓
validate_sql
        ↓
route_datasource
        ↓
execute_sql
   ┌────┴────┐
   ↓          ↓
success    error
   ↓          ↓
format    repair_sql
 result    (retry)
              ↓
         execute_sql
```

---

## 10. Error Recovery (错误恢复)

### 10.1 条件分支

```python
workflow.add_conditional_edges(
    "execute_sql",
    check_error,
    {
        "success": "format_result",
        "error": "repair_sql"
    }
)
```

### 10.2 重试机制

- **最大重试次数**: `retry_count <= 2`
- **重试流程**: repair_sql → execute_sql

---

## 11. API 设计

### 11.1 文件

**api/server.py**

### 11.2 技术栈

- FastAPI

### 11.3 接口

**POST /chat**

请求:
```json
{
    "session_id": "xxx",
    "query": "查询上海仓库存"
}
```

流程:
```
load memory (session_id)
        ↓
invoke graph
        ↓
store history
        ↓
return result
```

---

## 12. Prompt 设计

### 12.1 目录

**prompts/**

### 12.2 文件

| 文件 | 用途 |
|------|------|
| generate_sql_prompt.py | SQL 生成提示词 |
| repair_sql_prompt.py | SQL 修复提示词 |
| system_prompt.py | 系统提示词 |

### 12.3 Prompt 包含内容

- schema_context
- conversation_history
- user_query

---

## 13. 升级执行步骤

### Phase 1: 基础结构

- [ ] agent/state - Agent 状态定义
- [ ] skills/base - Skill 基类
- [ ] skills/registry - Skill 注册表
- [ ] agent/graph - LangGraph 图定义

### Phase 2: 核心 Skills

- [ ] generate_sql - SQL 生成
- [ ] validate_sql - SQL 校验
- [ ] execute_sql - SQL 执行 (复用现有 executor)

### Phase 3: Schema Retrieval

- [ ] schema_loader - Schema 加载
- [ ] schema_index - 索引构建
- [ ] schema_retriever - 向量检索
- [ ] embedding 集成

### Phase 4: Error Recovery

- [ ] repair_sql - SQL 自动修复
- [ ] retry workflow - 重试工作流
- [ ] 错误处理逻辑

### Phase 5: Memory & API

- [ ] conversation_memory - 对话记忆
- [ ] session_store - 会话存储
- [ ] api/server - FastAPI 服务
- [ ] prompts - 提示词工程

---

## 14. 完成标准

系统应支持:

- [ ] 自然语言生成 SQL
- [ ] SQL 自动修复 (retry)
- [ ] 多轮对话
- [ ] Schema RAG 检索
- [ ] 多数据源执行 (HANA / Trino)
- [ ] JSON 结果输出

---

## 15. 代码规模

| 模块 | 预计行数 |
|------|----------|
| agent/ | ~150 |
| skills/ | ~400 |
| schema/ | ~200 |
| memory/ | ~100 |
| prompts/ | ~150 |
| api/ | ~200 |
| **总计** | **1200-1500 行** |

**不修改现有 executor 模块** (复用到新架构)

---

## 16. 依赖项

```txt
langgraph
langchain
langchain-community
faiss-cpu  # 向量检索
numpy
pydantic
fastapi
uvicorn
```

---

## 17. 复用现有模块

| 现有模块 | 用途 |
|----------|------|
| app/trino_service.py | Trino 执行 |
| app/datasource/hana_executor.py | HANA 执行 |
| app/sql_validator.py | SQL 校验逻辑 |
| app/config.py | 配置管理 |

---

*文档状态: 已完成，可开始实施*
