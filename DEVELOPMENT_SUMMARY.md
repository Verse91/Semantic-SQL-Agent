# Semantic-SQL-Agent V2 开发经验总结

> 日期: 2026-03-11
> 开发者: Claw + 靖达

---

## 📋 开发内容

### 1. V2 Agent 架构搭建
- LangGraph 工作流设计
- Skills 模块化 (generate_sql, validate_sql, execute_sql, repair_sql)
- Schema RAG 检索
- 对话记忆系统

### 2. 测试数据库
- PostgreSQL 创建 sap_mock 数据库
- 30+ 张表 (SD/MM/PP/IM/MD)
- 光伏串焊机行业测试数据

### 3. 前端升级
- 从分步接口 → /chat 单接口
- 支持多轮对话
- 简化用户体验

---

## 🚫 踩坑记录

### 1. Python 模块导入问题
**问题**: `No module named 'llm_service'`
**原因**: v2 作为子目录，import 路径不对
**解决**: 添加 sys.path.insert(0, project_root)

### 2. MiniMax API Key
**问题**: `MINIMAX_API_KEY not set`
**解决**: 创建 .env 文件 + python-dotenv 加载

### 3. Trino 无 PostgreSQL
**问题**: Trino 默认连接 MySQL，不是 PostgreSQL
**解决**: 直接用 psycopg2 连接 PostgreSQL

### 4. API 响应格式
**问题**: 前端期望 response.data.data.sql
**解决**: 统一响应格式 {success, data: {sql}, error}

### 5. CORS 问题
**问题**: 前端请求被阻止
**解决**: 添加 FastAPI CORS middleware

### 6. PostgreSQL 事务错误
**问题**: `current transaction is aborted`
**原因**: 错误后未正确回滚，连接状态损坏
**解决**: 使用连接池 + autocommit=True

### 7. autocommit 参数错误
**问题**: `invalid connection option "autocommit"`
**解决**: 使用 conn.set_session(autocommit=True)

---

## ✅ 做得好

1. **方案先行** - 先讨论方案再动手，减少返工
2. **渐进式开发** - 小步迭代，及时测试
3. **API 兼容** - 保留 V1 接口，减少前端改动
4. **问题沟通** - 及时告诉用户问题，共同解决

---

## 🔧 技术要点

### 连接池使用
```python
from psycopg2 import pool

self.pool = pool.ThreadedConnectionPool(
    minconn=1, maxconn=5,
    host="localhost", port=5432,
    database="sap_mock",
    user="postgres", password="postgres"
)
conn = self.pool.getconn()
conn.set_session(autocommit=True)
# 使用后归还
self.pool.putconn(conn)
```

### MiniMax API 调用
```python
url = "https://api.minimaxi.com/v1/text/chatcompletion_v2"
data = {
    "model": "MiniMax-M2.1",
    "messages": [{"role": "user", "content": prompt}],
    "temperature": 0.3
}
resp = requests.post(url, json=data, headers=headers, timeout=60)
```

### LangGraph 简单工作流
```python
workflow = StateGraph(AgentState)
workflow.add_node("retrieve_schema", retrieve_schema_node)
workflow.add_node("generate_sql", generate_sql_node)
# ... 更多节点
workflow.add_edge("retrieve_schema", "generate_sql")
# ...
workflow.compile()
```

---

## 📦 依赖清单

```
langgraph
langchain
langchain-community
faiss-cpu
numpy
psycopg2-binary
python-dotenv
fastapi
uvicorn
requests
```

---

## 📝 待优化

- [ ] SQL 自愈逻辑完善
- [ ] Schema 向量检索 (FAISS)
- [ ] 多数据源路由 (HANA/Trino)
- [ ] 前端界面美化

---

*感谢靖达今天的开发工作！🎉*
