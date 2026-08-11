-- ============================================================
-- 文件名: sql/03_dws_aggregate.sql
-- 用途: DWS层汇总指标，基于DWD层计算业务KPI
-- ============================================================

USE user_behavior_db;

-- ============================================================
-- 汇总表1：每日访问汇总（PV、UV、人均访问次数）
-- ============================================================
DROP TABLE IF EXISTS dws_daily_metrics;

CREATE TABLE dws_daily_metrics (
    stat_date       DATE            PRIMARY KEY COMMENT '统计日期',
    pv              INT             COMMENT '页面浏览量（总事件数）',
    uv              INT             COMMENT '独立访客数（去重用户）',
    avg_visits_per_user DECIMAL(10,2) COMMENT '人均访问次数',
    total_orders    INT             COMMENT '下单总数',
    etl_timestamp   DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT 'ETL更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS层：每日核心指标汇总';

-- 插入数据
INSERT INTO dws_daily_metrics (stat_date, pv, uv, avg_visits_per_user, total_orders)
SELECT 
    DATE(event_time) AS stat_date,
    COUNT(*) AS pv,
    COUNT(DISTINCT user_id) AS uv,
    ROUND(COUNT(*) / NULLIF(COUNT(DISTINCT user_id), 0), 2) AS avg_visits_per_user,
    SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS total_orders
FROM dwd_clean_logs
WHERE event_time IS NOT NULL
GROUP BY DATE(event_time)
ORDER BY stat_date;


-- ============================================================
-- 汇总表2：每日事件类型分布
-- ============================================================
DROP TABLE IF EXISTS dws_daily_events;

CREATE TABLE dws_daily_events (
    stat_date       DATE            COMMENT '统计日期',
    event_type      VARCHAR(20)     COMMENT '事件类型',
    event_count     INT             COMMENT '事件数量',
    etl_timestamp   DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT 'ETL更新时间',
    PRIMARY KEY (stat_date, event_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS层：每日事件类型分布';

-- 插入数据
INSERT INTO dws_daily_events (stat_date, event_type, event_count)
SELECT 
    DATE(event_time) AS stat_date,
    event_type,
    COUNT(*) AS event_count
FROM dwd_clean_logs
WHERE event_time IS NOT NULL
GROUP BY DATE(event_time), event_type
ORDER BY stat_date, event_type;


-- ============================================================
-- 汇总表3：每小时流量趋势（用于观察波峰波谷）
-- ============================================================
DROP TABLE IF EXISTS dws_hourly_trend;

CREATE TABLE dws_hourly_trend (
    stat_hour       DATETIME        PRIMARY KEY COMMENT '统计小时（精确到小时）',
    pv              INT             COMMENT '该小时PV',
    uv              INT             COMMENT '该小时UV',
    etl_timestamp   DATETIME        DEFAULT CURRENT_TIMESTAMP COMMENT 'ETL更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='DWS层：每小时流量趋势';

-- 插入数据
INSERT INTO dws_hourly_trend (stat_hour, pv, uv)
SELECT 
    DATE_FORMAT(event_time, '%Y-%m-%d %H:00:00') AS stat_hour,
    COUNT(*) AS pv,
    COUNT(DISTINCT user_id) AS uv
FROM dwd_clean_logs
WHERE event_time IS NOT NULL
GROUP BY DATE_FORMAT(event_time, '%Y-%m-%d %H:00:00')
ORDER BY stat_hour;