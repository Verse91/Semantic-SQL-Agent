from typing import List, Dict, Any
from ..models.report_spec import ReportSpec, Metric


def generate_sql_from_report_spec(report_spec: ReportSpec) -> str:
    """
    根据 ReportSpec 生成 SQL
    
    SQL 框架：
    SELECT 
        dimensions,
        metrics
    FROM tables
    JOIN joins
    WHERE filters
    GROUP BY dimensions
    LIMIT 1000
    """
    # 构建 SELECT 部分
    select_parts = []
    
    # 添加维度
    for dim in report_spec.dimensions:
        select_parts.append(dim)
    
    # 添加指标
    for metric in report_spec.metrics:
        # 处理表达式中的字段名
        expr = metric.expression
        # 使用别名
        select_parts.append(f"{expr} AS {metric.name}")
    
    select_clause = ",\n    ".join(select_parts)
    
    # FROM 部分 - 第一个表作为主表
    main_table = report_spec.tables[0] if report_spec.tables else "unknown"
    from_clause = main_table
    
    # JOIN 部分
    if report_spec.joins:
        join_parts = []
        for join_cond in report_spec.joins:
            # 简化处理：假设是简单的 ON 条件
            if '=' in join_cond:
                parts = join_cond.split('=')
                if len(parts) == 2:
                    left = parts[0].strip()
                    right = parts[1].strip()
                    join_parts.append(f"JOIN {get_table_from_field(left)} ON {left} = {right}")
        from_clause += "\n" + "\n".join(join_parts)
    
    # WHERE 部分
    where_parts = []
    for filter_cond in report_spec.filters:
        # 简单处理：直接添加条件
        where_parts.append(filter_cond)
    
    where_clause = ""
    if where_parts:
        where_clause = "\nWHERE " + "\n    AND ".join(where_parts)
    
    # GROUP BY 部分
    group_by_clause = ""
    if report_spec.dimensions:
        group_by_clause = "\nGROUP BY " + ", ".join(report_spec.dimensions)
    
    # 构建完整 SQL
    sql = f"""SELECT 
    {select_clause}
FROM {from_clause}{where_clause}{group_by_clause}
LIMIT 1000"""
    
    return sql


def get_table_from_field(field: str) -> str:
    """从字段名提取表名"""
    if '.' in field:
        return '.'.join(field.split('.')[:-1])
    return field


def generate_sql_with_llm_assist(report_spec: ReportSpec, original_markdown: str = "") -> Dict[str, Any]:
    """
    使用 LLM 辅助生成优化的 SQL
    
    仅在需要优化格式或处理函数兼容性时调用 LLM
    """
    from ..llm_service import generate_sql as llm_generate_sql
    
    # 先用规则生成基础 SQL
    base_sql = generate_sql_from_report_spec(report_spec)
    
    # 构造优化 prompt
    prompt = f"""你是一个 SQL 优化助手。请优化以下 Trino SQL，检查语法错误，使其更符合 Trino 语法。

原始 SQL：
{base_sql}

要求：
1. 只返回优化后的 SQL，不要解释
2. 确保 Trino 兼容的语法
3. 保持相同的查询逻辑

优化后的 SQL："""
    
    try:
        result = llm_generate_sql(prompt)
        
        if result.get("sql"):
            return {
                "sql": result["sql"],
                "source": "llm_optimized"
            }
    except Exception as e:
        pass
    
    # LLM 失败时返回基础 SQL
    return {
        "sql": base_sql,
        "source": "rule_based"
    }


if __name__ == "__main__":
    # 测试
    spec = ReportSpec(
        name="销售周报",
        tables=["sales.orders", "sales.customers"],
        joins=["orders.customer_id = customers.id"],
        metrics=[
            Metric(name="总销售额", expression="sum(orders.amount)"),
            Metric(name="订单数量", expression="count(orders.id)")
        ],
        dimensions=["customers.region", "date_trunc('week', orders.order_date)"],
        filters=["orders.status = 'completed'"]
    )
    
    sql = generate_sql_from_report_spec(spec)
    print(sql)
