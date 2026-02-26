import re
import uuid
from typing import Dict, List, Any
from ..models.report_spec import ReportSpec, Metric


class MarkdownParseError(Exception):
    """Markdown 解析错误"""
    pass


class ReportSpecValidationError(Exception):
    """ReportSpec 验证错误"""
    pass


def parse_markdown_to_report_spec(markdown: str) -> Dict[str, Any]:
    """
    解析 Markdown 为 ReportSpec 结构
    
    Markdown 格式：
    # 报表名称
    ## 数据源
    table1
    table2
    ## 关联关系
    t1.id = t2.id
    ## 统计指标
    - 指标名: sum(table.field)
    ## 分组维度
    - dimension1
    - dimension2
    ## 过滤条件
    - condition1
    - condition2
    """
    result = {
        "report_id": str(uuid.uuid4()),
        "parsed_structure": None,
        "error": None
    }
    
    try:
        lines = markdown.strip().split('\n')
        
        # 解析报表名称
        name = None
        tables = []
        joins = []
        metrics = []
        dimensions = []
        filters = []
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            
            # 跳过空行
            if not line:
                continue
            
            # 标题（报表名称）
            if line.startswith('# '):
                name = line[2:].strip()
                continue
            
            # Section 标记
            if line.startswith('## '):
                section_name = line[3:].strip()
                if '数据源' in section_name:
                    current_section = 'tables'
                elif '关联' in section_name or '关系' in section_name:
                    current_section = 'joins'
                elif '指标' in section_name:
                    current_section = 'metrics'
                elif '维度' in section_name:
                    current_section = 'dimensions'
                elif '过滤' in section_name or '条件' in section_name:
                    current_section = 'filters'
                else:
                    current_section = None
                continue
            
            # 解析内容行
            if current_section == 'tables':
                # 数据源表
                table = line.strip().rstrip('.')
                if table:
                    tables.append(table)
                    
            elif current_section == 'joins':
                # 关联关系
                join = line.strip()
                if join and ('=' in join or 'JOIN' in join.upper()):
                    joins.append(join)
                    
            elif current_section == 'metrics':
                # 统计指标 - 格式：- 指标名: sum(table.field)
                if line.startswith('- '):
                    metric_line = line[2:]
                    if ':' in metric_line:
                        metric_name, metric_expr = metric_line.split(':', 1)
                        metrics.append({
                            "name": metric_name.strip(),
                            "expression": metric_expr.strip()
                        })
                        
            elif current_section == 'dimensions':
                # 分组维度 - 格式：- dimension
                if line.startswith('- '):
                    dim = line[2:].strip()
                    if dim:
                        dimensions.append(dim)
                        
            elif current_section == 'filters':
                # 过滤条件 - 格式：- condition
                if line.startswith('- '):
                    filt = line[2:].strip()
                    if filt:
                        filters.append(filt)
        
        # 验证必填字段
        if not name:
            raise MarkdownParseError("缺少报表名称（# 标题）")
        if not tables:
            raise MarkdownParseError("缺少数据源（## 数据源）")
        if not metrics:
            raise MarkdownParseError("缺少统计指标（## 统计指标）")
        
        # 构建 ReportSpec 对象
        report_spec = ReportSpec(
            name=name,
            tables=tables,
            joins=joins,
            metrics=[Metric(**m) for m in metrics],
            dimensions=dimensions,
            filters=filters
        )
        
        # 转换为字典
        result["parsed_structure"] = report_spec.model_dump()
        
    except MarkdownParseError as e:
        result["error"] = str(e)
    except Exception as e:
        result["error"] = f"解析失败: {str(e)}"
    
    return result


def validate_report_spec(report_spec: ReportSpec) -> List[str]:
    """
    验证 ReportSpec 的合法性
    
    返回错误列表，如果为空则验证通过
    """
    errors = []
    
    # 验证表名格式
    for table in report_spec.tables:
        if '.' not in table:
            errors.append(f"表名必须包含 catalog.schema.table 格式: {table}")
    
    # 验证指标表达式
    allowed_functions = [
        'sum', 'count', 'avg', 'min', 'max',
        'date_trunc', 'date_add', 'date_sub',
        'year', 'month', 'day', 'week',
        'upper', 'lower', 'trim', 'coalesce',
        'cast', 'convert'
    ]
    
    for metric in report_spec.metrics:
        expr = metric.expression.lower()
        # 检查是否包含 SELECT（不允许自由 SQL）
        if 'select' in expr:
            errors.append(f"指标 '{metric.name}' 表达式不允许包含 SELECT")
        # 检查是否包含子查询
        if '(' in expr and 'select' in expr:
            errors.append(f"指标 '{metric.name}' 不允许包含子查询")
    
    return errors


if __name__ == "__main__":
    # 测试解析
    test_md = """# 销售周报
## 数据源
sales.orders
sales.customers
## 关联关系
orders.customer_id = customers.id
## 统计指标
- 总销售额: sum(orders.amount)
- 订单数量: count(orders.id)
## 分组维度
- customers.region
- date_trunc('week', orders.order_date)
## 过滤条件
- orders.status = 'completed'
- orders.order_date >= current_date - interval '30' day
"""
    
    result = parse_markdown_to_report_spec(test_md)
    print(result)
