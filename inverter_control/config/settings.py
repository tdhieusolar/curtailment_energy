# config/settings.py
"""
Cấu hình hệ thống - Phiên bản 0.5.0
"""

# Import cấu hình hệ thống từ cùng thư mục
from .system_config import SYSTEM_URLS, CONTROL_REQUESTS_OFF, CONTROL_REQUESTS_ON, ON_ALL

# --- CẤU HÌNH PHIÊN BẢN 0.5.0 - INTERACTIVE MENU ---
VERSION = "0.5.0"

CONFIG = {
    "version": VERSION,
    "credentials": {
        "username": "installer",
        "password": "Mo_g010rP!"
    },
    "driver": {
        "path": "/usr/bin/chromedriver",
        "headless": True,
        "timeout": 25,
        "page_load_timeout": 30,
        "element_timeout": 10,
        "action_timeout": 5,
        "max_pool_size": 8,
        "min_pool_size": 2
    },
    "performance": {
        "max_workers": 8,
        "retry_attempts": 1,
        "retry_delay": 1,
        "batch_size": 10,
        "max_retry_queue": 2,
        "tasks_per_driver": 5
    },
    "logging": {
        "level": "INFO",
        "format": f"%(asctime)s - %(levelname)s - [%(threadName)s] - v{VERSION} - %(message)s",
        "file": f"inverter_control_v{VERSION}.log"
    }
}