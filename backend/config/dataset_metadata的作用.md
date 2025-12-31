# dataset_metadata.json 配置文件说明

## 📋 核心定位

`dataset_metadata.json` 是整个系统的**"数据字典"**或**"配置中心"**，是实现**元数据驱动架构**的核心文件。

**核心理念**：让代码从"硬编码"变成"配置驱动"

---

## 🎯 主要作用

### 1. 统一管理所有数据集的元信息

该JSON文件集中存储了所有实验数据集的：
- 数据集ID（如 `batch_1`, `batch_2`, `custom`）
- 数据库表名（如 `exp_data_batch_1`）
- 显示名称（如 "第1批实验数据"）
- 字段列表（所有列的名称、类型、分类）
- 可搜索字段配置
- 必填字段配置
- 覆盖率计算配置

### 2. 实现零硬编码的动态扩展

有了元数据配置，添加新数据集（如 batch_10）时：
- ❌ **不需要**修改任何业务代码
- ❌ **不需要**重启服务
- ✅ **只需要**运行 `generate_metadata.py` 或通过API自动创建
- ✅ **自动支持**查询、搜索、覆盖率、导入等所有功能

### 3. 前后端解耦

- 前端通过 `/api/experimental-data/{dataset_id}/schema` 获取字段信息
- 前端根据返回的元数据动态渲染表格和表单
- 字段修改无需前后端同时改动

---

## 🔍 具体使用场景

### 场景1：查询数据时 - 动态构建SQL

**文件位置**：`backend/services/experimental/base_service.py` 第94-128行

```python
def list_data(self, dataset_id: str, page: int, page_size: int):
    # ❌ 硬编码方式（老代码）：
    # fields = "编号, 物性_材料, 工艺_激光功率, ..."  # 写死37个字段
    
    # ✅ 元数据驱动方式（新代码）：
    fields = DatasetMetadata.get_all_field_names(dataset_id)  # 从JSON读取！
    fields_str = ', '.join(f'`{f}`' for f in fields)
    
    sql = f"SELECT {fields_str} FROM {table_name} WHERE ..."
    # SQL自动包含JSON中定义的所有字段
```

**何时使用**：每次调用 `GET /api/experimental-data/batch_1?page=1&page_size=20`

**价值**：
- 添加新字段"焊接日期"后，只需运行 `generate_metadata.py`
- 代码**无需修改**，查询结果自动包含新字段

---

### 场景2：搜索功能 - 确定可搜索字段

**文件位置**：`backend/services/experimental/base_service.py` 第166-210行

```python
def search(self, dataset_id: str, keyword: str):
    # ✅ 元数据驱动方式（新版本）：
    # 自动返回所有data_fields的字段名，无需手动配置
    search_fields = DatasetMetadata.get_searchable_fields(dataset_id)  # 返回所有数据字段！
    
    # 构建搜索SQL
    conditions = []
    for field in search_fields:
        conditions.append(f"`{field}` LIKE %s")
    
    where_clause = " OR ".join(conditions)
    # 生成：WHERE 编号 LIKE '%keyword%' OR 物性_材料 LIKE '%keyword%' OR ... (所有字段)
```

**何时使用**：调用 `GET /api/experimental-data/batch_1/search?keyword=激光`

**价值**：
- 所有 `data_fields` 都自动可搜索，无需手动配置
- 添加新字段后，自动支持搜索
- ~~JSON配置中的 `searchable_fields` 控制哪些字段可被搜索~~（已废弃，现在所有字段都可搜索）

---

### 场景3：覆盖率计算 - 确定统计字段

**文件位置**：`backend/services/experimental/coverage_service.py` 第64-89行

```python
def calculate_row_coverage(self, dataset_id: str, row: Dict) -> float:
    # ❌ 硬编码方式（老代码）：
    # data_fields = ['编号', '物性_材料', ...]  # 写死34个字段
    # audit_fields = ['id', 'created_at', ...]  # 写死审计字段
    
    # ✅ 元数据驱动：
    data_fields = DatasetMetadata.get_data_fields(dataset_id)  # 从JSON读取！
    exclude_fields = DatasetMetadata.get_coverage_exclude_fields(dataset_id)
    
    # 自动排除审计字段（id, created_at等）
    calculate_fields = [f for f in data_fields if f not in exclude_fields]
    
    # 计算覆盖率：非空字段数 / 总字段数
    filled = sum(1 for f in calculate_fields if row.get(f) is not None)
    return filled / len(calculate_fields)
```

