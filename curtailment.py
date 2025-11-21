#!/usr/bin/env python3
"""
INVERTER CONTROL SYSTEM - Phiên bản All-in-One
Chương trình điều khiển inverter tự động - Tất cả trong một file
Phiên bản: 0.5.3 - Optimized Pool - Single File
"""

import math
import queue
import threading
import pandas as pd
import os
import sys
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import deque

# Selenium imports
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, WebDriverException

# =============================================================================
# CẤU HÌNH HỆ THỐNG
# =============================================================================

VERSION = "0.5.3"
EXCEL_CONFIG_FILE = "inverter_config.xlsx"

# Cấu hình hệ thống
CONFIG = {
    "version": VERSION,
    "excel_file": EXCEL_CONFIG_FILE,
    "credentials": {
        "username": "installer",
        "password": "Mo_g010rP!"
    },
    "driver": {
        "path": "/usr/bin/chromedriver",
        "headless": True,
        "timeout": 25,
        "page_load_timeout": 20,
        "element_timeout": 8,
        "action_timeout": 5,
        "max_pool_size": 8,
        "min_pool_size": 1
    },
    "performance": {
        "max_workers": 8,
        "retry_attempts": 1,
        "retry_delay": 1,
        "batch_size": 8,
        "max_retry_queue": 2,
        "tasks_per_driver": 4
    },
    "logging": {
        "level": "INFO",
        "format": f"%(asctime)s - %(levelname)s - [%(threadName)s] - v{VERSION} - %(message)s",
        "file": f"inverter_control_v{VERSION}.log"
    }
}

# Selectors cho web elements
SELECTORS = {
    "login": {
        "dropdown_toggle": "#login-dropdown-list > a.dropdown-toggle",
        "username_field": "login-username",
        "password_field": "login-password", 
        "login_button": "login-buttons-password",
        "user_indicator": "installer"
    },
    "grid_control": {
        "connect_link": "link-grid-disconnect",  # ID của thẻ a
        "status_indicator": ["Disconnect Grid", "Connect Grid"],  # Text trong span
        "status_image": "img[src*='flash']",  # Selector cho hình ảnh trạng thái
        "status_text": ".menu-text"  # Selector cho text trạng thái
    },
    "monitoring": {
        "status_line": "#status-line-dsp",
        "power_active": ".js-active-power",
        "navbar": ".navbar"
    }
}

# Cấu hình hệ thống mặc định
SYSTEM_URLS = {
    "Zone B": {
        "B2": {
            "INV-01": { "url": "10.10.10.101", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.102", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.103", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.104", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.105", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.106", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.107", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.108", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.109", "info": "Inverter số 9", "status": "OK"},
            "INV-10": { "url": "10.10.10.110", "info": "Inverter số 10", "status": "OK"},
        },
        "B3R1": {
            "INV-01": { "url": "10.10.10.121", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.122", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.123", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.124", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.125", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.126", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.127", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.128", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.129", "info": "Inverter số 9", "status": "OK"},
        },
        "B3R2": {
            "INV-01": { "url": "10.10.10.111", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.112", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.113", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.114", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.115", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.116", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.117", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.118", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.119", "info": "Inverter số 9", "status": "OK"},
        },
        "B4R1": {
            "INV-01": { "url": "10.10.10.141", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.142", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.143", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.144", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.145", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.146", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.147", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.148", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.149", "info": "Inverter số 9", "status": "OK"},
            "INV-10": { "url": "10.10.10.150", "info": "Inverter số 10", "status": "OK"},
        },        
        "B4R2": {
            "INV-01": { "url": "10.10.10.131", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.132", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.133", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.134", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.135", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.136", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.137", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.138", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.139", "info": "Inverter số 9", "status": "OK"},
            "INV-10": { "url": "10.10.10.140", "info": "Inverter số 10", "status": "OK"},
        },        
        "B5R1": {
            "INV-01": { "url": "10.10.10.161", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.162", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.163", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.164", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.165", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.166", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.167", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.168", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.169", "info": "Inverter số 9", "status": "OK"},
            "INV-10": { "url": "10.10.10.170", "info": "Inverter số 10", "status": "OK"},
        },
        "B5R2": {
            "INV-01": { "url": "10.10.10.151", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.152", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.153", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.154", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.155", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.156", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.157", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.158", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.159", "info": "Inverter số 9", "status": "OK"},
            "INV-10": { "url": "10.10.10.160", "info": "Inverter số 10", "status": "OK"},
        },
        "B6R1": {
            "INV-01": { "url": "10.10.10.181", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.182", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.183", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.184", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.185", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.186", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.187", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.188", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.189", "info": "Inverter số 9", "status": "OK"},
            "INV-10": { "url": "10.10.10.190", "info": "Inverter số 10", "status": "OK"},
        },
        "B6R2": {
            "INV-01": { "url": "10.10.10.171", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.172", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.173", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.174", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.175", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.176", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.177", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.178", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.179", "info": "Inverter số 9", "status": "OK"},
            "INV-10": { "url": "10.10.10.180", "info": "Inverter số 10", "status": "OK"},
        },
        "B7": {
            "INV-01": { "url": "10.10.10.191", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.192", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.193", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.194", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.195", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.196", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.197", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.198", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.199", "info": "Inverter số 9", "status": "OK"},
            "INV-10": { "url": "10.10.10.200", "info": "Inverter số 10", "status": "OK"},
        },
        "B8": {
            "INV-01": { "url": "10.10.10.201", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.202", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.203", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.204", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.205", "info": "Inverter số 5", "status": "OK"},
        },
        "B11": {
            "INV-01": { "url": "10.10.10.211", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.212", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.213", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.214", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.215", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.216", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.217", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.218", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.219", "info": "Inverter số 9", "status": "OK"},
            "INV-10": { "url": "10.10.10.220", "info": "Inverter số 10", "status": "OK"},
        },
        "B12": {
            "INV-01": { "url": "10.10.10.241", "info": "Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.242", "info": "Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.243", "info": "Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.244", "info": "Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.245", "info": "Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.246", "info": "Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.247", "info": "Inverter số 7", "status": "OK"},
            "INV-08": { "url": "10.10.10.248", "info": "Inverter số 8", "status": "OK"},
            "INV-09": { "url": "10.10.10.249", "info": "Inverter số 9", "status": "OK"},
            "INV-10": { "url": "10.10.10.250", "info": "Inverter số 10", "status": "OK"},
        },  
        "B13-14": {
            "INV-01": { "url": "10.10.10.221", "info": "B13 Inverter số 1", "status": "OK"},
            "INV-02": { "url": "10.10.10.222", "info": "B13 Inverter số 2", "status": "OK"},
            "INV-03": { "url": "10.10.10.223", "info": "B13 Inverter số 3", "status": "OK"},
            "INV-04": { "url": "10.10.10.224", "info": "B13 Inverter số 4", "status": "OK"},
            "INV-05": { "url": "10.10.10.225", "info": "B13 Inverter số 5", "status": "OK"},
            "INV-06": { "url": "10.10.10.226", "info": "B13 Inverter số 6", "status": "OK"},
            "INV-07": { "url": "10.10.10.231", "info": "B14 Inverter số 1", "status": "OK"},
            "INV-08": { "url": "10.10.10.232", "info": "B14 Inverter số 2", "status": "OK"},
            "INV-09": { "url": "10.10.10.233", "info": "B14 Inverter số 3", "status": "OK"},
            "INV-10": { "url": "10.10.10.234", "info": "B14 Inverter số 4", "status": "OK"},
        },
    }
}

# Các kịch bản điều khiển mặc định
CONTROL_REQUESTS_OFF = {
    "B3R1": {"action": "OFF", "count": 9},
    "B4R2": {"action": "OFF", "count": 10},
    "B5R2": {"action": "OFF", "count": 10},
    "B8": {"action": "OFF", "count": 4},
}

CONTROL_REQUESTS_ON = {
    "B3R1": {"action": "ON", "count": 9},
    "B4R2": {"action": "ON", "count": 10},
    "B5R2": {"action": "ON", "count": 10},
    "B8": {"action": "ON", "count": 4},
}

ON_ALL = {
    "B2": {"action": "ON", "count": 10},
    "B3R1": {"action": "ON", "count": 9},
    "B3R2": {"action": "ON", "count": 9},
    "B4R1": {"action": "ON", "count": 10},
    "B4R2": {"action": "ON", "count": 10},
    "B5R1": {"action": "ON", "count": 10},
    "B5R2": {"action": "ON", "count": 10},
    "B6R1": {"action": "ON", "count": 10},
    "B6R2": {"action": "ON", "count": 10},
    "B7": {"action": "ON", "count": 10},
    "B8": {"action": "ON", "count": 5},
    "B11": {"action": "ON", "count": 10},
    "B12": {"action": "ON", "count": 10},
    "B13-14": {"action": "ON", "count": 10},
}

# =============================================================================
# CORE CLASSES
# =============================================================================

