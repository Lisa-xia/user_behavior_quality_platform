-- ============================================================
-- 文件名: sql/01_ods_create.sql
-- 用途: 创建ODS层原始日志表，并导入CSV数据
-- 说明: ODS层保持数据原样，不做任何清洗
-- ============================================================

-- 1. 创建数据库（如果不存在）
CREATE DATABASE IF NOT EXISTS user_behavior_db;
USE user_behavior_db;

-- 2. 删除旧表（如果存在，便于重复运行）
DROP TABLE IF EXISTS ods_raw_logs;

-- 3. 创建ODS层原始日志表
--    字段类型与CSV完全对应，所有字段均可为NULL（保留原始空值）
CREATE TABLE ods_raw_logs (
    user_id          VARCHAR(20)     COMMENT '用户ID（可能有空值）',
    session_id       VARCHAR(50)     COMMENT '会话ID',
    event_type       VARCHAR(20)     COMMENT '事件类型: click/view/purchase',
    product_id       VARCHAR(20)     COMMENT '商品ID（可能有空值）',
    event_time       VARCHAR(50)     COMMENT '事件时间（可能有格式错误）',
    device_type      VARCHAR(20)     COMMENT '设备类型: iOS/Android/Web',
    ip               VARCHAR(20)     COMMENT 'IP地址',
    -- 审计字段（记录数据加载时间）
    load_timestamp   DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT '数据加载时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='ODS层：用户行为原始日志';