**何时使用**：调用 `GET /api/experimental-data/batch_1/coverage`

**价值**：
- JSON中的 `exclude_from_calculation` 配置了需要排除的字段
- 覆盖率计算自动排除 `id`、`created_at` 等审计字段
- 无需在代码中维护排除列表

---

### 场景4：前端渲染 - 获取字段结构

**文件位置**：`backend/routes/experimental/data_routes.py` 第72-97行

```python
@router.get("/{dataset_id}/schema")
async def get_schema(dataset_id: str):
    """获取数据集的字段结构（供前端渲染表格）"""
    
    # 从JSON读取字段信息
    all_fields = DatasetMetadata.get_all_field_names(dataset_id)
    
    # 按分类组织字段
    categories = {
        "物性": DatasetMetadata.get_fields_by_category(dataset_id, "物性"),
        "工艺": DatasetMetadata.get_fields_by_category(dataset_id, "工艺"),
        "状态": DatasetMetadata.get_fields_by_category(dataset_id, "状态"),
        "性能": DatasetMetadata.get_fields_by_category(dataset_id, "性能"),
    }
    
    return {
        "dataset_id": dataset_id,
        "fields": all_fields,
        "categories": categories,
        "searchable_fields": DatasetMetadata.get_searchable_fields(dataset_id)
    }
```

**何时使用**：前端加载页面时调用 `GET /api/experimental-data/batch_1/schema`

**价值**：
- 前端不需要硬编码列名和分类
- 根据返回的分类信息，动态渲染"物性/工艺/状态/性能"Tab按钮
- 字段顺序、分类变更时，前端自动适配

---

### 场景5：导入CSV - 验证列名匹配

**文件位置**：`backend/routes/experimental/data_routes.py` 第271-295行

```python
@router.post("/{dataset_id}/import")
async def import_file(dataset_id: str, file: UploadFile):
    # 读取CSV文件
    df = pd.read_csv(file.file)
    csv_columns = df.columns.tolist()
    
    # 从JSON获取数据库表的列名
    db_columns = DatasetMetadata.get_all_field_names(dataset_id)
    
    # 验证：CSV的列名是否与数据库一致？
    missing_in_csv = set(db_columns) - set(csv_columns)
    extra_in_csv = set(csv_columns) - set(db_columns)
    
    if missing_in_csv or extra_in_csv:
        raise HTTPException(
            status_code=400,
            detail=f"列名不匹配！缺少：{missing_in_csv}，多余：{extra_in_csv}"
        )
    
    # 验证通过，开始导入
    ...
```

**何时使用**：上传CSV文件时 `POST /api/experimental-data/batch_1/import`

**价值**：
- 防止用户上传错误的CSV文件
- 如果CSV少了"焊接温度"字段，导入前就报错提示
- 避免部分数据导入成功、部分失败的情况

---

### 场景6：字段类型验证

**文件位置**：`backend/services/experimental/base_service.py` 第320-350行

```python
def validate_data(self, dataset_id: str, data: Dict) -> Dict:
    """根据元数据验证数据类型"""
    
    # 从JSON获取字段类型定义
    field_definitions = DatasetMetadata.get_field_definitions(dataset_id)
    
    validated = {}
    for field_name, field_info in field_definitions.items():
        value = data.get(field_name)
        field_type = field_info['type']
        
        # 根据类型转换
        if field_type == 'integer':
            validated[field_name] = int(value) if value else None
        elif field_type == 'float':
            validated[field_name] = float(value) if value else None
        elif field_type == 'datetime':
            validated[field_name] = parse_datetime(value) if value else None
        else:
            validated[field_name] = str(value) if value else None
    
    return validated
```

**价值**：
- 数据类型统一管理
- 自动类型转换和验证
- 避免类型不匹配导致的数据库错误

---

## 🔄 完整工作流程

```
1. 创建新数据库表 (exp_data_batch_7)
   ↓
2. 运行脚本生成元数据
   python backend/scripts/generate_metadata.py
   ↓
3. 更新 dataset_metadata.json
   {
     "datasets": {
       "batch_7": {
         "table_name": "exp_data_batch_7",
         "fields": {...}
       }
     }
   }
   ↓
4. 重新加载元数据缓存
   DatasetMetadata.reload_metadata()
   ↓
5. 所有功能自动支持 batch_7
   ✓ 数据查询
   ✓ 关键词搜索
   ✓ 覆盖率计算
   ✓ 前端渲染
   ✓ CSV导入
   ✓ 数据验证
   
🎯 全程零业务代码修改！
```

---

