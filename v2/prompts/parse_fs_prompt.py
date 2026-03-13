"""
FS Parser Prompt
"""


def build_parse_fs_prompt(fs_document: str) -> str:
    """
    构建 FS 解析 prompt
    
    Args:
        fs_document: FS 文档内容
        
    Returns:
        prompt 字符串
    """
    prompt = f"""你是一个专业的报表需求分析师。

请分析以下 FS（Functional Spec）报表文档，提取结构化信息。

## FS 文档内容：
{fs_document}

## 输出要求：
请将上述 FS 文档解析为 JSON 格式，包含以下字段：
{{
    "report_name": "报表名称",
    "tables": ["涉及的表名，如 sd.vbak, md.kna1 等"],
    "dimensions": ["维度字段，如客户、日期、地区等"],
    "metrics": ["指标字段，如销售金额、数量、利润率等"],
    "filters": ["筛选条件，如时间范围、客户类型等"]
}}

注意：
1. tables 必须是完整的表名（带 schema），如 sd.vbak, md.kna1, im.mard 等
2. 如果文档中没有明确的信息，请使用空数组 []
3. 只返回 JSON，不要其他解释

JSON："""
    
    return prompt
