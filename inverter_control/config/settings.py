# config/settings.py
"""
Cấu hình hệ thống - Phiên bản 0.5.3 - Auto ChromeDriver
"""

import os
import sys

def get_chromedriver_path():
    """Tự động xác định đường dẫn ChromeDriver"""
    
    # Thử các đường dẫn phổ biến
    possible_paths = []
    
    # Đường dẫn trong project
    if sys.platform.startswith("win32"):
        possible_paths.extend([
            os.path.join("drivers", "chromedriver.exe"),
            "chromedriver.exe",
            r"C:\Windows\System32\chromedriver.exe"
        ])
    else:
        possible_paths.extend([
            os.path.join("drivers", "chromedriver"),
            "/usr/local/bin/chromedriver",
            "/usr/bin/chromedriver",
            "/snap/bin/chromedriver",
            "chromedriver"
        ])
    
    # Kiểm tra từng đường dẫn
    for path in possible_paths:
        if os.path.exists(path):
            print(f"✅ Tìm thấy ChromeDriver tại: {path}")
            return path
    
    # Nếu không tìm thấy, thử cài đặt tự động
    print("❌ Không tìm thấy ChromeDriver, đang thử cài đặt tự động...")
    try:
        from webdriver_manager.chrome import ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        print(f"✅ Đã cài đặt ChromeDriver tại: {driver_path}")
        return driver_path
    except Exception as e:
        print(f"⚠️ Không thể cài đặt tự động ChromeDriver: {e}")
        # Fallback path
        return "/usr/bin/chromedriver" if not sys.platform.startswith("win32") else "chromedriver.exe"

# Cấu hình tối ưu cho phiên bản optimized pool
CONFIG = {
    "version": "0.5.3",
    "excel_file": "inverter_config.xlsx",
    "credentials": {
        "username": "installer",
        "password": "Mo_g010rP!"
    },
    "driver": {
        "path": get_chromedriver_path(),  # Sử dụng hàm tự động
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
        "format": "%(asctime)s - %(levelname)s - [%(threadName)s] - v0.5.3 - %(message)s",
        "file": "inverter_control_v0.5.3.log"
    }
}

# Export các biến để tương thích với code cũ
VERSION = CONFIG["version"]
EXCEL_CONFIG_FILE = CONFIG["excel_file"]

# Cấu hình mặc định từ system_config
from .system_config import SYSTEM_URLS as ORIGINAL_SYSTEM_URLS
from .system_config import CONTROL_REQUESTS_OFF, CONTROL_REQUESTS_ON, ON_ALL

# Biến để lưu config từ Excel
EXCEL_SYSTEM_URLS = None
EXCEL_CONTROL_SCENARIOS = None
SYSTEM_URLS = ORIGINAL_SYSTEM_URLS
CONTROL_SCENARIOS = None

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
    
    print(f"✅ Đã tải cấu hình từ Excel: {len(EXCEL_SYSTEM_URLS)} zones, {len(EXCEL_CONTROL_SCENARIOS)} scenarios (v{VERSION})")
    return EXCEL_SYSTEM_URLS, EXCEL_CONTROL_SCENARIOS