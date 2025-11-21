# config/settings.py
"""
Cấu hình hệ thống
"""

# Import cấu hình hệ thống từ cùng thư mục
from .system_config import SYSTEM_URLS, CONTROL_REQUESTS_OFF, CONTROL_REQUESTS_ON, ON_ALL

# --- CẤU HÌNH PHIÊN BẢN 0.4.1 - DYNAMIC DRIVER POOL ---
CONFIG = {
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
        "max_pool_size": 8,  # Số driver tối đa
        "min_pool_size": 2   # Số driver tối thiểu
    },
    "performance": {
        "max_workers": 8,
        "retry_attempts": 1,
        "retry_delay": 1,
        "batch_size": 10,
        "max_retry_queue": 2,
        "tasks_per_driver": 5  # Mỗi driver xử lý ~5 tasks
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s",
        "file": "inverter_control_v0.4.1.log"
    }
}