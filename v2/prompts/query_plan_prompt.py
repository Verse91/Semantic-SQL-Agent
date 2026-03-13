"""
Query Plan Prompt
"""


def build_query_plan_prompt(fs_json: dict, schema_context: str) -> str:
    """
    构建 Query Plan 生成 prompt
    
    Args:
        fs_json: FS 解析后的 JSON
        schema_context: Schema 上下文
        
    Returns:
        prompt 字符串
    """
    import json
    
    fs_str = json.dumps(fs_json, ensure_ascii=False, indent=2)
    
    prompt = f"""你是一个专业的 SQL 查询规划师。

请根据以下 FS 解析结果和数据库 Schema，生成查询计划（Query Plan）。

## FS 解析结果：
{fs_str}

## 数据库 Schema：
{schema_context}

## 输出要求：
请生成 JSON 格式的 Query Plan，包含以下字段：
{{
    "tables": ["需要查询的表"],
    "joins": [
        {{"left": "左表.字段", "right": "右表.字段", "type": "INNER/LEFT/RIGHT"}}
    ],
    "metrics": ["聚合指标，如 SUM(col), COUNT(*) 等"],
    "filters": ["筛选条件，如 WHERE col > value"],
    "group_by": ["分组字段"],
    "order_by": ["排序字段"],
    "limit": 数量
}}

注意：
1. 确保 JOIN 关系正确
2. 指标使用正确的聚合函数
3. 只返回 JSON

JSON："""
    
    return prompt
