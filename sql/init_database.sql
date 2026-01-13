-- =====================================================
-- 焊接数据库初始化SQL脚本
-- 数据库名称: metal_welding
-- 创建时间: 2025-12-18
-- =====================================================

-- 使用数据库
USE metal_welding;

-- =====================================================
-- 1. 创建用户表
-- =====================================================
CREATE TABLE IF NOT EXISTS sys_users (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '用户ID',
    username VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    password VARCHAR(100) NOT NULL COMMENT '密码（明文）',
    role ENUM('root', 'admin', 'user') NOT NULL DEFAULT 'user' COMMENT '角色：root-超级管理员, admin-管理员, user-普通用户',
    status ENUM('active', 'disabled') NOT NULL DEFAULT 'active' COMMENT '状态：active-激活, disabled-禁用',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    last_login DATETIME COMMENT '最后登录时间',
    created_by VARCHAR(50) COMMENT '创建人',
    INDEX idx_username (username),
    INDEX idx_role (role),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- 插入默认用户
INSERT INTO sys_users (username, password, role, created_by) VALUES
('root', '123456', 'root', 'system'),
('admin', '123456', 'admin', 'system'),
('user', '123456', 'user', 'system')
ON DUPLICATE KEY UPDATE username=username;

-- =====================================================
-- 2. 创建导入任务表
-- =====================================================
CREATE TABLE IF NOT EXISTS sys_import_tasks (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '任务ID',
    task_id VARCHAR(100) NOT NULL UNIQUE COMMENT '任务唯一标识',
    batch_id VARCHAR(50) NOT NULL COMMENT '批次ID',
    filename VARCHAR(255) NOT NULL COMMENT '上传的文件名',
    file_path VARCHAR(500) COMMENT '文件存储路径',
    mode ENUM('append', 'replace') NOT NULL DEFAULT 'append' COMMENT '导入模式',
    status ENUM('pending', 'processing', 'completed', 'failed') NOT NULL DEFAULT 'pending' COMMENT '任务状态',
    progress INT NOT NULL DEFAULT 0 COMMENT '进度百分比',
    total_rows INT DEFAULT 0 COMMENT '总行数',
    current_row INT DEFAULT 0 COMMENT '当前处理行',
    success_count INT DEFAULT 0 COMMENT '成功导入数量',
    failed_count INT DEFAULT 0 COMMENT '失败数量',
    failed_rows JSON COMMENT '失败行详情',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '任务创建时间',
    started_at DATETIME COMMENT '开始处理时间',
    completed_at DATETIME COMMENT '完成时间',
    created_by VARCHAR(50) COMMENT '创建人',
    INDEX idx_task_id (task_id),
    INDEX idx_batch_id (batch_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='CSV导入任务表';

-- =====================================================
-- 3. 创建操作日志表
-- =====================================================
CREATE TABLE IF NOT EXISTS sys_operation_logs (
    id INT PRIMARY KEY AUTO_INCREMENT COMMENT '日志ID',
    user_id INT COMMENT '用户ID',
    username VARCHAR(50) COMMENT '用户名',
    operation_type ENUM('login', 'logout', 'create', 'update', 'delete', 'import', 'export') NOT NULL COMMENT '操作类型',
    target_type VARCHAR(50) COMMENT '操作对象类型',
    target_id VARCHAR(100) COMMENT '操作对象ID',
    batch_id VARCHAR(50) COMMENT '批次ID',
    description TEXT COMMENT '操作描述',
    request_method VARCHAR(10) COMMENT '请求方法',
    request_url VARCHAR(500) COMMENT '请求URL',
    request_ip VARCHAR(50) COMMENT '请求IP',
    user_agent VARCHAR(500) COMMENT '用户代理',
    status ENUM('success', 'failed') NOT NULL COMMENT '操作状态',
    error_message TEXT COMMENT '错误信息',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
    INDEX idx_user_id (user_id),
    INDEX idx_operation_type (operation_type),
    INDEX idx_batch_id (batch_id),
    INDEX idx_created_at (created_at),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='操作日志表';

-- =====================================================
-- 完成
-- =====================================================
SELECT '数据库系统表初始化完成!' AS message;
