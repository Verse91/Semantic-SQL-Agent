import os

# Trino 配置
TRINO_HOST = os.getenv("TRINO_HOST", "localhost")
TRINO_PORT = os.getenv("TRINO_PORT", "8080")
TRINO_USER = os.getenv("TRINO_USER", "admin")
TRINO_CATALOG = os.getenv("TRINO_CATALOG", "mysql")
TRINO_SCHEMA = os.getenv("TRINO_SCHEMA", "sap")

# OpenClaw API 配置
OPENCLOW_API_URL = os.getenv("OPENCLOW_API_URL", "http://localhost:18789")
OPENCLOW_API_KEY = os.getenv("OPENCLOW_API_KEY", "")

# 数据库 Schema 信息（用于 LLM 生成 SQL）
DATABASE_SCHEMA = os.getenv(
    "DATABASE_SCHEMA",
    """
表 sales:
- id int
- amount double
- date date
- customer varchar

表 mara (物料主数据):
- matnr VARCHAR(40) - 物料号
- ersda DATE - 创建日期
- ernam VARCHAR(12) - 创建人
- laeda DATE - 修改日期
- aenam VARCHAR(12) - 修改人
- vpsta VARCHAR(4) - 维护状态
- pstat VARCHAR(4) - 状态
- lvorm VARCHAR(1) - 删除标志
- mtart VARCHAR(4) - 物料类型
- matkl VARCHAR(9) - 物料组

表 makt (物料描述):
- matnr VARCHAR(40) - 物料号
- spras VARCHAR(2) - 语言 (E=英文, C=中文)
- maktx VARCHAR(120) - 物料描述
"""
)
