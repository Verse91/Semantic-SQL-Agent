# Semantic-SQL-Agent v2 升级方案草案

> 草案来源: ChatGPT 升级建议
> 接收时间: 2026-03-11

---

## 1. 升级目标

- 支持多轮对话
- 支持 Skills / Tools
- 支持 SQL 自愈
- 支持多数据源
- 使用 LangGraph Workflow
- 与现有 Semantic-SQL-Agent 代码结构兼容

---

## 2. 总体架构

**核心原则**: Deterministic Data Agent

```
User Query
 │
 ▼
Conversation Memory
 │
 ▼
Schema Retrieval
 │
 ▼
Generate SQL
 │
 ▼
Validate SQL
 │
 ▼
Route Datasource
 │
 ▼
Execute SQL
 │
 ▼
Error ?
 ┌───┴────┐
 │        │
Repair SQL│
 │        │
 └──Retry─┘
 │
 ▼
Format Result
 │
 ▼
Return
```

LangGraph 用于管理节点、状态、分支和重试。

---

## 3. 项目目录结构

```
semantic_sql_agent_v2/
│
├── agent/
│   ├── graph.py          # LangGraph 工作流
│   ├── state.py          # Agent 状态定义
│   └── workflow.py       # 工作流编排
│
├── skills/
│   ├── base.py           # Skill 基类
│   ├── registry.py       # Skill 注册表
│   ├── generate_sql.py   # SQL 生成
│   ├── validate_sql.py   # SQL 校验
│   ├── execute_sql.py    # SQL 执行
│   ├── repair_sql.py     # SQL 自愈
│   ├── route_datasource.py  # 数据源路由
│   └── format_result.py  # 结果格式化
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
│   ├── hana_executor.py    # HANA 执行器
│   ├── trino_executor.py  # Trino 执行器
│   └── router.py           # 数据源路由
│
├── prompts/
│   ├── generate_sql_prompt.py
│   ├── repair_sqlrompt.py
│   └── system_prompt.py
│
├── utils/
│   ├── sql_parser.py
│   └── logger.py
│
└── api/
    ├── server.py
    └── chat_endpoint.py
```

---

## 4. Agent State 设计

```python
from typing import TypedDict, List, Optional

class AgentState(TypedDict):
    user_query: str
    conversation_history: List[str]
    schema_context: str
    generated_sql: Optional[str]
    validated_sql: Optional[str]
    datasource: Optional[str]
    execution_result: Optional[str]
    error: Optional[str]
    retry_count: int
```

---

## 5. Skills System

### 统一接口

```python
class BaseSkill:
    name = ""
    def run(self, state):
        raise NotImplementedError
```

### Skill Registry

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

## 6. 核心 Skills

| Skill | 功能 | 输入 | 输出 |
|-------|------|------|------|
| generate_sql | SQL 生成 | user_query, schema_context, history | generated_sql |
| validate_sql | SQL 校验 | generated_sql | validated_sql / error |
| route_datasource | 数据源路由 | validated_sql | datasource |
| execute_sql | SQL 执行 | validated_sql, datasource | result / error |
| repair_sql | SQL 自愈 | error, original_sql, schema | fixed_sql |
| format_result | 结果格式化 | execution_result | formatted_output |

### SQL 自愈场景
- column not found
- syntax error
- table not exist

---

## 7. Schema Retrieval (RAG)

**重要性**: SQL Agent 成功的关键

```
User Query
    ↓
Embedding
    ↓
Vector Search (top k tables)
    ↓
输出: table schema + column schema + description
    ↓
作为 SQL prompt context
```

---

## 8. LangGraph Workflow

```python
from langgraph.graph import StateGraph

workflow = StateGraph(AgentState)

# 添加节点
workflow.add_node("retrieve_schema", retrieve_schema)
workflow.add_node("generate_sql", generate_sql)
workflow.add_node("validate_sql", validate_sql)
workflow.add_node("route_datasource", route_datasource)
workflow.add_node("execute_sql", execute_sql)
workflow.add_node("repair_sql", repair_sql)
workflow.add_node("format_result", format_result)

# 条件边 - 错误处理
workflow.add_conditional_edges(
    "execute_sql",
    check_error,
    {
        "success": "format_result",
        "error": "repair_sql"
    }
)
```

---

## 9. 多轮对话 Memory

```python
# 存储结构
session_id:
  - history: [{"role": "user", "content": "..."}, {"role": "agent", "content": "..."}]
  - last_sql: "SELECT ..."
```

**第二轮示例**:
```
User: 查询库存
Agent: SQL_1

User: 只看上海仓
→ Prompt: history + "只看上海仓" + schema_context
```

---

## 10. API 层

```python
@app.post("/chat")
def chat(req):
    state = {
        "user_query": req.query,
        "conversation_history": memory.get(req.session),
        "retry_count": 0
    }
    result = graph.invoke(state)
    return result
```

---

## 11. 完整执行流程

```
User
    ↓
API
    ↓
LangGraph
    ↓
retrieve_schema
    ↓
generate_sql
    ↓
validate_sql
    ↓
route_datasource
    ↓
execute_sql
    ↓
repair_sql (optional)
    ↓
format_result
    ↓
response
```

---

## 12. 能力对比 (V1 vs V2)

| 功能 | V1 | V2 |
|------|----|----|
| 多轮对话 | ❌ | ✅ |
| Skills 系统 | ❌ | ✅ |
| SQL 自愈 | ❌ | ✅ |
| Schema 检索 (RAG) | ❌ | ✅ |
| 多数据源 | ⚠️ | ✅ |
| Workflow Agent | ❌ | ✅ |

---

## 13. 工程规模预估

| 模块 | 代码行数 |
|------|----------|
| Agent Graph | 200 |
| Skills | 600 |
| Schema RAG | 300 |
| Memory | 100 |
| API | 200 |
| **总计** | **≈1400 行** |

---

## 14. 实施计划

### Phase 1: 基础架构 (1周)
- [ ] 项目结构搭建
- [ ] Agent State 定义
- [ ] LangGraph 基础框架
- [ ] Skills 基类和注册表

### Phase 2: 核心 Skills (1周)
- [ ] generate_sql skill
- [ ] validate_sql skill
- [ ] execute_sql skill
- [ ] 数据源路由

### Phase 3: 高级能力 (1周)
- [ ] repair_sql (SQL 自愈)
- [ ] schema_retriever (RAG)
- [ ] conversation_memory

### Phase 4: 集成测试 (3-5天)
- [ ] 端到端测试
- [ ] 错误处理
- [ ] 性能优化

---

## 15. 风险评估

| 风险 | 影响 | 应对方案 |
|------|------|----------|
| LangGraph 版本兼容性 | 中 | 锁定版本 |
| Schema RAG 效果 | 高 | 人工评测 + 迭代 |
| SQL 自愈成功率 | 中 | 多轮重试 + 降级 |
| 向后兼容性 | 低 | 保留 V1 API |

---

## 16. 未来可扩展能力

- [ ] BI 图表生成 (chart_generator skill)
- [ ] Python 数据分析 (python_executor)
- [ ] 报表保存 (report_builder)
- [ ] 自动 Query Planning (多步骤查询)

---

*文档状态: 已接收，待评审*
