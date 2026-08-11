-- ============================================================
-- 文件名: sql/02_dwd_clean.sql
-- 用途: DWD层数据清洗（处理带小数点的数字字符串）
-- ============================================================

USE user_behavior_db;

-- 1. 删除旧表
DROP TABLE IF EXISTS dwd_clean_logs;

-- 2. 创建清洗后明细表（字段类型先设为VARCHAR，确保写入）
CREATE TABLE dwd_clean_logs (
    user_id          VARCHAR(20)     COMMENT '用户ID（清洗后）',
    session_id       VARCHAR(50)     COMMENT '会话ID',
    event_type       VARCHAR(20)     COMMENT '事件类型',
    product_id       VARCHAR(20)     COMMENT '商品ID（清洗后）',
    event_time       DATETIME        COMMENT '事件时间（标准格式）',
    device_type      VARCHAR(20)     COMMENT '设备类型',
    ip               VARCHAR(20)     COMMENT 'IP地址',
    etl_timestamp    DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT 'ETL处理时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWD层：清洗后的用户行为明细';

-- 3. 清洗数据并插入
INSERT INTO dwd_clean_logs (user_id, session_id, event_type, product_id, event_time, device_type, ip)
SELECT 
    -- 清洗user_id：去掉'.0'后缀，并过滤空值
    CASE 
        WHEN user_id IS NULL OR TRIM(user_id) = '' OR TRIM(user_id) = 'NULL' THEN NULL
        ELSE REPLACE(REPLACE(TRIM(user_id), '.0', ''), '.', '')
    END AS user_id,
    
    -- session_id保持原样
    NULLIF(TRIM(session_id), '') AS session_id,
    
    -- event_type保持原样
    NULLIF(TRIM(event_type), '') AS event_type,
    
    -- 清洗product_id：同样去掉'.0'后缀
    CASE 
        WHEN product_id IS NULL OR TRIM(product_id) = '' OR TRIM(product_id) = 'NULL' THEN NULL
        ELSE REPLACE(REPLACE(TRIM(product_id), '.0', ''), '.', '')
    END AS product_id,
    
    -- 清洗event_time：只保留合法日期格式
    CASE 
        WHEN event_time REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2}$' 
        THEN STR_TO_DATE(event_time, '%Y-%m-%d %H:%i:%s')
        ELSE NULL
    END AS event_time,
    
    NULLIF(TRIM(device_type), '') AS device_type,
    NULLIF(TRIM(ip), '') AS ip

FROM ods_raw_logs
WHERE 
    -- 过滤掉user_id为空的记录（改为保留有效数据）
    user_id IS NOT NULL 
    AND TRIM(user_id) != ''
    AND TRIM(user_id) != 'NULL'
    AND session_id IS NOT NULL 
    AND TRIM(session_id) != '';