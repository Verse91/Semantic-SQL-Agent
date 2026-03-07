# SAP HANA JDBC 驱动

## 获取 ngdbc.jar

SAP HANA JDBC 驱动 (`ngdbc.jar`) 需要从 SAP 官方渠道获取：

### 方法 1: SAP Support Portal (推荐)
1. 访问 https://support.sap.com/
2. 搜索 "JDBC" 或 "SAP HANA Client"
3. 下载 SAP HANA Client for your platform
4. 解压后找到 `ngdbc.jar`

### 方法 2: SAP HANA Express
如果你有 HANA Express 环境：
```bash
# 在 HANA 服务器上
ls $SAP_HOME/exports/dbdriver/ngdbc.jar
```

### 方法 3: Maven 仓库 (仅用于开发)
```xml
<dependency>
    <groupId>com.sap.cloud.db.jdbc</groupId>
    <artifactId>ngdbc</artifactId>
    <version>2.21.12</version>
</dependency>
```

## 安装

将下载的 `ngdbc.jar` 复制到此目录：

```bash
cp /path/to/ngdbc.jar drivers/
```

## 配置

编辑 `config/database.yaml` 设置 HANA 连接信息：

```yaml
hana:
  jdbc_url: jdbc:sap://your-hana-host:30015
  user: YOUR_USERNAME
  password: YOUR_PASSWORD
```

建议使用环境变量：

```bash
export HANA_USER=your_username
export HANA_PASSWORD=your_password
```
