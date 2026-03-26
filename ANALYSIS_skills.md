# Skills 分析报告

## 1. Skill 清单

| Skill | 文件 | 行数 | 状态 | 描述 |
|-------|------|------|------|------|
| `parse_fs` | parse_fs.py | 121 | ✅ 正常 | 将 FS 报表文档解析为结构化 JSON |
| `generate_query_plan` | generate_query_plan.py | 123 | ✅ 正常 | 根据 FS JSON 生成查询计划 |
| `generate_sql` | generate_sql.py | 105 | ✅ 正常 | 将自然语言或 Query Plan 转换为 SQL |
| `validate_sql` | validate_sql.py | 59 | ✅ 正常 | 校验 SQL 安全性，仅允许 SELECT |
| `route_datasource` | route_datasource.py | 65 | ✅ 正常 | 根据表名前缀路由数据源 |
| `execute_sql` | execute_sql.py | 119 | ⚠️ 需优化 | 执行 SQL 并返回结果 |
| `repair_sql` | repair_sql.py | 69 | ⚠️ 需优化 | 根据错误信息自动修复 SQL |
| `format_result` | format_result.py | 49 | ✅ 正常 | 将 SQL 执行结果格式化为 JSON |

**基础类**: `BaseSkill` (base.py) — 所有 Skill 继承，接口统一 ✅

---

## 2. 架构分析

### 2.1 单例模式问题（严重）

**所有 8 个 Skill 都用模块级单例：**
```python
# 每个 skill 文件底部
execute_sql_skill = ExecuteSQLSkill()
format_result_skill = FormatResultSkill()
generate_query_plan_skill = GenerateQueryPlanSkill()
...
```

**问题**：
- `execute_sql.py` 第 119 行的连接池是**跨请求共享**的，高并发下会出问题
- 无法为不同请求创建独立的 skill 实例
- LangGraph workflow 中每个 node 应该用 factory 创建新实例

**正确做法**：
```python
def get_execute_sql_skill() -> ExecuteSQLSkill:
    return ExecuteSQLSkill()  # 每次创建新实例

def get_generate_sql_skill() -> GenerateSQLSkill:
    return GenerateSQLSkill()
```

### 2.2 Registry 未被使用

`registry.py` 定义了 `SkillRegistry`，但 **workflow 完全没用到** — skills 直接在 `graph.py` 里 import 单例。Registry 成了死代码。

### 2.3 统一接口 ✅

所有 skills 都继承 `BaseSkill`，都有 `run(state: Dict) -> Dict` 方法，接口一致。

---

## 3. 各 Skill 代码质量问题

### `execute_sql.py` — ⚠️ 高优先级
- **单例连接池**（119 行）：`psycopg2.pool.ThreadedConnectionPool` 是模块级共享的，并发请求会竞争连接
- **无连接超时配置**：连接池参数（minconn/maxconn）都是默认值
- **异常处理缺失**：如果数据库不可达，整个 skill 会崩溃

### `repair_sql.py` — ⚠️ 中优先级
- **错误信息提取不完整**：第 40 行用正则提取错误位置，但很多数据库错误格式不匹配
- **未限制修复次数**：理论上可以无限循环修复（虽然有 retry_count 保护，但 repair_sql 本身不检查）
- **无 LLM 调用失败处理**：如果 MiniMax API 挂了，没有 fallback

### `generate_sql.py` — ⚠️ 中优先级
- **无 LLM 超时设置**：`llm_service` 调用没有 timeout 参数
- **无重试机制**：LLM 调用失败直接报错，没有重试
- **SQL 注入风险**：prompt 构建用的是 f-string，如果 user_query 包含恶意内容可能影响 prompt injection（但实际 SQL 执行有 validate_sql 保护）

### `validate_sql.py` — ✅ 低优先级
- **关键字列表不完整**：没有禁止 `grant`, `revoke`, `merge`, `commit`, `rollback` 等
- **正则匹配太简单**：`re.search(r'\bDROP\b', sql, re.IGNORECASE)` 只匹配大写 word boundary，MySQL 下可能绕过

