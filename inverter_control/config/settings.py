# config/settings.py
"""
Cấu hình hệ thống - Phiên bản 0.5.1
"""

import os

# --- CẤU HÌNH PHIÊN BẢN 0.5.1 - EXCEL CONFIG ---
VERSION = "0.5.1"
EXCEL_CONFIG_FILE = "inverter_config.xlsx"

# Cấu hình mặc định từ system_config (KHÔNG thay đổi)
from .system_config import SYSTEM_URLS as ORIGINAL_SYSTEM_URLS
from .system_config import CONTROL_REQUESTS_OFF, CONTROL_REQUESTS_ON, ON_ALL

# Biến để lưu config từ Excel (sẽ được khởi tạo sau)
EXCEL_SYSTEM_URLS = None
EXCEL_CONTROL_SCENARIOS = None

# Cấu hình mặc định
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

def load_config_from_excel():
    """Load cấu hình từ file Excel và trả về config"""
    global EXCEL_SYSTEM_URLS, EXCEL_CONTROL_SCENARIOS
    
    # Import tại đây để tránh circular import
    from .excel_reader import ExcelConfigReader
    
    excel_reader = ExcelConfigReader(EXCEL_CONFIG_FILE)
    
    # Kiểm tra file Excel
    if not excel_reader.check_excel_file():
        print(f"❌ File Excel {EXCEL_CONFIG_FILE} không tồn tại hoặc không hợp lệ")
        print("🔄 Đang tạo file template...")
        if excel_reader.create_excel_template():
            print(f"✅ Đã tạo file template: {EXCEL_CONFIG_FILE}")
            print("📝 Vui lòng điền thông tin vào file Excel và chạy lại chương trình")
        return None, None
    
    # Đọc cấu hình stations từ Excel
    EXCEL_SYSTEM_URLS = excel_reader.read_stations_config()
    if not EXCEL_SYSTEM_URLS:
        print("❌ Không thể đọc cấu hình stations từ Excel, sử dụng config gốc")
        EXCEL_SYSTEM_URLS = ORIGINAL_SYSTEM_URLS
    
    # Đọc scenarios từ Excel
    EXCEL_CONTROL_SCENARIOS = excel_reader.get_available_scenarios()
    if not EXCEL_CONTROL_SCENARIOS:
        print("⚠️ Không có scenarios nào trong file Excel, sử dụng scenarios mặc định")
        # Sử dụng scenarios mặc định
        EXCEL_CONTROL_SCENARIOS = {
            "1": {"name": "Tắt một số inverter", "requests": CONTROL_REQUESTS_OFF},
            "2": {"name": "Bật một số inverter", "requests": CONTROL_REQUESTS_ON},
            "3": {"name": "Bật tất cả inverter", "requests": ON_ALL}
        }
    
    print(f"✅ Đã tải cấu hình từ Excel: {len(EXCEL_SYSTEM_URLS)} zones, {len(EXCEL_CONTROL_SCENARIOS)} scenarios")
    return EXCEL_SYSTEM_URLS, EXCEL_CONTROL_SCENARIOS

# Export các biến để tương thích với code cũ
SYSTEM_URLS = ORIGINAL_SYSTEM_URLS
CONTROL_SCENARIOS = None