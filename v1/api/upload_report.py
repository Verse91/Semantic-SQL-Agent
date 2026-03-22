from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from typing import Dict, Any
import json

from ..models.report_spec import UploadReportResponse, ReportSpec
from ..services.markdown_parser import parse_markdown_to_report_spec, validate_report_spec, ReportSpecValidationError

router = APIRouter()


@router.post("/upload_report_spec", response_model=UploadReportResponse)
async def upload_report_spec(file: UploadFile = File(...)):
    """
    上传 Markdown 报表定义文件
    
    支持 .md 和 .txt 格式
    """
    result = {
        "success": False,
        "data": None,
        "error": None
    }
    
    try:
        # 检查文件类型
        if not file.filename.endswith(('.md', '.txt')):
            result["error"] = "仅支持 .md 或 .txt 格式的 Markdown 文件"
            return result
        
        # 读取文件内容
        content = await file.read()
        markdown = content.decode('utf-8')
        
        # 解析 Markdown
        parse_result = parse_markdown_to_report_spec(markdown)
        
        if parse_result.get("error"):
            result["error"] = parse_result["error"]
            return result
        
        # 验证 ReportSpec
        parsed_structure = parse_result["parsed_structure"]
        report_spec = ReportSpec(**parsed_structure)
        
        validation_errors = validate_report_spec(report_spec)
        if validation_errors:
            result["error"] = " | ".join(validation_errors)
            return result
        
        # 返回解析结果
        result["success"] = True
        result["data"] = {
            "report_id": parse_result["report_id"],
            "name": parsed_structure["name"],
            "parsed_structure": parsed_structure
        }
        
    except Exception as e:
        result["error"] = f"处理失败: {str(e)}"
    
    return result


@router.post("/generate_sql_from_spec")
async def generate_sql_from_spec(request: dict):
    """
    根据 ReportSpec 生成 SQL
    """
    result = {
        "success": False,
        "data": None,
        "error": None
    }
    
    try:
        # 解析 ReportSpec
        report_spec_dict = request.get("report_spec")
        if not report_spec_dict:
            result["error"] = "缺少 report_spec 字段"
            return result
        
        from ..models.report_spec import ReportSpec
        from ..services.report_sql_generator import generate_sql_from_report_spec, generate_sql_with_llm_assist
        
        # 构建 ReportSpec
        report_spec = ReportSpec(**report_spec_dict)
        
        # 验证
        validation_errors = validate_report_spec(report_spec)
        if validation_errors:
            result["error"] = " | ".join(validation_errors)
            return result
        
        # 生成 SQL（先尝试规则，LLM 作为后备）
        sql_result = generate_sql_with_llm_assist(report_spec)
        
        result["success"] = True
        result["data"] = {
            "sql": sql_result["sql"],
            "source": sql_result.get("source", "rule_based")
        }
        
    except Exception as e:
        result["error"] = f"生成失败: {str(e)}"
    
    return result
