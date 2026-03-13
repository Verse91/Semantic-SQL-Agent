# Semantic-SQL-Agent v2 扩展开发说明（FS 报表解析能力）

## 1 目标

在现有 Semantic-SQL-Agent v2（LangGraph + Skills 架构） 上新增 **FS（Functional Spec）报表解析能力**，支持：

- 上传报表说明文件（FS）
- 自动解析报表字段与指标
- 自动生成 Query Plan
- 自动生成 SQL
- 调用现有 SQL workflow 执行

支持复杂 BI 报表生成。

---

## 2 新功能流程

新增 workflow：

```
FS Upload
  ↓
FS Loader
  ↓
FS Parser
  ↓
Schema Retrieval
  ↓
Query Plan Generator
  ↓
Generate SQL
  ↓
Validate SQL
  ↓
Route Datasource
  ↓
Execute SQL
  ↓
Repair SQL (optional)
  ↓
Format Result
```

FS 输入将替代 user_query 进入 SQL 生成流程。

---

## 3 新增目录结构

在现有项目中新增：

```
documents/
  fs_loader.py
  fs_parser.py

skills/
  parse_fs.py
  generate_query_plan.py

prompts/
  parse_fs_prompt.py
  query_plan_prompt.py
```

---

## 4 FS Loader

**文件**: `documents/fs_loader.py`

**功能**: 读取用户上传文件

**支持类型**: txt, md, pdf, docx

**示例实现**:

```python
def load_fs(file_path):
    with open(file_path) as f:
        return f.read()
```

**扩展支持**: pypdf, python-docx

**输出**: fs_document

---

## 5 FS Parser Skill

**文件**: `skills/parse_fs.py`

**功能**: 将 FS 文档转换为结构化 JSON

**输入**: fs_document

**输出**: fs_json

**结构**:

```json
{
  "report_name": "",
  "tables": [],
  "dimensions": [],
  "metrics": [],
  "filters": []
}
```

使用 LLM 解析。

**Prompt 文件**: `prompts/parse_fs_prompt.py`

---

## 6 Query Plan Skill

**文件**: `skills/generate_query_plan.py`

**功能**: 根据 FS JSON 与 schema context 生成 Query Plan

**输入**: fs_json, schema_context

**输出**: query_plan

**结构**:

```json
{
  "tables": [],
  "joins": [],
  "metrics": [],
  "filters": [],
  "group_by": []
}
```

**Prompt 文件**: `prompts/query_plan_prompt.py`

---

## 7 SQL Generator 修改

**原逻辑**: `generate_sql(user_query)`

**修改为**: `generate_sql(query_plan)`

**Prompt 输入**: query_plan, schema_context

SQL 根据 Query Plan 生成。

---

## 8 LangGraph Workflow 修改

**新增节点**: load_fs, parse_fs, generate_query_plan

**更新 graph**:

```
load_fs
  ↓
parse_fs
  ↓
schema_retrieval
  ↓
generate_query_plan
  ↓
generate_sql
  ↓
validate_sql
  ↓
route_datasource
  ↓
execute_sql
```

**错误分支保持不变**:

```
execute_sql
  │
  ├ success → format_result
  │
  └ error → repair_sql → execute_sql
```

---

## 9 Agent State 修改

**文件**: `agent/state.py`

**新增字段**: fs_document, fs_json, query_plan

**完整 state 示例**:

```python
class AgentState(TypedDict):
    user_query: str
    fs_document: str
    fs_json: dict
    query_plan: dict
    schema_context: str
    generated_sql: str
    validated_sql: str
    datasource: str
    execution_result: str
    error: str
    retry_count: int
```

---

## 10 API 接口

**新增接口**: POST /upload_fs

**参数**: file, session_id

**返回**: query_result

**API 流程**:

```
upload file
  ↓
save file
  ↓
invoke workflow
  ↓
return result
```

---

## 11 Prompt 设计

**新增 Prompt**: parse_fs_prompt, query_plan_prompt

**Prompt 必须包含**: schema_context, fs_document

---

## 12 执行顺序

### Phase 1
- [x] 方案制定
- [ ] 实现 fs_loader
- [ ] 实现 parse_fs skill

### Phase 2
- [ ] 实现 generate_query_plan skill

### Phase 3
- [ ] 修改 generate_sql prompt

### Phase 4
- [ ] 修改 LangGraph workflow
- [ ] 修改 Agent state

### Phase 5
- [ ] 实现 upload_fs API

---

## 13 完成标准

系统必须支持：

1. [ ] 上传 FS 文档
2. [ ] 自动解析报表结构
3. [ ] 自动生成 Query Plan
4. [ ] 自动生成 SQL
5. [ ] 执行 SQL 返回结果
6. [ ] SQL 执行失败自动修复

---

## 14 新增代码规模

预计新增代码：≈600-800 行

现有 SQL 执行模块无需修改。
