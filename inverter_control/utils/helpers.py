"""
Các hàm utility hỗ trợ
"""

import time
import psutil

def get_system_resources():
    """Lấy thông tin tài nguyên hệ thống"""
    memory = psutil.virtual_memory()
    cpu_percent = psutil.cpu_percent(interval=1)
    
    return {
        "memory_used": memory.used / (1024**3),  # GB
        "memory_total": memory.total / (1024**3),  # GB
        "memory_percent": memory.percent,
        "cpu_percent": cpu_percent
    }

def format_duration(seconds):
    """Định dạng thời lượng"""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def validate_ip_address(ip):
    """Validate địa chỉ IP"""
    parts = ip.split('.')
    if len(parts) != 4:
        return False
    for part in parts:
        if not part.isdigit():
            return False
        num = int(part)
        if num < 0 or num > 255:
            return False
    return True