class InverterControlLogger:
    """Lớp quản lý logging"""
    
    def __init__(self, config=None):
        self.config = config or CONFIG
        self.setup_logging()
        
    def setup_logging(self):
        """Thiết lập hệ thống logging"""
        logging.basicConfig(
            level=getattr(logging, self.config["logging"]["level"]),
            format=self.config["logging"]["format"],
            handlers=[
                logging.FileHandler(self.config["logging"]["file"], encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_success(self, message, inv_name=""):
        prefix = f"[{inv_name}] " if inv_name else ""
        self.logger.info(f"✅ {prefix}{message}")
    
    def log_error(self, message, inv_name=""):
        prefix = f"[{inv_name}] " if inv_name else ""
        self.logger.error(f"❌ {prefix}{message}")
    
    def log_warning(self, message, inv_name=""):
        prefix = f"[{inv_name}] " if inv_name else ""
        self.logger.warning(f"⚠️ {prefix}{message}")
    
    def log_info(self, message, inv_name=""):
        prefix = f"[{inv_name}] " if inv_name else ""
        self.logger.info(f"ℹ️ {prefix}{message}")
    
    def log_debug(self, message, inv_name=""):
        prefix = f"[{inv_name}] " if inv_name else ""
        self.logger.debug(f"🔍 {prefix}{message}")
    
    def log_version(self, version):
        self.logger.info(f"🚀 Khởi động Inverter Control v{version}")
    
    def log_queue_stats(self, stats):
        self.logger.info(f"📊 Hàng đợi - Chính: {stats['primary_queue']}, Retry: {stats['retry_queue']}, Hoàn thành: {stats['completed']}, Thất bại: {stats['failed']}")


class InverterTask:
    """Lớp đại diện cho một task inverter"""
    
    def __init__(self, full_inv_name, target_url, required_action, inv_status):
        self.full_inv_name = full_inv_name
        self.target_url = target_url
        self.required_action = required_action
        self.inv_status = inv_status
        self.retry_count = 0
        self.last_error = None
        self.created_time = datetime.now()
        self.priority = 1
    
    def __str__(self):
        return f"InverterTask({self.full_inv_name}, {self.required_action}, retry={self.retry_count})"
    
    def should_retry(self, max_retry_queue):
        return self.retry_count < max_retry_queue
    
    def mark_retry(self, error_msg=None):
        self.retry_count += 1
        self.last_error = error_msg
        self.priority = 2
        return self


class SmartTaskQueue:
    """Hàng đợi thông minh quản lý task và retry"""
    
    def __init__(self, config):
        self.config = config
        self.primary_queue = deque()
        self.retry_queue = deque()
        self.completed_tasks = []
        self.failed_tasks = []
        self.logger = InverterControlLogger(config)
        self.lock = threading.Lock()
    
    def add_tasks(self, tasks):
        with self.lock:
            for task in tasks:
                self.primary_queue.append(task)
            self.logger.log_info(f"📥 Đã thêm {len(tasks)} tasks vào hàng đợi chính")
    
    def get_next_batch(self, batch_size):
        with self.lock:
            batch = []
            while self.primary_queue and len(batch) < batch_size:
                batch.append(self.primary_queue.popleft())
            while self.retry_queue and len(batch) < batch_size:
                task = self.retry_queue.popleft()
                self.logger.log_info(f"🔄 Lấy task từ retry queue: {task.full_inv_name} (retry {task.retry_count})")
                batch.append(task)
            return batch
    
    def add_to_retry_queue(self, task, error_msg=None):
        with self.lock:
            if task.should_retry(self.config["performance"]["max_retry_queue"]):
                task.mark_retry(error_msg)
                self.retry_queue.append(task)
                self.logger.log_warning(f"⏳ Đã chuyển {task.full_inv_name} sang retry queue (lần {task.retry_count})")
                return True
            else:
                self.failed_tasks.append(task)
                self.logger.log_error(f"💥 Task {task.full_inv_name} đã vượt quá số lần retry tối đa")
                return False
    
    def mark_completed(self, task, status, message):
        with self.lock:
            task.completion_status = status
            task.completion_message = message
            task.completed_time = datetime.now()
            self.completed_tasks.append(task)
    
    def has_pending_tasks(self):
        with self.lock:
            return len(self.primary_queue) > 0 or len(self.retry_queue) > 0
    
    def get_stats(self):
        with self.lock:
            return {
                "primary_queue": len(self.primary_queue),
                "retry_queue": len(self.retry_queue),
                "completed": len(self.completed_tasks),
                "failed": len(self.failed_tasks),
                "total_retries": sum(task.retry_count for task in self.completed_tasks + self.failed_tasks)
            }


class DynamicDriverPool:
    """Pool quản lý driver động với pool size tối ưu"""
    
    def __init__(self, config):
        self.config = config
        self.available_drivers = queue.Queue()
        self.in_use_drivers = set()
        self.lock = threading.Lock()
        self.logger = InverterControlLogger(config)
        self.is_initialized = False
        self.pool_size = 0
        self.driver_semaphore = threading.Semaphore(0)
        
    def initialize_pool(self, total_tasks):
        if self.is_initialized:
            self.logger.log_info("✅ Driver pool đã được khởi tạo trước đó")
            return True
            
        self.pool_size = self._calculate_optimal_pool_size(total_tasks)
        
        if total_tasks == 1:
            self.pool_size = 1
            self.logger.log_info(f"🔄 Chỉ có 1 task → khởi tạo 1 driver")
        else:
            self.logger.log_info(f"🔄 Khởi tạo {self.pool_size} drivers cho {total_tasks} tasks")
        
        successful_drivers = 0
        
        for i in range(self.pool_size):
            driver = self._create_driver_robust()
            if driver:
                self.available_drivers.put(driver)
                successful_drivers += 1
                self.driver_semaphore.release()
                self.logger.log_debug(f"✅ Đã khởi tạo driver {successful_drivers}/{self.pool_size}")
        
        if successful_drivers == 0:
            self.logger.log_error("❌ Không thể khởi tạo driver nào!")
            return False
            
        self.is_initialized = True
        
        if total_tasks == 1:
            self.logger.log_info(f"✅ Đã khởi tạo 1 driver cho 1 task")
        else:
            self.logger.log_info(f"✅ Đã khởi tạo {successful_drivers}/{self.pool_size} drivers thành công")
        
        return True
    
    def _calculate_optimal_pool_size(self, total_tasks):
        if total_tasks == 1:
            return 1
        
        if total_tasks <= 3:
            calculated_size = min(2, total_tasks)
        else:
            calculated_size = math.ceil(total_tasks / self.config["performance"]["tasks_per_driver"])
        
        optimal_size = max(self.config["driver"]["min_pool_size"], 
                          min(self.config["driver"]["max_pool_size"], calculated_size))
        optimal_size = min(optimal_size, total_tasks)
        
        self.logger.log_info(f"📊 Tính toán pool size: {total_tasks} tasks → {optimal_size} drivers")
        return optimal_size
    
    def _create_driver_robust(self):
        try:
            service = Service(self.config["driver"]["path"])
            
            chrome_options = webdriver.ChromeOptions()
            if self.config["driver"]["headless"]:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            chrome_options.page_load_strategy = 'eager'
            chrome_options.add_experimental_option("prefs", {
                "profile.managed_default_content_settings.images": 2,
            })
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(self.config["driver"]["page_load_timeout"])
            driver.implicitly_wait(2)
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except WebDriverException as e:
            self.logger.log_error(f"❌ Lỗi WebDriver: {e}")
            return None
        except Exception as e:
            self.logger.log_error(f"❌ Lỗi tạo driver: {e}")
            return None
    
    def get_driver(self, timeout=20):
        if not self.is_initialized:
            self.logger.log_error("❌ Driver pool chưa khởi tạo")
            return None
            
        if not self.driver_semaphore.acquire(timeout=timeout):
            self.logger.log_warning("⚠️ Timeout khi chờ driver")
            return None
            
        try:
            driver = self.available_drivers.get_nowait()
            with self.lock:
                self.in_use_drivers.add(driver)
            
            available_count = self.available_drivers.qsize()
            self.logger.log_debug(f"📥 Lấy driver, còn {available_count} available")
            return driver
            
        except queue.Empty:
            self.driver_semaphore.release()
            self.logger.log_error("❌ Lỗi đồng bộ: semaphore nhưng queue rỗng")
            return None
    
    def return_driver(self, driver):
        if driver is None:
            return
            
        if not self.is_initialized:
            try:
                driver.quit()
            except:
                pass
            return
        
        try:
            driver.current_url
        except Exception as e:
            self.logger.log_warning(f"⚠️ Driver không hoạt động, đóng: {e}")
            try:
                driver.quit()
            except:
                pass
            
            new_driver = self._create_driver_robust()
            if new_driver:
                self.available_drivers.put(new_driver)
                self.driver_semaphore.release()
                self.logger.log_info("🔄 Đã thay thế driver hỏng")
            return
        
        try:
            driver.delete_all_cookies()
        except Exception as e:
            self.logger.log_debug(f"🔧 Lỗi reset driver: {e}")
        
        with self.lock:
            if driver in self.in_use_drivers:
                self.in_use_drivers.remove(driver)
        
        self.available_drivers.put(driver)
        self.driver_semaphore.release()
        
        available_count = self.available_drivers.qsize()
        self.logger.log_debug(f"📤 Trả driver, có {available_count} available")
    
    def cleanup(self):
        if not self.is_initialized:
            return
            
        self.logger.log_info("🧹 Dọn dẹp driver pool...")
        
        closed_count = 0
        while not self.available_drivers.empty():
            try:
                driver = self.available_drivers.get_nowait()
                driver.quit()
                closed_count += 1
                try:
                    self.driver_semaphore.acquire(blocking=False)
                except:
                    pass
            except:
                pass
        
        with self.lock:
            for driver in self.in_use_drivers.copy():
                try:
                    driver.quit()
                    closed_count += 1
                except:
                    pass
            self.in_use_drivers.clear()
        
        self.is_initialized = False
        self.logger.log_info(f"✅ Đã đóng {closed_count} drivers")
    
    def get_pool_info(self):
        with self.lock:
            return {
                "pool_size": self.pool_size,
                "available": self.available_drivers.qsize(),
                "in_use": len(self.in_use_drivers),
                "semaphore_value": self.driver_semaphore._value,
                "is_initialized": self.is_initialized
            }


class InverterController:
    """Lớp điều khiển inverter"""
    
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.logger = InverterControlLogger(config)
    
    def wait_for_element(self, by, value, timeout=None):
        try:
            wait_timeout = timeout or self.config["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            return None
    
    def wait_for_element_clickable(self, by, value, timeout=None):
        try:
            wait_timeout = timeout or self.config["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            return None
    
    def wait_for_text_present(self, by, value, text, timeout=None):
        try:
            wait_timeout = timeout or self.config["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.text_to_be_present_in_element((by, value), text))
        except TimeoutException:
            return False
    
    def wait_for_page_loaded(self, timeout=None):
        try:
            wait_timeout = timeout or self.config["driver"]["page_load_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            return False
    
    def fast_login(self, url, username=None, password=None):
        username = username or self.config["credentials"]["username"]
        password = password or self.config["credentials"]["password"]
        
        try:
            if not url.startswith(('http://', 'https://')):
                url = f"http://{url}"
            
            self.driver.get(url)
            
            if not self.wait_for_page_loaded(timeout=10):
                self.logger.log_debug("Trang load chậm, tiếp tục thử...")
            
            if self.wait_for_text_present(By.TAG_NAME, "body", "installer", timeout=1):
                self.logger.log_debug("Đã đăng nhập sẵn")
                return True
            
            dropdown = self.wait_for_element_clickable(
                By.CSS_SELECTOR, SELECTORS["login"]["dropdown_toggle"], timeout=2
            )
            if dropdown:
                dropdown.click()
                self.wait_for_element(By.ID, SELECTORS["login"]["username_field"], timeout=1)
            
            username_field = self.wait_for_element(By.ID, SELECTORS["login"]["username_field"], timeout=2)
            if not username_field:
                self.logger.log_debug("Không tìm thấy field username, có thể đã đăng nhập")
                return True
            
            username_field.clear()
            username_field.send_keys(username)
            
            password_field = self.wait_for_element(By.ID, SELECTORS["login"]["password_field"], timeout=2)
            if not password_field:
                self.logger.log_debug("Không tìm thấy field password")
                return False
            
            password_field.clear()
            password_field.send_keys(password)
            
            login_btn = self.wait_for_element_clickable(By.ID, SELECTORS["login"]["login_button"], timeout=2)
            if not login_btn:
                self.logger.log_debug("Không tìm thấy nút đăng nhập")
                return False
            
            login_btn.click()
            
            if self.wait_for_text_present(By.TAG_NAME, "body", "installer", timeout=5):
                self.logger.log_debug("Đăng nhập thành công")
                return True
            
            if self.wait_for_element(By.CSS_SELECTOR, SELECTORS["monitoring"]["navbar"], timeout=2):
                self.logger.log_debug("Đăng nhập thành công (qua navbar)")
                return True
            
            self.logger.log_debug("Không xác định được trạng thái đăng nhập")
            return False
                
        except Exception as e:
            self.logger.log_debug(f"Login thất bại: {e}")
            return False
    
    def get_grid_status(self):
        try:
            link_element = self.wait_for_element(
                By.ID, SELECTORS["grid_control"]["connect_link"], timeout=3
            )
            
            if not link_element:
                self.logger.log_debug("Không tìm thấy element grid control")
                return None
            
            status_text_element = link_element.find_element(By.CSS_SELECTOR, SELECTORS["grid_control"]["status_text"])
            status_text = status_text_element.text.strip() if status_text_element else ""
            
            img_element = link_element.find_element(By.CSS_SELECTOR, SELECTORS["grid_control"]["status_image"])
            img_src = img_element.get_attribute("src") if img_element else ""
            
            self.logger.log_debug(f"Trạng thái grid - Text: '{status_text}', Image: '{img_src}'")
            
            if "Disconnect Grid" in status_text:
                return "Disconnect Grid"
            elif "Connect Grid" in status_text:
                return "Connect Grid"
            else:
                if "flash_off" in img_src:
                    return "Disconnect Grid"
                elif "flash_on" in img_src:
                    return "Connect Grid"
                else:
                    return status_text
                    
        except Exception as e:
            self.logger.log_debug(f"Lỗi khi lấy trạng thái grid: {e}")
            return None
    
    def perform_grid_action(self, target_action):
        current_status = self.get_grid_status()
        
        if not current_status:
            return False, "Không thể xác định trạng thái hiện tại"
        
        self.logger.log_debug(f"Trạng thái hiện tại: '{current_status}', Hành động mong muốn: '{target_action}'")
        
        if target_action == "ON":
            expected_status_after = "Disconnect Grid"
            should_perform_action = current_status == "Connect Grid"
        elif target_action == "OFF":
            expected_status_after = "Connect Grid"
            should_perform_action = current_status == "Disconnect Grid"
        else:
            return False, f"Hành động không hợp lệ: {target_action}"
        
        if not should_perform_action:
            status_message = f"BỎ QUA: Đã ở trạng thái mong muốn (Hiện tại: {current_status})"
            self.logger.log_debug(status_message)
            return True, status_message
        
        try:
            link_element = self.wait_for_element_clickable(
                By.ID, SELECTORS["grid_control"]["connect_link"], timeout=3
            )
            if not link_element:
                return False, "Không tìm thấy element điều khiển grid"
            
            self.logger.log_debug(f"Thực hiện {target_action} grid...")
            
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_element)
            
            actions = ActionChains(self.driver)
            actions.move_to_element(link_element).double_click().perform()
            
            self.logger.log_debug("Đã thực hiện double click, chờ trạng thái thay đổi...")
            
            status_changed = False
            for i in range(6):
                import time
                time.sleep(0.5)
                new_status = self.get_grid_status()
                self.logger.log_debug(f"Lần {i+1}: Trạng thái mới: '{new_status}'")
                
                if new_status == expected_status_after:
                    status_changed = True
                    break
                elif new_status != current_status:
                    self.logger.log_debug(f"Trạng thái đã thay đổi từ '{current_status}' sang '{new_status}'")
                    break
            
            if status_changed:
                final_status = self.get_grid_status()
                return True, f"THÀNH CÔNG: Chuyển từ '{current_status}' sang '{final_status}'"
            else:
                final_status = self.get_grid_status()
                return False, f"LỖI: Trạng thái không thay đổi như mong đợi (Hiện tại: {final_status}, Mong đợi: {expected_status_after})"
                
        except StaleElementReferenceException:
            try:
                self.logger.log_debug("Element bị stale, thử lại...")
                link_element = self.wait_for_element_clickable(
                    By.ID, SELECTORS["grid_control"]["connect_link"], timeout=2
                )
                if link_element:
                    actions = ActionChains(self.driver)
                    actions.move_to_element(link_element).double_click().perform()
                    
                    import time
                    time.sleep(2)
                    new_status = self.get_grid_status()
                    if new_status == expected_status_after:
                        return True, f"THÀNH CÔNG: Chuyển từ '{current_status}' sang '{new_status}'"
                    else:
                        return False, f"LỖI: Trạng thái không thay đổi (Hiện tại: {new_status})"
                else:
                    return False, "LỖI: Không thể tìm thấy element sau khi retry"
            except Exception as retry_e:
                return False, f"LỖI THỰC HIỆN (retry): {retry_e}"
                
        except Exception as e:
            return False, f"LỖI THỰC HIỆN: {str(e)}"


class TaskProcessor:
    """Xử lý tác vụ với tối ưu cho ít tasks"""
    
    def __init__(self, config, system_urls):
        self.config = config
        self.system_urls = system_urls
        self.logger = InverterControlLogger(config)
        self.task_queue = SmartTaskQueue(config)
        self.driver_pool = DynamicDriverPool(config)
        self.active_tasks = 0
        self.active_lock = threading.Lock()
    
    def prepare_tasks(self, control_requests):
        tasks = []
        total_inverters = 0
        
        for zone_name, stations in self.system_urls.items():
            for station_name, inverters in stations.items():
                if station_name in control_requests:
                    request = control_requests[station_name]
                    required_action = request["action"]
                    required_count = request["count"]
                    
                    sorted_invs = sorted(inverters.items())
                    count_added = 0
                    
                    for inv_name, inv_info in sorted_invs:
                        if count_added >= required_count:
                            break
                            
                        full_inv_name = f"{station_name}-{inv_name}"
                        target_url = inv_info["url"]
                        inv_status = inv_info.get("status", "OK").upper()
                        
                        task = InverterTask(full_inv_name, target_url, required_action, inv_status)
                        tasks.append(task)
                        count_added += 1
                        total_inverters += 1
        
        return tasks, total_inverters
    
    def process_single_inverter(self, task):
        with self.active_lock:
            self.active_tasks += 1
            current_active = self.active_tasks
        
        self.logger.log_debug(f"🎯 Bắt đầu xử lý {task.required_action} (active: {current_active})", task.full_inv_name)
        
        try:
            driver = self.driver_pool.get_driver(timeout=25)
            if not driver:
                return task, "RETRY", "Không lấy được driver từ pool"
            
            controller = InverterController(driver, self.config)
            login_success = controller.fast_login(task.target_url)
            
            if not login_success:
                self.driver_pool.return_driver(driver)
                return task, "RETRY", "Đăng nhập thất bại"
            
            success, message = controller.perform_grid_action(task.required_action)
            self.driver_pool.return_driver(driver)
            
            if success:
                status = "SUCCESS"
                self.logger.log_success(message, task.full_inv_name)
            else:
                if "BỎ QUA" in message:
                    status = "SUCCESS"
                    self.logger.log_info(message, task.full_inv_name)
                else:
                    status = "RETRY"
                    self.logger.log_warning(message, task.full_inv_name)
            
            return task, status, message
            
        except Exception as e:
            error_msg = f"Lỗi xử lý: {str(e)}"
            self.logger.log_error(error_msg, task.full_inv_name)
            return task, "RETRY", error_msg
        finally:
            with self.active_lock:
                self.active_tasks -= 1
    
    def run_parallel_optimized(self, control_requests):
        start_time = datetime.now()
        
        tasks, total_inverters = self.prepare_tasks(control_requests)
        total_tasks = len(tasks)
        
        self.logger.log_info(f"🚀 Bắt đầu xử lý {total_tasks} tasks - Phiên bản {VERSION}")
        
        if total_tasks == 0:
            self.logger.log_warning("⚠️ Không có tác vụ nào để xử lý!")
            return []
        
        self.logger.log_info("🔄 Đang khởi tạo driver pool...")
        if not self.driver_pool.initialize_pool(total_tasks):
            self.logger.log_error("❌ Không thể khởi tạo driver pool!")
            return []
        
        pool_info = self.driver_pool.get_pool_info()
        self.logger.log_info(f"🎯 Driver pool: {pool_info['pool_size']} drivers")
        
        self.task_queue.add_tasks(tasks)
        
        if total_tasks == 1:
            completed_count = self._process_single_task()
        elif total_tasks <= 3:
            completed_count = self._process_few_tasks(total_tasks)
        else:
            completed_count = self._process_many_tasks(total_tasks)
        
        final_results = self._get_final_results()
        self._analyze_results(final_results, start_time, total_tasks)
        
        self.driver_pool.cleanup()
        return final_results
    
    def _process_single_task(self):
        self.logger.log_info("🔸 Chế độ tối ưu: 1 task → xử lý tuần tự")
        
        batch_tasks = self.task_queue.get_next_batch(1)
        if not batch_tasks:
            return 0
        
        task = batch_tasks[0]
        try:
            processed_task, status, message = self.process_single_inverter(task)
            
            if status in ["SUCCESS", "SKIPPED"]:
                self.task_queue.mark_completed(processed_task, status, message)
                return 1
            elif status == "RETRY":
                if self.task_queue.add_to_retry_queue(processed_task, message):
                    self.logger.log_warning(f"⏳ Task {task.full_inv_name} chuyển sang retry queue")
                else:
                    self.task_queue.mark_completed(processed_task, "FAILED", message)
            else:
                self.task_queue.mark_completed(processed_task, status, message)
                
        except Exception as e:
            self.logger.log_error(f"Lỗi xử lý task: {e}", task.full_inv_name)
            if self.task_queue.add_to_retry_queue(task, str(e)):
                self.logger.log_warning(f"⏳ Task {task.full_inv_name} chuyển sang retry queue do lỗi")
        
        return 0
    
    def _process_few_tasks(self, total_tasks):
        self.logger.log_info(f"🔸 Chế độ tối ưu: {total_tasks} tasks → xử lý đơn giản")
        
        completed_count = 0
        batch_tasks = self.task_queue.get_next_batch(total_tasks)
        
        if not batch_tasks:
            return 0
        
        with ThreadPoolExecutor(max_workers=len(batch_tasks)) as executor:
            future_to_task = {
                executor.submit(self.process_single_inverter, task): task 
                for task in batch_tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    processed_task, status, message = future.result(timeout=30)
                    
                    if status in ["SUCCESS", "SKIPPED"]:
                        self.task_queue.mark_completed(processed_task, status, message)
                        completed_count += 1
                    elif status == "RETRY":
                        if self.task_queue.add_to_retry_queue(processed_task, message):
                            self.logger.log_warning(f"⏳ Task {task.full_inv_name} chuyển sang retry queue")
                    else:
                        self.task_queue.mark_completed(processed_task, status, message)
                        
                except Exception as e:
                    self.logger.log_error(f"Lỗi future: {e}", task.full_inv_name)
                    if self.task_queue.add_to_retry_queue(task, str(e)):
                        self.logger.log_warning(f"⏳ Task {task.full_inv_name} chuyển sang retry queue do timeout")
        
        return completed_count
    
    def _process_many_tasks(self, total_tasks):
        self.logger.log_info(f"🔸 Chế độ tiêu chuẩn: {total_tasks} tasks → xử lý song song")
        
        completed_count = 0
        batch_number = 0
        
        while self.task_queue.has_pending_tasks():
            batch_number += 1
            batch_stats = self._process_batch_with_limits(batch_number)
            completed_count += batch_stats["completed"]
            
            queue_stats = self.task_queue.get_stats()
            progress_percent = (completed_count / total_tasks) * 100
            
            self.logger.log_info(
                f"📦 Batch {batch_number}: {batch_stats['completed']} hoàn thành, "
                f"{batch_stats['retried']} retry, {batch_stats['failed']} thất bại"
            )
            self.logger.log_info(f"📈 Tiến trình: {completed_count}/{total_tasks} ({progress_percent:.1f}%)")
            
            if queue_stats["primary_queue"] == 0 and queue_stats["retry_queue"] < 2:
                self.logger.log_info("⏹️ Chỉ còn ít tasks retry, kết thúc sớm")
                break
        
        final_retry_stats = self._process_final_retry()
        completed_count += final_retry_stats["completed"]
        
        return completed_count
    
    def _process_batch_with_limits(self, batch_number):
        batch_stats = {"completed": 0, "retried": 0, "failed": 0}
        
        pool_info = self.driver_pool.get_pool_info()
        max_concurrent = min(
            self.config["performance"]["max_workers"],
            pool_info["available"] + 2
        )
        
        batch_tasks = self.task_queue.get_next_batch(max_concurrent)
        
        if not batch_tasks:
            return batch_stats
        
        self.logger.log_debug(f"🔄 Batch {batch_number}: {len(batch_tasks)} tasks, {max_concurrent} concurrent")
        
        with ThreadPoolExecutor(max_workers=len(batch_tasks)) as executor:
            future_to_task = {
                executor.submit(self.process_single_inverter, task): task 
                for task in batch_tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    processed_task, status, message = future.result(timeout=30)
                    
                    if status in ["SUCCESS", "SKIPPED"]:
                        self.task_queue.mark_completed(processed_task, status, message)
                        batch_stats["completed"] += 1
                    elif status == "RETRY":
                        if self.task_queue.add_to_retry_queue(processed_task, message):
                            batch_stats["retried"] += 1
                        else:
                            batch_stats["failed"] += 1
                    else:
                        self.task_queue.mark_completed(processed_task, status, message)
                        batch_stats["failed"] += 1
                        
                except Exception as e:
                    self.logger.log_error(f"Lỗi future: {e}", task.full_inv_name)
                    if self.task_queue.add_to_retry_queue(task, str(e)):
                        batch_stats["retried"] += 1
                    else:
                        batch_stats["failed"] += 1
        
        return batch_stats
    
    def _process_final_retry(self):
        queue_stats = self.task_queue.get_stats()
        if queue_stats["retry_queue"] == 0:
            return {"completed": 0, "retried": 0, "failed": 0}
        
        self.logger.log_info(f"🔄 Xử lý {queue_stats['retry_queue']} tasks retry cuối cùng")
        
        final_stats = {"completed": 0, "retried": 0, "failed": 0}
        batch_tasks = self.task_queue.get_next_batch(queue_stats["retry_queue"])
        
        for task in batch_tasks:
            try:
                processed_task, status, message = self.process_single_inverter(task)
                
                if status in ["SUCCESS", "SKIPPED"]:
                    self.task_queue.mark_completed(processed_task, status, message)
                    final_stats["completed"] += 1
                else:
                    self.task_queue.mark_completed(processed_task, "FAILED", f"Final retry failed: {message}")
                    final_stats["failed"] += 1
                    
            except Exception as e:
                self.logger.log_error(f"Final retry error: {e}", task.full_inv_name)
                self.task_queue.mark_completed(task, "FAILED", "Final retry timeout")
                final_stats["failed"] += 1
        
        return final_stats
    
    def _get_final_results(self):
        results = []
        
        for task in self.task_queue.completed_tasks:
            results.append((task.full_inv_name, task.completion_status, task.completion_message))
        
        for task in self.task_queue.failed_tasks:
            results.append((task.full_inv_name, "FAILED", f"Vượt quá số lần retry: {task.last_error}"))
        
        return results
    
    def _analyze_results(self, results, start_time, total_tasks):
        end_time = datetime.now()
        duration = end_time - start_time
        
        stats = {"SUCCESS": 0, "FAILED": 0, "SKIPPED": 0}
        for _, status, _ in results:
            stats[status] = stats.get(status, 0) + 1
        
        queue_stats = self.task_queue.get_stats()
        
        self.logger.log_info("=" * 60)
        self.logger.log_info(f"🎯 BÁO CÁO TỔNG KẾT - PHIÊN BẢN {VERSION}")
        self.logger.log_info("=" * 60)
        self.logger.log_info(f"📦 Tổng số tác vụ: {total_tasks}")
        self.logger.log_info(f"🎯 Số drivers sử dụng: {self.driver_pool.get_pool_info()['pool_size']}")
        self.logger.log_info(f"✅ Thành công: {stats['SUCCESS']}")
        self.logger.log_info(f"❌ Thất bại: {stats['FAILED']}")
        self.logger.log_info(f"⏭️ Bỏ qua: {stats['SKIPPED']}")
        self.logger.log_info(f"🔄 Tổng số lần retry: {queue_stats['total_retries']}")
        
        if total_tasks > 0:
            success_rate = (stats['SUCCESS'] / total_tasks) * 100
            self.logger.log_info(f"📊 Tỷ lệ thành công: {success_rate:.1f}%")
        
        total_seconds = duration.total_seconds()
        if total_tasks > 0:
            avg_time = total_seconds / total_tasks
            self.logger.log_info(f"⏱️ Thời gian trung bình/task: {avg_time:.2f}s")
        
        self.logger.log_info(f"🕒 Tổng thời gian thực hiện: {duration}")
        
        errors = [(name, msg) for name, status, msg in results if status == "FAILED"]
        if errors:
            self.logger.log_info("🔍 CHI TIẾT LỖI:")
            for name, msg in errors:
                self.logger.log_error(msg, name)


class ExcelConfigReader:
    """Lớp đọc cấu hình từ file Excel"""
    
    def __init__(self, excel_file_path="inverter_config.xlsx"):
        self.excel_file_path = excel_file_path
        self.logger = self._create_logger()
        self.required_sheets = ['Stations', 'Control_Scenarios']
    
    def _create_logger(self):
        class SimpleLogger:
            def __init__(self):
                logging.basicConfig(
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - [ExcelReader] - %(message)s",
                    handlers=[logging.StreamHandler(sys.stdout)]
                )
                self.logger = logging.getLogger(__name__)
            
            def log_info(self, message):
                self.logger.info(f"ℹ️ {message}")
            
            def log_error(self, message):
                self.logger.error(f"❌ {message}")
            
            def log_warning(self, message):
                self.logger.warning(f"⚠️ {message}")
        
        return SimpleLogger()
    
    def check_excel_file(self):
        if not os.path.exists(self.excel_file_path):
            self.logger.log_error(f"File Excel không tồn tại: {self.excel_file_path}")
            return False
        
        try:
            excel_file = pd.ExcelFile(self.excel_file_path)
            missing_sheets = []
            
            for sheet in self.required_sheets:
                if sheet not in excel_file.sheet_names:
                    missing_sheets.append(sheet)
            
            if missing_sheets:
                self.logger.log_error(f"Thiếu sheets: {', '.join(missing_sheets)}")
                return False
            
            self.logger.log_info(f"✅ File Excel hợp lệ: {self.excel_file_path}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Lỗi kiểm tra file Excel: {e}")
            return False
    
    def read_stations_config(self):
        try:
            df = pd.read_excel(self.excel_file_path, sheet_name='Stations')
            
            required_columns = ['Zone', 'Station', 'Inverter', 'URL', 'Status']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.log_error(f"Thiếu cột trong sheet Stations: {', '.join(missing_columns)}")
                return None
            
            system_urls = {}
            
            for _, row in df.iterrows():
                zone = row['Zone']
                station = row['Station']
                inverter = row['Inverter']
                url = row['URL']
                status = row.get('Status', 'OK')
                info = row.get('Info', f'Inverter {inverter}')
                
                if zone not in system_urls:
                    system_urls[zone] = {}
                
                if station not in system_urls[zone]:
                    system_urls[zone][station] = {}
                
                system_urls[zone][station][inverter] = {
                    "url": url,
                    "info": info,
                    "status": status
                }
            
            self.logger.log_info(f"✅ Đã đọc cấu hình {len(system_urls)} zones từ Excel")
            return system_urls
            
        except Exception as e:
            self.logger.log_error(f"Lỗi đọc stations từ Excel: {e}")
            return None
    
    def read_control_scenarios(self):
        try:
            df = pd.read_excel(self.excel_file_path, sheet_name='Control_Scenarios')
            
            required_columns = ['Station', 'Action', 'Count']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.log_error(f"Thiếu cột trong sheet Control_Scenarios: {', '.join(missing_columns)}")
                return {}
            
            scenarios = {
                "Tắt một số inverter": {},
                "Bật một số inverter": {},
                "Bật tất cả inverter": {}
            }
            
            system_stations = self.read_stations_config()
            if system_stations:
                all_stations = {}
                for zone_name, stations in system_stations.items():
                    for station_name, inverters in stations.items():
                        all_stations[station_name] = len(inverters)
                
                for station, count in all_stations.items():
                    scenarios["Bật tất cả inverter"][station] = {
                        "action": "ON",
                        "count": count
                    }
            
            for _, row in df.iterrows():
                station = row['Station']
                action = row['Action']
                count = row['Count']
                
                if action == 'OFF':
                    scenario_name = "Tắt một số inverter"
                elif action == 'ON':
                    scenario_name = "Bật một số inverter"
                else:
                    self.logger.log_warning(f"Action không hợp lệ: {action}, bỏ qua")
                    continue
                
                scenarios[scenario_name][station] = {
                    "action": action,
                    "count": count
                }
            
            self.logger.log_info(f"✅ Đã đọc {len([s for s in scenarios.values() if s])} scenarios từ Excel")
            return scenarios
            
        except Exception as e:
            self.logger.log_error(f"Lỗi đọc scenarios từ Excel: {e}")
            return {}
    
    def get_available_scenarios(self):
        scenarios = self.read_control_scenarios()
        if not scenarios:
            self.logger.log_warning("⚠️ Không có scenarios nào trong file Excel")
            return {}
        
        scenario_list = {}
        index = 1
        
        for scenario_name, requests in scenarios.items():
            if requests:
                scenario_list[str(index)] = {
                    "name": scenario_name,
                    "requests": requests
                }
                index += 1
        
        self.logger.log_info(f"✅ Đã tạo {len(scenario_list)} scenarios cho menu")
        return scenario_list
    
    def validate_scenario_with_system(self, scenario_requests, system_urls):
        errors = []
        warnings = []
        
        for station, request in scenario_requests.items():
            station_exists = False
            for zone_name, stations in system_urls.items():
                if station in stations:
                    station_exists = True
                    
                    available_inverters = len(stations[station])
                    requested_count = request["count"]
                    
                    if requested_count > available_inverters:
                        warnings.append(f"Station {station}: Yêu cầu {requested_count} nhưng chỉ có {available_inverters} inverter")
                    
                    action = request["action"]
                    if action not in ['ON', 'OFF']:
                        errors.append(f"Station {station}: Action '{action}' không hợp lệ (phải là ON hoặc OFF)")
                    
                    break
            
            if not station_exists:
                errors.append(f"Station '{station}' không tồn tại trong hệ thống")
        
        return errors, warnings

    def create_excel_template(self):
        try:
            stations_data = {
                'Zone': ['Zone B', 'Zone B', 'Zone B', 'Zone B', 'Zone B', 'Zone B', 'Zone B', 'Zone B'],
                'Station': ['B3R1', 'B3R1', 'B3R1', 'B4R2', 'B4R2', 'B5R2', 'B5R2', 'B8'],
                'Inverter': ['INV-01', 'INV-02', 'INV-03', 'INV-01', 'INV-02', 'INV-01', 'INV-02', 'INV-01'],
                'URL': ['10.10.10.121', '10.10.10.122', '10.10.10.123', '10.10.10.131', '10.10.10.132', 
                       '10.10.10.151', '10.10.10.152', '10.10.10.201'],
                'Status': ['OK', 'OK', 'OK', 'OK', 'OK', 'OK', 'OK', 'OK'],
                'Info': ['Inverter số 1', 'Inverter số 2', 'Inverter số 3', 'Inverter số 1', 'Inverter số 2', 
                        'Inverter số 1', 'Inverter số 2', 'Inverter số 1']
            }
            df_stations = pd.DataFrame(stations_data)
            
            scenarios_data = {
                'Station': ['B3R1', 'B4R2', 'B5R2', 'B8', 'B3R1', 'B4R2', 'B5R2', 'B8'],
                'Action': ['OFF', 'OFF', 'OFF', 'OFF', 'ON', 'ON', 'ON', 'ON'],
                'Count': [9, 10, 10, 4, 9, 10, 10, 4]
            }
            df_scenarios = pd.DataFrame(scenarios_data)
            
            with pd.ExcelWriter(self.excel_file_path, engine='openpyxl') as writer:
                df_stations.to_excel(writer, sheet_name='Stations', index=False)
                df_scenarios.to_excel(writer, sheet_name='Control_Scenarios', index=False)
            
            self.logger.log_info(f"✅ Đã tạo file template: {self.excel_file_path}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Lỗi tạo template Excel: {e}")
            return False


class InteractiveMenu:
    """Lớp quản lý menu tương tác"""
    
    def __init__(self):
        excel_system_urls, excel_control_scenarios = self.load_config_from_excel()
        
        if excel_system_urls and excel_control_scenarios:
            self.SYSTEM_URLS = excel_system_urls
            self.CONTROL_SCENARIOS = excel_control_scenarios
            print("✅ Đang sử dụng cấu hình từ Excel")
        else:
            self.SYSTEM_URLS = SYSTEM_URLS
            self.CONTROL_SCENARIOS = {
                "1": {"name": "Tắt một số inverter", "requests": CONTROL_REQUESTS_OFF},
                "2": {"name": "Bật một số inverter", "requests": CONTROL_REQUESTS_ON},
                "3": {"name": "Bật tất cả inverter", "requests": ON_ALL},
            }
            print("⚠️ Đang sử dụng cấu hình mặc định")
        
        try:
            self.processor = TaskProcessor(CONFIG, self.SYSTEM_URLS)
            
            self.SCENARIOS = {
                **self.CONTROL_SCENARIOS,
                "4": {"name": "Bật/tắt 1 inverter", "requests": None},
                "5": {"name": "Tùy chỉnh", "requests": None},
                "6": {"name": "Xem trạng thái hệ thống", "requests": None},
                "7": {"name": "Quản lý cấu hình Excel", "requests": None},
                "0": {"name": "Thoát chương trình", "requests": None}
            }
            
            print(f"✅ Đã khởi tạo menu với {len(self.SCENARIOS)} scenarios")
            
        except Exception as e:
            print(f"❌ Lỗi khởi tạo InteractiveMenu: {e}")
            import traceback
            traceback.print_exc()
            exit(1)
    
    def load_config_from_excel(self):
        excel_reader = ExcelConfigReader(EXCEL_CONFIG_FILE)
        
        if not excel_reader.check_excel_file():
            print(f"❌ File Excel {EXCEL_CONFIG_FILE} không tồn tại hoặc không hợp lệ")
            print("🔄 Đang tạo file template...")
            if excel_reader.create_excel_template():
                print(f"✅ Đã tạo file template: {EXCEL_CONFIG_FILE}")
                print("📝 Vui lòng điền thông tin vào file Excel và chạy lại chương trình")
            return None, None
        
        excel_system_urls = excel_reader.read_stations_config()
        if not excel_system_urls:
            print("❌ Không thể đọc cấu hình stations từ Excel, sử dụng config gốc")
            excel_system_urls = SYSTEM_URLS
        
        excel_control_scenarios = excel_reader.get_available_scenarios()
        if not excel_control_scenarios:
            print("⚠️ Không có scenarios nào trong file Excel, sử dụng scenarios mặc định")
            excel_control_scenarios = {
                "1": {"name": "Tắt một số inverter", "requests": CONTROL_REQUESTS_OFF},
                "2": {"name": "Bật một số inverter", "requests": CONTROL_REQUESTS_ON},
                "3": {"name": "Bật tất cả inverter", "requests": ON_ALL},
            }
        
        print(f"✅ Đã tải cấu hình từ Excel: {len(excel_system_urls)} zones, {len(excel_control_scenarios)} scenarios")
        return excel_system_urls, excel_control_scenarios
    
    def display_header(self):
        print("\n" + "=" * 60)
        print(f"🚀 CHƯƠNG TRÌNH ĐIỀU KHIỂN INVERTER - PHIÊN BẢN {VERSION}")
        print("=" * 60)
        print("🎯 All-in-One Version - Single File Execution")
        print("⚡ Optimized Driver Pool - 1 task = 1 driver")
        print("🔌 Bật/Tắt 1 INV - Điều khiển inverter riêng lẻ")
        print("🔌 Bật tất cả INV - Hỗ trợ toàn bộ hệ thống")
        print("📊 Interactive Menu với tính năng Quay lại")
        print("🔄 Xử lý thông minh với retry mechanism")
        print("=" * 60)
    
    def display_menu(self):
        print("\n📋 MENU CHÍNH:")
        
        for key, scenario in self.CONTROL_SCENARIOS.items():
            print(f"{key}. {scenario['name']}")
        
        print("4. Bật/tắt 1 inverter")
        print("5. Tùy chỉnh")
        print("6. Xem trạng thái hệ thống")
        print("7. Quản lý cấu hình Excel")
        print("0. Thoát chương trình")
        print("-" * 40)
    
    def get_user_choice(self):
        max_choice = max([int(k) for k in self.SCENARIOS.keys() if k != '0'])
        
        while True:
            choice = input(f"\n👉 Chọn chức năng (0-{max_choice}): ").strip()
            if choice in self.SCENARIOS:
                return choice
            else:
                print(f"❌ Lựa chọn không hợp lệ! Vui lòng chọn từ 0-{max_choice}")
    
    def single_inverter_menu(self):
        print("\n🔌 BẬT/TẮT 1 INVERTER")
        print("=" * 50)
        print("📝 Định dạng: TênStation-TênInverter HànhĐộng")
        print("💡 Ví dụ: B3R1-INV-01 ON")
        print("💡 Ví dụ: B4R2-INV-05 OFF")
        print("📋 Lệnh đặc biệt:")
        print("   'list' - Xem danh sách inverters")
        print("   'back' - Quay lại menu chính")
        print("-" * 50)
        
        while True:
            line = input("Nhập lệnh: ").strip()
            
            if line.lower() == 'back':
                return None
            
            elif line.lower() == 'list':
                self.display_all_inverters_detailed()
                continue
            
            else:
                try:
                    parts = line.split()
                    if len(parts) == 2:
                        full_inv_name = parts[0]
                        action = parts[1].upper()
                        
                        if action not in ['ON', 'OFF']:
                            print("❌ Hành động phải là ON hoặc OFF!")
                            continue
                        
                        if '-' not in full_inv_name:
                            print("❌ Định dạng không hợp lệ! Ví dụ: B3R1-INV-01")
                            continue
                        
                        possible_stations = []
                        for zone_name, stations in self.SYSTEM_URLS.items():
                            for station_name in stations.keys():
                                if full_inv_name.startswith(station_name + '-'):
                                    possible_stations.append(station_name)
                        
                        if not possible_stations:
                            print(f"❌ Không tìm thấy station phù hợp với '{full_inv_name}'")
                            self.display_all_inverters_detailed()
                            continue
                        
                        station_name = max(possible_stations, key=len)
                        inverter_name = full_inv_name[len(station_name)+1:]
                        
                        inverter_found = False
                        target_url = None
                        
                        for zone_name, stations in self.SYSTEM_URLS.items():
                            if station_name in stations:
                                if inverter_name in stations[station_name]:
                                    inverter_found = True
                                    target_url = stations[station_name][inverter_name]["url"]
                                    inv_info = stations[station_name][inverter_name]["info"]
                                    break
                        
                        if not inverter_found:
                            print(f"❌ Không tìm thấy inverter '{inverter_name}' trong station '{station_name}'")
                            self.display_station_inverters(station_name)
                            continue
                        
                        print(f"\n🔍 Đã tìm thấy inverter:")
                        print(f"   🏗️  Station: {station_name}")
                        print(f"   ⚡ Inverter: {inverter_name}")
                        print(f"   🌐 URL: {target_url}")
                        print(f"   📝 Info: {inv_info}")
                        print(f"   🎯 Hành động: {action}")
                        
                        confirm = input(f"\n✅ Xác nhận {action} inverter {full_inv_name}? (y/n): ").strip().lower()
                        if confirm != 'y':
                            print("⏹️ Đã hủy thực hiện.")
                            continue
                        
                        single_request = {
                            station_name: {
                                "action": action,
                                "count": 1
                            }
                        }
                        
                        return single_request
                        
                    else:
                        print("❌ Định dạng không hợp lệ! Ví dụ: B3R1-INV-01 ON")
                        
                except Exception as e:
                    print(f"❌ Lỗi: {e}")
    
    def display_all_inverters_detailed(self):
        print("\n📋 DANH SÁCH TẤT CẢ INVERTERS:")
        print("=" * 70)
        
        for zone_name, stations in self.SYSTEM_URLS.items():
            print(f"\n📍 {zone_name}:")
            for station_name, inverters in stations.items():
                print(f"   🏗️  {station_name}:")
                for inv_name, inv_info in inverters.items():
                    full_name = f"{station_name}-{inv_name}"
                    status = inv_info.get("status", "OK")
                    url = inv_info["url"]
                    info = inv_info.get("info", "")
                    print(f"      ⚡ {full_name:20} | {status:6} | {url:15} | {info}")
        
        print("=" * 70)
        print("💡 Sử dụng: [Station-Inverter] [ON/OFF]")
        print("💡 Ví dụ: B3R1-INV-01 ON")
        print("=" * 70)
    
    def display_station_inverters(self, station_name):
        print(f"\n📋 INVERTERS TRONG STATION {station_name}:")
        print("-" * 50)
        
        station_found = False
        for zone_name, stations in self.SYSTEM_URLS.items():
            if station_name in stations:
                station_found = True
                inverters = stations[station_name]
                for inv_name, inv_info in inverters.items():
                    full_name = f"{station_name}-{inv_name}"
                    status = inv_info.get("status", "OK")
                    url = inv_info["url"]
                    print(f"   ⚡ {full_name:20} | {status:6} | {url}")
                break
        
        if not station_found:
            print(f"❌ Không tìm thấy station '{station_name}'")
        
        print("-" * 50)
    
    def custom_scenario_menu(self):
        custom_requests = {}
        
        while True:
            print("\n🎛️ CHẾ ĐỘ TÙY CHỈNH")
            print("=" * 40)
            print("📝 Định dạng: TênStation SốLượng HànhĐộng")
            print("💡 Ví dụ: B3R1 5 OFF")
            print("📋 Lệnh đặc biệt:")
            print("   'list' - Xem danh sách stations")
            print("   'done' - Hoàn thành nhập")
            print("   'back' - Quay lại menu chính")
            print("   'clear' - Xóa tất cả yêu cầu")
            print("   'show' - Xem yêu cầu hiện tại")
            print("   'all_on' - Bật tất cả inverter")
            print("-" * 40)
            
            if custom_requests:
                print("📋 Yêu cầu hiện tại:")
                for station, req in custom_requests.items():
                    print(f"   {station}: {req['count']} INV - {req['action']}")
                print("-" * 40)
            
            line = input("Nhập lệnh: ").strip()
            
            if line.lower() == 'back':
                confirm = input("❓ Quay lại menu chính? (y/n): ").strip().lower()
                if confirm == 'y':
                    return None
                else:
                    continue
            
            elif line.lower() == 'done':
                if not custom_requests:
                    print("⚠️ Chưa có yêu cầu nào! Vui lòng thêm yêu cầu trước.")
                    continue
                print("\n📋 Tổng hợp yêu cầu:")
                total_inverters = 0
                for station, req in custom_requests.items():
                    print(f"   ✅ {station}: {req['count']} INV - {req['action']}")
                    total_inverters += req['count']
                print(f"📊 Tổng số inverter: {total_inverters}")
                
                confirm = input("\n✅ Xác nhận thực hiện? (y/n): ").strip().lower()
                if confirm == 'y':
                    return custom_requests
                else:
                    continue
            
            elif line.lower() == 'clear':
                if custom_requests:
                    confirm = input("❓ Xóa tất cả yêu cầu? (y/n): ").strip().lower()
                    if confirm == 'y':
                        custom_requests = {}
                        print("✅ Đã xóa tất cả yêu cầu")
                else:
                    print("ℹ️ Không có yêu cầu nào để xóa")
            
            elif line.lower() == 'show':
                if custom_requests:
                    print("\n📋 Yêu cầu hiện tại:")
                    total_inverters = 0
                    for station, req in custom_requests.items():
                        print(f"   {station}: {req['count']} INV - {req['action']}")
                        total_inverters += req['count']
                    print(f"📊 Tổng số inverter: {total_inverters}")
                else:
                    print("ℹ️ Chưa có yêu cầu nào")
            
            elif line.lower() == 'list':
                self.display_available_stations()
            
            elif line.lower() == 'all_on':
                confirm = input("🔌 BẬT TẤT CẢ INVERTER? (y/n): ").strip().lower()
                if confirm == 'y':
                    all_on_requests = {}
                    for zone_name, stations in self.SYSTEM_URLS.items():
                        for station_name, inverters in stations.items():
                            all_on_requests[station_name] = {
                                "action": "ON",
                                "count": len(inverters)
                            }
                    print("✅ Đã tạo yêu cầu Bật tất cả inverter")
                    return all_on_requests
            
            else:
                try:
                    parts = line.split()
                    if len(parts) == 3:
                        station, count, action = parts
                        action = action.upper()
                        
                        if action not in ['ON', 'OFF']:
                            print("❌ Hành động phải là ON hoặc OFF!")
                            continue
                        
                        try:
                            count = int(count)
                            if count <= 0:
                                print("❌ Số lượng phải lớn hơn 0!")
                                continue
                        except ValueError:
                            print("❌ Số lượng phải là số nguyên!")
                            continue
                        
                        station_exists = False
                        for zone_name, stations in self.SYSTEM_URLS.items():
                            if station in stations:
                                station_exists = True
                                available_inverters = len(stations[station])
                                if count > available_inverters:
                                    print(f"⚠️ Cảnh báo: {station} chỉ có {available_inverters} inverter, bạn yêu cầu {count}")
                                break
                        
                        if not station_exists:
                            print(f"❌ Station '{station}' không tồn tại!")
                            self.display_available_stations()
                            continue
                        
                        custom_requests[station] = {
                            "action": action,
                            "count": count
                        }
                        print(f"✅ Đã thêm: {station} - {count} INV - {action}")
                        
                    else:
                        print("❌ Định dạng không hợp lệ! Ví dụ: B3R1 5 OFF")
                        
                except Exception as e:
                    print(f"❌ Lỗi: {e}")
    
    def display_available_stations(self):
        print("\n🏭 DANH SÁCH STATIONS:")
        print("-" * 50)
        total_inverters = 0
        for zone_name, stations in self.SYSTEM_URLS.items():
            print(f"\n📍 {zone_name}:")
            for station_name, inverters in stations.items():
                inv_count = len(inverters)
                total_inverters += inv_count
                print(f"   🏗️  {station_name}: {inv_count} inverter(s)")
        print("-" * 50)
        print(f"📊 TỔNG SỐ INVERTER TRONG HỆ THỐNG: {total_inverters}")
        print("-" * 50)
    
    def system_status_menu(self):
        while True:
            print("\n📊 TRẠNG THÁI HỆ THỐNG")
            print("=" * 40)
            print("1. Xem tổng quan hệ thống")
            print("2. Xem chi tiết từng zone")
            print("3. Xem thống kê inverter")
            print("4. Xem thông tin Bật tất cả")
            print("5. Tìm kiếm inverter")
            print("0. Quay lại menu chính")
            print("-" * 40)
            
            choice = input("Chọn chức năng: ").strip()
            
            if choice == '0':
                return
            
            elif choice == '1':
                self.display_system_overview()
            
            elif choice == '2':
                self.display_zone_details()
            
            elif choice == '3':
                self.display_inverter_stats()
            
            elif choice == '4':
                self.display_all_inverters_info()
            
            elif choice == '5':
                self.search_inverter_menu()
            
            else:
                print("❌ Lựa chọn không hợp lệ!")
    
    def search_inverter_menu(self):
        print("\n🔍 TÌM KIẾM INVERTER")
        print("=" * 40)
        print("Nhập tên inverter (có thể nhập một phần):")
        print("💡 Ví dụ: INV-01, B3R1, 121, ...")
        print("   'back' - Quay lại")
        print("-" * 40)
        
        while True:
            search_term = input("Từ khóa tìm kiếm: ").strip()
            
            if search_term.lower() == 'back':
                return
            
            if not search_term:
                continue
            
            print(f"\n🔍 Kết quả tìm kiếm cho '{search_term}':")
            print("-" * 60)
            
            found_count = 0
            for zone_name, stations in self.SYSTEM_URLS.items():
                for station_name, inverters in stations.items():
                    for inv_name, inv_info in inverters.items():
                        full_name = f"{station_name}-{inv_name}"
                        url = inv_info["url"]
                        info = inv_info.get("info", "")
                        status = inv_info.get("status", "OK")
                        
                        if (search_term.upper() in full_name.upper() or 
                            search_term in url or 
                            search_term.upper() in info.upper()):
                            
                            found_count += 1
                            print(f"   ⚡ {full_name:20} | {status:6} | {url:15} | {info}")
            
            if found_count == 0:
                print("   ❌ Không tìm thấy inverter nào phù hợp")
            else:
                print(f"   📊 Tìm thấy {found_count} inverter(s)")
            
            print("-" * 60)
    
    def display_all_inverters_info(self):
        print("\n🔌 THÔNG TIN BẬT TẤT CẢ INVERTER")
        print("=" * 60)
        
        total_stations = 0
        total_inverters = 0
        
        print("📋 DANH SÁCH TẤT CẢ STATIONS VÀ INVERTERS:")
        print("-" * 60)
        
        for zone_name, stations in self.SYSTEM_URLS.items():
            print(f"\n📍 {zone_name}:")
            for station_name, inverters in stations.items():
                inv_count = len(inverters)
                total_stations += 1
                total_inverters += inv_count
                
                status_count = {}
                for inv_name, inv_info in inverters.items():
                    status = inv_info.get("status", "OK")
                    status_count[status] = status_count.get(status, 0) + 1
                
                status_text = ", ".join([f"{count} {status}" for status, count in status_count.items()])
                print(f"   🏗️  {station_name}: {inv_count} inverter(s) - [{status_text}]")
        
        print("\n" + "=" * 60)
        print(f"📊 TỔNG SỐ STATIONS: {total_stations}")
        print(f"🔢 TỔNG SỐ INVERTERS: {total_inverters}")
        print("💡 Sử dụng chức năng 'Bật tất cả inverter' để bật toàn bộ hệ thống")
        print("💡 Sử dụng chức năng 'Bật/tắt 1 inverter' để điều khiển riêng lẻ")
        print("=" * 60)
        
        input("\n👆 Nhấn Enter để tiếp tục...")
    
    def display_system_overview(self):
        print("\n📈 TỔNG QUAN HỆ THỐNG")
        print("=" * 50)
        
        total_stations = 0
        total_inverters = 0
        
        for zone_name, stations in self.SYSTEM_URLS.items():
            zone_stations = len(stations)
            zone_inverters = sum(len(inverters) for inverters in stations.values())
            
            total_stations += zone_stations
            total_inverters += zone_inverters
            
            print(f"\n📍 {zone_name}:")
            print(f"   🏗️  Số stations: {zone_stations}")
            print(f"   ⚡ Số inverters: {zone_inverters}")
        
        print("\n" + "=" * 50)
        print(f"📊 TỔNG CỘNG:")
        print(f"   🏗️  Tổng stations: {total_stations}")
        print(f"   ⚡ Tổng inverters: {total_inverters}")
        print("=" * 50)
        
        input("\n👆 Nhấn Enter để tiếp tục...")
    
    def display_zone_details(self):
        print("\n🏭 CHI TIẾT TỪNG ZONE")
        print("=" * 60)
        
        for zone_name, stations in self.SYSTEM_URLS.items():
            print(f"\n📍 {zone_name}:")
            print("-" * 40)
            
            for station_name, inverters in stations.items():
                inv_count = len(inverters)
                status_count = {}
                
                for inv_name, inv_info in inverters.items():
                    status = inv_info.get("status", "OK")
                    status_count[status] = status_count.get(status, 0) + 1
                
                status_text = ", ".join([f"{count} {status}" for status, count in status_count.items()])
                print(f"   🏗️  {station_name}: {inv_count} inverter(s) - [{status_text}]")
        
        print("=" * 60)
        input("\n👆 Nhấn Enter để tiếp tục...")
    
    def display_inverter_stats(self):
        print("\n📊 THỐNG KÊ INVERTER")
        print("=" * 50)
        
        status_stats = {}
        total_inverters = 0
        
        for zone_name, stations in self.SYSTEM_URLS.items():
            for station_name, inverters in stations.items():
                for inv_name, inv_info in inverters.items():
                    total_inverters += 1
                    status = inv_info.get("status", "OK")
                    status_stats[status] = status_stats.get(status, 0) + 1
        
        print(f"🔢 Tổng số inverter: {total_inverters}")
        print("\n📈 Phân bố trạng thái:")
        for status, count in status_stats.items():
            percentage = (count / total_inverters) * 100
            print(f"   {status}: {count} inverter ({percentage:.1f}%)")
        
        print("=" * 50)
        input("\n👆 Nhấn Enter để tiếp tục...")
    
    def excel_config_menu(self):
        excel_reader = ExcelConfigReader()
        
        while True:
            print("\n📊 QUẢN LÝ CẤU HÌNH EXCEL")
            print("=" * 40)
            print("1. Kiểm tra file Excel")
            print("2. Xem thông tin cấu hình")
            print("3. Tạo template Excel (nếu chưa có)")
            print("4. Validate scenarios")
            print("0. Quay lại menu chính")
            print("-" * 40)
            
            choice = input("Chọn chức năng: ").strip()
            
            if choice == '0':
                return
            
            elif choice == '1':
                if excel_reader.check_excel_file():
                    print("✅ File Excel hợp lệ và đầy đủ")
                else:
                    print("❌ File Excel có vấn đề")
            
            elif choice == '2':
                self.display_excel_config_info()
            
            elif choice == '3':
                if excel_reader.create_excel_template():
                    print("✅ Đã tạo template Excel thành công")
                else:
                    print("❌ Lỗi khi tạo template")
            
            elif choice == '4':
                self.validate_scenarios()
            
            else:
                print("❌ Lựa chọn không hợp lệ!")
            
            input("\n👆 Nhấn Enter để tiếp tục...")
    
    def display_excel_config_info(self):
        print("\n📈 THÔNG TIN CẤU HÌNH TỪ EXCEL")
        print("=" * 50)
        
        total_zones = len(self.SYSTEM_URLS)
        total_stations = sum(len(stations) for stations in self.SYSTEM_URLS.values())
        total_inverters = sum(len(inverters) for stations in self.SYSTEM_URLS.values() for inverters in stations.values())
        
        print(f"🏗️  Số zones: {total_zones}")
        print(f"🏭 Số stations: {total_stations}")
        print(f"⚡ Số inverters: {total_inverters}")
        
        print(f"\n📋 Số scenarios: {len(self.CONTROL_SCENARIOS)}")
        for key, scenario in self.CONTROL_SCENARIOS.items():
            scenario_name = scenario['name']
            station_count = len(scenario['requests'])
            total_inv_in_scenario = sum(req['count'] for req in scenario['requests'].values())
            print(f"   {key}. {scenario_name}: {station_count} stations, {total_inv_in_scenario} inverters")
        
        print("=" * 50)
    
    def validate_scenarios(self):
        excel_reader = ExcelConfigReader()
        
        print("\n🔍 VALIDATE SCENARIOS")
        print("=" * 50)
        
        all_valid = True
        
        for key, scenario in self.CONTROL_SCENARIOS.items():
            print(f"\n📋 Scenario: {scenario['name']}")
            errors, warnings = excel_reader.validate_scenario_with_system(
                scenario['requests'], self.SYSTEM_URLS
            )
            
            if errors:
                print("❌ Lỗi:")
                for error in errors:
                    print(f"   - {error}")
                all_valid = False
            
            if warnings:
                print("⚠️ Cảnh báo:")
                for warning in warnings:
                    print(f"   - {warning}")
            
            if not errors and not warnings:
                print("✅ Scenario hợp lệ")
        
        if all_valid:
            print("\n🎉 Tất cả scenarios đều hợp lệ!")
        else:
            print("\n❌ Có scenarios không hợp lệ, vui lòng kiểm tra lại file Excel")
        
        print("=" * 50)
    
    def execute_scenario(self, choice):
        try:
            scenario = self.SCENARIOS[choice]
            
            if choice == "0":
                print("\n👋 Đang thoát chương trình...")
                return False
            
            elif choice == "4":
                requests = self.single_inverter_menu()
                if requests is None:
                    return True
            
            elif choice == "5":
                requests = self.custom_scenario_menu()
                if requests is None:
                    return True
            
            elif choice == "6":
                self.system_status_menu()
                return True
            
            elif choice == "7":
                self.excel_config_menu()
                return True
            
            else:
                requests = scenario["requests"]
                print(f"\n🎯 Đang xử lý: {scenario['name']}")
                print(f"📊 Số lượng stations: {len(requests)}")
                
                total_inverters = sum(req["count"] for req in requests.values())
                print(f"🔢 Tổng số inverter cần xử lý: {total_inverters}")
                
                print("\n📋 Chi tiết:")
                for station, req in requests.items():
                    print(f"   🏗️  {station}: {req['count']} INV - {req['action']}")
                
                if "tất cả" in scenario['name'].lower():
                    print(f"\n⚠️  CẢNH BÁO: Bạn sắp {scenario['name'].upper()}!")
                    print(f"⚠️  Sẽ ảnh hưởng đến {total_inverters} inverter trong hệ thống!")
                
                confirm = input("\n✅ Xác nhận thực hiện? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("⏹️ Đã hủy thực hiện.")
                    return True
            
            if choice not in ["6", "7"] and requests:
                print(f"\n🚀 Bắt đầu xử lý {len(requests)} yêu cầu...")
                if choice == "4":
                    print("🔌 THỰC HIỆN: BẬT/TẮT 1 INVERTER")
                elif "tất cả" in scenario.get('name', '').lower():
                    print(f"🔌 THỰC HIỆN: {scenario['name'].upper()} - {total_inverters} INVERTER")
                self.processor.run_parallel_optimized(requests)
            
            input("\n👆 Nhấn Enter để tiếp tục...")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi trong execute_scenario: {e}")
            import traceback
            traceback.print_exc()
            input("\n👆 Nhấn Enter để tiếp tục...")
            return True
    
    def run(self):
        print("🔄 Khởi động chương trình...")
        
        while True:
            try:
                self.display_header()
                self.display_menu()
                choice = self.get_user_choice()
                
                should_continue = self.execute_scenario(choice)
                if not should_continue:
                    break
                    
            except KeyboardInterrupt:
                print("\n\n⏹️ Chương trình đã được dừng bởi người dùng")
                break
            except Exception as e:
                print(f"❌ Lỗi trong menu chính: {e}")
                import traceback
                traceback.print_exc()
                input("\n👆 Nhấn Enter để tiếp tục...")


def main():
    """Hàm chính - Phiên bản All-in-One"""
    try:
        menu = InteractiveMenu()
        menu.run()
    except KeyboardInterrupt:
        print("\n\n⏹️ Chương trình đã được dừng bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Cảm ơn bạn đã sử dụng chương trình!")


if __name__ == "__main__":
    main()