## 📊 硬编码 vs 元数据驱动对比

| 维度 | 硬编码方式 | 元数据驱动方式 |
|------|-----------|---------------|
| **添加新数据集** | 需修改10+处代码 | 运行1个脚本即可 |
| **修改字段名** | 全局搜索替换，容易遗漏 | 只需修改JSON文件 |
| **字段分类调整** | 前后端代码都要改 | 只改JSON，前端自动适配 |
| **前端适配** | 前后端都要修改 | 后端改JSON，前端调用schema接口自动获取 |
| **维护成本** | 高（容易漏改，难以测试） | 低（统一配置，单点维护） |
| **扩展性** | 差（改动困难，易出错） | 强（无限扩展，配置即可用） |
| **代码可读性** | 差（业务逻辑混杂字段定义） | 好（配置与逻辑分离） |
| **测试难度** | 高（需要大量mock） | 低（只需替换配置文件） |

---

## 💡 实际案例：添加新批次

### 场景：需要添加 batch_10 实验数据

#### ❌ 硬编码方式（传统做法）

需要修改以下文件：

1. **backend/services/experimental/base_service.py**
```python
def list_data(self, batch_id):
    if batch_id == 10:  # 手动加判断
        fields = "编号,物性_材料,工艺_激光功率,..."  # 手动写40个字段
        sql = f"SELECT {fields} FROM exp_data_batch_10 ..."
```

2. **backend/services/experimental/coverage_service.py**
```python
# 手动添加batch_10的字段列表
BATCH_10_DATA_FIELDS = [
    '编号', '物性_材料', '物性_体积分数', ...  # 40个字段全写
]
```

3. **backend/routes/experimental/data_routes.py**
```python
# 手动添加batch_10的路由逻辑
if dataset_id == 'batch_10':
    searchable_fields = ['编号', '物性_材料', ...]
```

4. **前端代码（如果有）**
```javascript
// 手动配置batch_10的列信息
const batch10Columns = [
  { field: '编号', label: '编号' },
  { field: '物性_材料', label: '材料', category: '物性' },
  ...  // 40个字段
]
```

**问题**：
- 需要修改4-5个文件
- 容易遗漏某个位置
- 修改后需要完整测试
- 前后端都要改动

---

#### ✅ 元数据驱动方式（现代做法）

```bash
# 方式1：通过API导入CSV自动创建
curl -X POST http://localhost:8000/api/experimental-data/batch_10/import \
     -F "file=@batch_10_data.csv" \
     -H "Authorization: Bearer <token>"

# 方式2：手动运行生成脚本
python backend/scripts/generate_metadata.py

# 3. 完成！所有功能自动支持batch_10
✓ 查询：GET /api/experimental-data/batch_10
✓ 搜索：GET /api/experimental-data/batch_10/search
✓ 覆盖率：GET /api/experimental-data/batch_10/coverage
✓ Schema：GET /api/experimental-data/batch_10/schema
✓ 导入：POST /api/experimental-data/batch_10/import
```

**优势**：
- ✅ 零代码修改
- ✅ 前端自动适配（调用schema接口获取字段）
- ✅ 所有功能自动生效
- ✅ 无需重启服务（可选）

---

## 📝 JSON文件结构说明

```json
{
  "datasets": {
    "batch_1": {
      "table_name": "exp_data_batch_1",           // 数据库表名
      "display_name": "第1批实验数据",             // 显示名称
      "description": "批次1的激光焊接实验数据",     // 描述
      
      "fields": {
        "data_fields": [                          // 数据字段列表
          {
            "name": "编号",                        // 字段名
            "type": "string",                     // 字段类型
            "nullable": true,                     // 是否可空
            "category": "其他"                     // 字段分类
          },
          {
            "name": "物性_材料",
            "type": "string",
            "nullable": true,
            "category": "物性"                     // 分类：物性/工艺/状态/性能
          }
          // ... 更多字段
        ],
        
        // 注意：searchable_fields 配置已废弃（可选）
        // 所有 data_fields 都自动可搜索，由代码动态获取
        
        "required_fields": ["编号"],              // 必填字段列表
        
        "audit_fields": [                         // 审计字段（系统字段）
          "created_at",
          "updated_at",
          "created_by",
          "updated_by"
        ]
      },
      
      "coverage": {                               // 覆盖率计算配置
        "threshold": 0.9,                         // 覆盖率阈值（90%）
        "exclude_from_calculation": [             // 计算时排除的字段
          "id",
          "created_at",
          "updated_at",
          "created_by",
          "updated_by",
          "deleted_at",
          "is_deleted",
          "version"
        ]
      }
    }
    // ... 更多数据集（batch_2, batch_3, ...）
  }
}
```

