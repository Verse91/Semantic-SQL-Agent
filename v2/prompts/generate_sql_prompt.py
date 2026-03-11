"""
SQL 生成 Prompt
"""
from typing import List, Dict


def build_generate_sql_prompt(
    user_query: str,
    schema_context: str = "",
    conversation_history: List[Dict] = None
) -> str:
    """
    构建 SQL 生成 prompt
    
    Args:
        user_query: 用户查询
        schema_context: Schema 上下文
        conversation_history: 对话历史
        
    Returns:
        prompt 字符串
    """
    history_text = ""
    if conversation_history:
        history_text = "\n\n对话历史:\n"
        for msg in conversation_history[-4:]:  # 最近 4 条
            role = msg.get("role", "user")
            content = msg.get("content", "")
            history_text += f"{role}: {content}\n"
    
    prompt = f"""你是一个专业SQL数据分析师。

已知表结构：
{schema_context}
{history_text}

规则：
1. 只允许生成 SELECT 查询
2. 禁止 DROP、DELETE、UPDATE、INSERT、ALTER、TRUNCATE
3. 字段名和别名只能用英文
4. 只返回SQL语句，不要任何解释

用户问题：{user_query}

只返回SQL。"""
    
    return prompt
