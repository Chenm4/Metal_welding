# 后端代码说明

## 📁 项目结构

```
backend/
├── .env                      # 环境配置文件
├── config.py                 # 配置类定义
├── requirements.txt          # Python依赖包
├── scripts/                  # 脚本工具
│   ├── create_db.py         # 创建数据库
│   ├── init_db.py           # 初始化数据表
│   └── generate_sql.py      # 根据Excel生成建表SQL
├── services/                 # 业务逻辑服务层
│   ├── __init__.py
│   └── csv_service.py       # CSV/Excel处理服务
└── utils/                    # 工具模块
    ├── __init__.py
    └── database.py          # 数据库连接工具
```

## 🚀 快速开始

### 1. 创建Conda环境

```bash
conda create -n metalwelding python=3.11
conda activate metalwelding
```

### 2. 安装依赖

```bash
pip install pymysql pandas openpyxl
```

### 3. 配置数据库

编辑 `.env` 文件，设置MySQL连接信息：

```
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=1234
MYSQL_DATABASE=metal_welding
```

### 4. 初始化数据库

```bash
cd backend/scripts

# 第一步：创建数据库
python create_db.py

# 第二步：初始化所有表
python init_db.py
```

## 📊 数据库表结构

执行完初始化后，数据库中包含以下表：

### 系统表（3个）

- **sys_users** - 用户表（包含admin和viewer两个默认用户）
- **sys_import_tasks** - CSV导入任务记录表
- **sys_operation_logs** - 操作日志表

### 数据表（4个）

- **exp_data_batch_1** - 批次1数据表（34个字段）
- **exp_data_batch_2** - 批次2数据表（结构同batch_1）
- **exp_data_batch_3** - 批次3数据表（结构同batch_1）
- **exp_data_batch_4** - 批次4数据表（结构同batch_1）

## 📝 批次1字段说明

根据 `data/batch_1/625试验数据_修改过后.xlsx` 自动生成，共34个字段：

### 物性字段（2个）

- 物性_材料
- 物性_材料厚度

### 工艺字段（7个）

- 正面保护气流量（L/min）
- 背面保护气流量（L/min）
- 工艺_激光功率
- 工艺_焊接速度
- 激光倾角
- 离焦量
- 送丝速度

### 性能字段（6个）

- 焊缝宽度
- 熔深（mm）
- 焊缝形貌
- 性能_拉伸性能（温度23℃）抗拉强度MPa
- 性能_拉伸性能（温度23℃）断后伸长率%
- 性能_拉伸性能（温度23℃）屈服强度MPa

### 其他字段（19个）

- 编号
- 接头类型
- 光斑尺寸（mm）
- 视觉系统
- 电流
- 正面保护气类型
- 背面保护气类型
- 焊丝
- 焊丝直径
- 焊脚高度
- 内部质量
- 尺寸
- 无损照片号
- 无损结果
- 性能_弯曲性能
- 性能_剪切性能
- 金相组织
- 工艺
- 挂靠项目任务号

## 🛠️ 核心功能说明

### 1. CSV/Excel处理服务 (`services/csv_service.py`)

**主要功能：**

- ✅ 自动检测文件编码（UTF-8/GBK）
- ✅ 读取Excel和CSV文件
- ✅ 自动分析列分类（物性/工艺/状态/性能）
- ✅ 根据DataFrame自动生成建表SQL
- ✅ 数据清洗（空值处理）

**核心函数：**

```python
read_excel(file_path)              # 读取Excel文件
read_csv(file_path)                # 读取CSV文件
analyze_columns(df)                # 分析列并分类
generate_create_table_sql(df, table_name)  # 生成建表SQL
clean_value(value)                 # 清洗数据值
```

### 2. 数据库工具 (`utils/database.py`)

**主要功能：**

- ✅ MySQL连接池管理
- ✅ MongoDB连接管理
- ✅ 数据库会话管理（FastAPI依赖注入）
- ✅ SQL文件执行
- ✅ 表结构查询

**核心函数：**

```python
get_db()                           # 获取数据库会话
test_mysql_connection()            # 测试连接
execute_sql_file(sql_file_path)    # 执行SQL文件
get_table_columns(table_name)      # 获取表列名
table_exists(table_name)           # 检查表是否存在
```

### 3. 自动SQL生成 (`scripts/generate_sql.py`)

**功能：**

- 读取Excel文件
- 自动识别所有列
- 按照规范生成CREATE TABLE语句
- 所有字段统一使用VARCHAR(255)
- 自动添加审计字段（created_at, updated_at等）

**使用方法：**

```bash
python generate_sql.py
```

生成的SQL保存在 `sql/init_batch_1.sql`

## ⚙️ 配置说明

### 环境变量 (`.env`)

所有配置都在 `.env`文件中，包括：

- 应用配置（名称、版本、调试模式）
- JWT配置（密钥、算法、过期时间）
- MySQL配置（主机、端口、用户名、密码、数据库名）
- MongoDB配置
- 文件上传配置
- 日志配置
- CORS配置

### 配置类 (`config.py`)

使用Pydantic Settings管理配置，支持：

- 环境变量自动加载
- 类型验证
- 默认值设置
- 批次映射配置
- 数据分类配置

## 🔑 设计要点

### 1. 完全解耦

- ✅ 数据库操作单独封装在 `utils/database.py`
- ✅ CSV处理逻辑独立在 `services/csv_service.py`
- ✅ SQL脚本与代码分离，存放在 `sql/`目录
- ✅ 配置文件独立管理

### 2. 函数式编程

- ✅ 所有功能都封装成独立函数
- ✅ 函数职责单一，易于测试
- ✅ 参数清晰，返回值明确

### 3. 主键设计

- ✅ **不使用CSV中的字段作为主键**
- ✅ 统一使用自增id作为主键
- ✅ CSV中的"编号"等字段允许重复
- ✅ 只添加时间索引，提高查询效率

### 4. 数据类型

- ✅ 按照要求，所有CSV字段统一使用 `VARCHAR(255)`
- ✅ 附加字段使用合适类型（DATETIME、JSON、TEXT、ENUM）
- ✅ 字符集统一使用 `utf8mb4`

## 📋 下一步计划

1. ✅ 数据库初始化完成
2. 🔄 实现数据导入功能（从Excel导入到数据库）
3. 🔄 实现覆盖率计算服务
4. 🔄 实现FastAPI接口
5. 🔄 实现认证和权限控制
6. 🔄 实现前端对接

## 🐛 常见问题

### Q: 如何重新生成表结构？

```bash
# 删除表后重新初始化
python init_db.py
```

### Q: 如何查看生成的SQL？

查看文件：`sql/init_batch_1.sql`

### Q: 如何为新批次生成SQL？

修改 `scripts/generate_sql.py` 中的文件路径，然后运行。

### Q: 数据库连接失败？

检查：

1. MySQL服务是否启动
2. `.env`中的用户名密码是否正确
3. 数据库是否已创建（运行 `create_db.py`）

## 📞 技术支持

如有问题，请查看：

- [API规范 - 前端对接文档](../docs/API_规范_前端对接文档.md)
- [API规范 - 后端开发文档](../docs/API_规范_后端开发文档.md)
- [数据库设计文档](../docs/数据库设计文档.md)
- [错误码规范](../docs/错误码规范.md)