---

## 🔧 生成元数据的脚本

**脚本位置**：`backend/scripts/generate_metadata.py`

**功能**：
1. 连接数据库
2. 扫描所有 `exp_data_` 开头的表
3. 读取每个表的列信息（SHOW COLUMNS）
4. 推断字段类型（int/float/string/datetime）
5. 根据字段名前缀分类（物性_、工艺_、状态_、性能_）
6. 生成完整的JSON配置
7. 保存到 `backend/config/dataset_metadata.json`

**运行方式**：
```bash
cd backend/scripts
python generate_metadata.py
```

**输出示例**：
```
发现 4 个数据集表: exp_data_batch_1, exp_data_batch_2, exp_data_batch_3, exp_data_batch_4

正在处理 exp_data_batch_1...
✓ exp_data_batch_1: 37 个数据字段

正在处理 exp_data_batch_2...
✓ exp_data_batch_2: 37 个数据字段

...

✓ 元数据配置已生成: E:\value_code\Metal_welding\backend\config\dataset_metadata.json
  共 4 个数据集
```

---

## 🎯 核心价值总结

### 1. 解耦 - 配置与逻辑分离
- 字段定义从代码中抽离到JSON配置
- 业务逻辑只关注"怎么做"，不关心"具体字段"
- 修改配置不影响代码稳定性

### 2. 灵活 - 修改配置不改代码
- 添加字段：运行脚本即可
- 调整分类：修改JSON即可
- 修改搜索范围：改searchable_fields即可

### 3. 可维护 - 单点管理
- 所有数据集的元信息集中在一个文件
- 不需要在多个文件中维护重复信息
- 减少维护成本和出错概率

### 4. 可扩展 - 无限数量的数据集
- 支持任意数量的数据集（batch_1 到 batch_N）
- 支持自定义数据集名称（不限于batch格式）
- 通过API自动创建新数据集

### 5. 类型安全 - 统一的类型定义
- 字段类型集中定义
- 自动类型验证和转换
- 避免类型不匹配错误

### 6. 前后端协同 - 自动同步
- 前端通过schema接口获取字段信息
- 字段变更时前端自动适配
- 减少前后端联调成本

---

## 🚀 最佳实践

### 1. 每次表结构变更后重新生成
```bash
# 添加/修改字段后，运行脚本更新元数据
python backend/scripts/generate_metadata.py
```

### 2. 版本控制
- 将 `dataset_metadata.json` 纳入Git版本控制
- 表结构变更时提交对应的元数据变更
- 方便追踪历史变更

### 3. 手动微调
- 脚本生成后，可手动调整 `searchable_fields`
- 可调整 `category` 分类
- 可修改 `display_name` 显示名称

### 4. 环境隔离
- 开发/测试/生产环境使用不同的元数据文件
- 通过环境变量指定元数据文件路径
- 避免环境间配置混乱

### 5. 缓存刷新
```python
# 修改JSON后，在代码中刷新缓存
from backend.models.experimental.metadata import DatasetMetadata
DatasetMetadata.reload_metadata()
```

---

## 🔗 相关文件

| 文件路径 | 作用 |
|---------|------|
| `backend/config/dataset_metadata.json` | 元数据配置文件（本文档描述的核心文件） |
| `backend/scripts/generate_metadata.py` | 元数据生成脚本 |
| `backend/models/experimental/metadata.py` | 元数据读取和管理类 |
| `backend/services/experimental/base_service.py` | 使用元数据的业务服务 |
| `backend/routes/experimental/data_routes.py` | 提供schema接口的路由 |

---

## 📚 总结

**`dataset_metadata.json` 是整个系统的"配置中心"**：

- 📋 **数据字典**：定义所有数据集的字段信息
- 🔧 **配置驱动**：让代码从硬编码变成配置驱动
- 🚀 **零改代码**：添加数据集无需修改业务逻辑
- 🎨 **前端友好**：提供schema接口供前端动态渲染
- 🔍 **类型安全**：统一的字段类型定义和验证
- 📦 **易于维护**：单点管理，修改方便

**核心优势**：
> 没有这个JSON文件，你的系统是"硬编码"的——每次改动都要改代码、测试、重启服务。  
> 有了它，大部分改动只需改配置文件，甚至可以通过API动态创建新数据集！

这就是**元数据驱动架构**的核心价值所在。

