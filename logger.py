"""
基于loguru的日志系统
使用步骤：
1. 将该脚本引入到仓库
2. from 该脚本 import log
3. 在主入口脚本加： 
from logger_manager.log_manager import setup_logging

setup_logging(
    console_level="INFO",   # 控制台日志级别
    file_level="DEBUG",     # 文件日志级别
    log_file="logs/app.log" # 日志文件路径
)
这样全局日志格式、文件、级别等都统一。
"""
import sys
from loguru import logger
from pathlib import Path
from typing import Optional

class LogManager:
    _instance: Optional['LogManager'] = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._logger = logger
            self._initialized = True
    
    def setup(self, 
              console_level: str = "INFO",
              file_level: str = "DEBUG",
              log_file: str = "logs/app.log",
              enable_console: bool = True,
              enable_file: bool = True):
        """
        配置日志系统
        """
        # 移除所有现有处理器
        self._logger.remove()
        
        if enable_console:
            self._logger.add(
                sys.stderr,
                format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}:{function}:{line}</cyan> | <magenta>PID:{process}</magenta> | <yellow>TID:{thread}</yellow> - <level>{message}</level>",
                level=console_level,
                colorize=True
            )
        
        if enable_file:
            # 确保日志目录存在
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            self._logger.add(
                log_file,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | PID:{process} | TID:{thread} - {message}",
                level=file_level,
                rotation="10 MB",
                retention="7 days",
                compression="zip",
                encoding="utf-8"
            )
    
    @property
    def logger(self):
        return self._logger

# 全局实例
log_manager = LogManager()


# 便捷函数
def get_logger():
    return log_manager.logger

def setup_logging(**kwargs):
    log_manager.setup(**kwargs)
    return log_manager.logger

log = get_logger()