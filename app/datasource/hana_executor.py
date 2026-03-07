"""
SAP HANA 数据库执行器
使用 JDBC 通过 jaydebeapi 执行 HANA 查询
"""

import os
import jaydebeapi
import yaml
from typing import List, Dict, Any, Optional


class HanaError(Exception):
    """HANA 执行异常"""
    pass


class HanaExecutor:
    """SAP HANA JDBC 执行器"""
    
    def __init__(self, config_path: str = "config/database.yaml"):
        """
        初始化 HANA 执行器
        
        Args:
            config_path: 配置文件路径 (相对于项目根目录)
        """
        # 查找项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        config_path = os.path.join(project_root, "config", "database.yaml")
        
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        hana_config = config.get('hana', {})
        
        self.driver = hana_config.get('driver', 'com.sap.db.jdbc.Driver')
        self.jdbc_url = hana_config.get('jdbc_url', 'jdbc:sap://localhost:30015')
        
        # 支持环境变量
        self.user = os.getenv('HANA_USER', hana_config.get('user', 'SYSTEM'))
        self.password = os.getenv('HANA_PASSWORD', hana_config.get('password', ''))
        self.jar_path = hana_config.get('jar', 'drivers/ngdbc.jar')
        
        # 解析 jar 路径
        self.jar_path = os.path.join(project_root, self.jar_path)
    
    def _get_connection(self):
        """
        建立 HANA JDBC 连接
        
        Returns:
            jaydebeapi 连接对象
        """
        try:
            conn = jaydebeapi.connect(
                self.driver,
                self.jdbc_url,
                [self.user, self.password],
                self.jar_path
            )
            return conn
        except Exception as e:
            raise HanaError(f"Failed to connect to HANA: {str(e)}")
    
    def run_query(self, sql: str) -> List[Dict[str, Any]]:
        """
        执行 SELECT 查询
        
        Args:
            sql: SELECT 查询语句
            
        Returns:
            查询结果列表，每行为一个字典
        """
        conn = None
        cursor = None
        
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # 执行查询
            cursor.execute(sql)
            
            # 获取列名
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            
            # 获取所有结果
            rows = cursor.fetchall()
            
            # 转换为字典列表
            result = []
            for row in rows:
                row_dict = {}
                for i, col in enumerate(columns):
                    # 处理日期、时间等类型
                    value = row[i]
                    row_dict[col] = self._convert_value(value)
                result.append(row_dict)
            
            return result
            
        except Exception as e:
            raise HanaError(f"Query execution failed: {str(e)}")
        
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    def _convert_value(self, value: Any) -> Any:
        """
        转换特殊数据类型
        
        Args:
            value: 原始值
            
        Returns:
            转换后的值
        """
        # 处理 None
        if value is None:
            return None
        
        # 处理日期类型 (java.util.Date)
        # 注意: 根据实际 JDBC 返回类型调整
        return value
    
    def test_connection(self) -> bool:
        """
        测试 HANA 连接
        
        Returns:
            连接是否成功
        """
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM DUMMY")
            cursor.fetchone()
            cursor.close()
            conn.close()
            return True
        except Exception:
            return False


if __name__ == "__main__":
    # 测试连接
    executor = HANAExecutor()
    
    test_sql = "SELECT MATNR, ERSDA FROM MARA LIMIT 10"
    print(f"Executing: {test_sql}")
    
    try:
        result = executor.run_query(test_sql)
        print(f"Result: {result}")
    except HanaError as e:
        print(f"Error: {e}")