### `route_datasource.py` — ✅ 低优先级
- **SAP 表前缀硬编码**：第 27-31 行的前缀列表可能不完整
- **无匹配时默认 PostgreSQL**：可能不适合 SAP HANA 等其他数据源

### `parse_fs.py` — ✅ 低优先级
- **正则依赖**：用正则解析 FS 文档，格式变化就会坏
- **无文件大小限制**：如果 fs_document 太大，可能 OOM

### `format_result.py` — ✅ 好
- 问题最少，有基本的空值处理

### `generate_query_plan.py` — ✅ 好
- 结构清晰，错误处理到位

---

## 4. Workflow 集成状态

| Skill | 在 Workflow 中使用 | 调用位置 |
|-------|-------------------|----------|
| `parse_fs` | ✅ | `parse_fs_node` → `parse_fs_skill.run(state)` |
| `generate_query_plan` | ✅ | `generate_query_plan_node` |
| `generate_sql` | ✅ | `generate_sql_node` |
| `validate_sql` | ✅ | `validate_sql_node` |
| `route_datasource` | ✅ | `route_datasource_node` |
| `execute_sql` | ✅ | `execute_sql_node` |
| `repair_sql` | ✅ | `repair_sql_node` |
| `format_result` | ✅ | `format_result_node` |

**结论**：所有 8 个 skills 都被使用，没有孤儿 skill。Registry 虽然没用到但 skills 本身都在被调用。

---

## 5. Top 5 改进建议

### 🔴 P0 — `execute_sql` 单例连接池必须修复

```python
# execute_sql.py 改动：
# 删除底部单例：
# execute_sql_skill = ExecuteSQLSkill()

# 改用 factory 函数：
def get_execute_sql_skill() -> ExecuteSQLSkill:
    return ExecuteSQLSkill()

# 同时 graph.py 中的 node 也需要改用 factory
```

### 🟠 P1 — 所有 Skill 的 LLM 调用加 timeout 和重试

`generate_sql.py` 和 `repair_sql.py` 的 LLM 调用都没有超时：
```python
# 当前
result = llm_service.chat(prompt)

# 应该改为
from functools import timeout import Timeout
try:
    result = timeout(30)(llm_service.chat)(prompt)  # 30秒超时
except TimeoutError:
    state["error"] = "LLM 调用超时"
```

### 🟡 P2 — `validate_sql` 补充禁止关键字

补充以下关键字到 FORBIDDEN_KEYWORDS：
```python
"grant", "revoke", "merge", "commit", "rollback", 
"deny", "execute", "call", "xp_", "sp_"
```

### 🟡 P3 — `repair_sql` 加修复次数限制

```python
# 在 run() 开头加
if state.get("repair_attempt", 0) >= 3:
    state["error"] = "SQL 修复次数超限"
    return state
state["repair_attempt"] = state.get("repair_attempt", 0) + 1
```

### 🟢 P4 — 清理未使用的 Registry 或接入 workflow

两个选择：
1. **删除** `registry.py` — 如果确定不用
2. **接入** — 让 workflow 从 registry 获取 skill，而不是直接 import 单例

---

## 6. 总结

| 维度 | 评分 | 说明 |
|------|------|------|
| 接口一致性 | ✅ 9/10 | 全部继承 BaseSkill |
| 代码复用 | ⚠️ 6/10 | 有重复的 sys.path.insert 和 tracing import |
| 错误处理 | ⚠️ 5/10 | 大部分 skill 无 try/catch |
| 并发安全 | 🔴 3/10 | execute_sql 单例连接池是定时炸弹 |
| 可维护性 | ⚠️ 7/10 | 代码清晰，但单例模式埋隐患 |

**最大风险**：`execute_sql.py` 的单例连接池在高并发下会出问题，必须优先修复。
