# ============================================================
# 文件名: quality_engine/logger.py
# 用途: 统一日志管理 - 同时输出到终端和文件
# ============================================================

import logging
import os
from datetime import datetime


def setup_logger(
    name="quality_engine",
    log_dir="./output",
    log_level=logging.INFO,
    console_level=logging.INFO,
    file_level=logging.DEBUG
):
    """
    配置并返回 logger 实例
    
    参数:
        name: logger 名称
        log_dir: 日志文件目录
        log_level: 根日志级别
        console_level: 控制台输出级别
        file_level: 文件输出级别
    
    返回:
        logging.Logger: 配置好的 logger 实例
    """
    # 确保日志目录存在
    os.makedirs(log_dir, exist_ok=True)
    
    # 创建 logger
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # 清除已有的 handlers（避免重复）
    if logger.handlers:
        logger.handlers.clear()
    
    # 日志格式
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台 Handler（INFO 级别）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件 Handler（DEBUG 级别，记录所有内容）
    log_filename = f"app_{datetime.now().strftime('%Y%m%d')}.log"
    log_path = os.path.join(log_dir, log_filename)
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(file_level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# 创建默认 logger 实例
default_logger = setup_logger()

# 快捷函数
def get_logger(name=None):
    """获取 logger 实例"""
    if name:
        return logging.getLogger(name)
    return default_logger


def set_log_level(level):
    """动态设置日志级别"""
    default_logger.setLevel(level)
    for handler in default_logger.handlers:
        handler.setLevel(level)