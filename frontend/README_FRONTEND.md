# SiCp/Al 复合材料焊接数据库系统 - 前端

一个基于 React + TypeScript + Ant Design 构建的现代化焊接数据管理系统。

## ✨ 功能特性

### 🔐 用户认证
- 登录/登出功能
- JWT Token 认证
- 用户角色权限控制（管理员/普通用户）
- 自动 Token 刷新和过期处理

### 📊 数据管理
- 多数据集支持，动态切换
- 数据列表展示，支持分页
- 实时搜索功能
- 字段分类筛选（物性/工艺/状态/性能）
- 数据完整度统计和可视化

### ⚙️ 管理员功能
- 数据 CRUD 操作（新增、编辑、删除、批量删除）
- CSV/Excel 文件导入
- 自动创建新数据集
- 数据验证和重复检测

### 🎨 用户界面
- 响应式设计，支持移动端
- 优雅的动画效果
- 直观的操作提示
- 友好的错误处理

## 🚀 技术栈

- **框架**: React 19 + TypeScript
- **路由**: React Router v6
- **UI 库**: Ant Design 5
- **HTTP 客户端**: Axios
- **构建工具**: Vite
- **状态管理**: React Context API
- **样式方案**: CSS Modules + Ant Design

## 📦 项目结构

```
src/
├── components/          # 公共组件
│   ├── DataEditModal/  # 数据编辑弹窗
│   ├── ImportModal/    # CSV 导入弹窗
│   └── PrivateRoute/   # 路由守卫
├── config/             # 配置文件
│   └── constants.ts    # 常量定义
├── contexts/           # React Context
│   └── AuthContext.tsx # 认证上下文
├── layouts/            # 布局组件
│   └── MainLayout/     # 主布局
├── pages/              # 页面组件
│   ├── Login/          # 登录页
│   └── DataManagement/ # 数据管理页
├── router/             # 路由配置
│   └── index.tsx
├── services/           # API 服务
│   ├── auth.ts         # 认证服务
│   ├── data.ts         # 数据服务
│   ├── dataset.ts      # 数据集服务
│   └── coverage.ts     # 覆盖率服务
├── types/              # TypeScript 类型
│   └── index.ts
└── utils/              # 工具函数
    ├── request.ts      # HTTP 请求封装
    └── storage.ts      # 本地存储工具
```

## 🛠️ 开发指南

### 环境要求

- Node.js >= 16
- npm >= 8

### 安装依赖

```bash
npm install
```

### 开发模式

```bash
npm run dev
```

应用将运行在 `http://localhost:5173`

### 生产构建

```bash
npm run build
```

### 预览生产版本

```bash
npm run preview
```

## ⚙️ 配置

### 环境变量

在项目根目录创建 `.env.local` 文件配置环境变量：

```env
# API 基础地址
VITE_API_BASE_URL=http://localhost:8004
```

### API 代理

开发环境下，Vite 会自动代理 `/api` 请求到后端服务器，配置见 `vite.config.ts`。

## 📝 API 接口对接

所有 API 接口定义在 `src/services/` 目录下，与后端路由保持一致：

- **认证**: `/api/auth/*` - 用户登录、获取用户信息
- **数据集**: `/api/experimental-data/datasets` - 数据集列表和结构
- **数据管理**: `/api/experimental-data/{dataset_id}/*` - 数据 CRUD、搜索、导入
- **覆盖率**: `/api/experimental-data/{dataset_id}/coverage` - 数据完整度统计

## 🎯 核心功能说明

### 1. 用户角色

- **管理员**: 拥有所有权限，可以增删改查数据、导入文件
- **普通用户**: 只能查看数据，不能修改

### 2. 数据分类

数据字段按业务分为四类，每类用不同颜色标识：

- 🧱 **物性参数** (蓝色): 材料物理性质
- ⚙️ **工艺参数** (绿色): 焊接工艺参数
- 🌡️ **状态参数** (橙色): 实时监测状态
- 📈 **性能指标** (红色): 焊接质量指标

### 3. 数据导入

支持两种导入模式：

- **新建数据集**: 自动创建新表和元数据配置
- **追加数据**: 向现有数据集添加数据

系统会自动：
- 解析 CSV/Excel 表头
- 推断字段分类
- 验证数据完整性
- 检测并跳过重复数据

### 4. 数据完整度

实时显示数据集完整度（覆盖率），包括：
- 综合覆盖率百分比
- 各字段填充率
- 低覆盖率记录提示

## 🔧 开发规范

### 代码风格

- 使用 TypeScript 严格模式
- 组件使用函数式组件 + Hooks
- 遵循 React 最佳实践
- 所有接口调用添加错误处理
- 关键操作添加 loading 状态

### 注释规范

- 文件头部添加功能说明
- 导出函数添加 JSDoc 注释
- 复杂逻辑添加行内注释

### 组件设计原则

- 单一职责，功能内聚
- Props 类型化，添加接口定义
- 状态最小化，避免冗余
- 合理拆分，提高复用性

## 📄 License

MIT

## 👥 联系方式

如有问题或建议，请联系项目维护者。
