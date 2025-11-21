# config/settings.py
import os
import sys
import platform

def detect_browser_config():
    """Tự động phát hiện cấu hình trình duyệt"""
    
    # Ưu tiên file cấu hình auto-generated
    if os.path.exists("browser_config.py"):
        try:
            from browser_config import BROWSER, BROWSER_PATH, DRIVER_PATH
            print(f"✅ Sử dụng cấu hình từ browser_config.py: {BROWSER.upper()}")
            return DRIVER_PATH, BROWSER_PATH, BROWSER
        except:
            pass
    
    # Fallback: tự động phát hiện
    system = platform.system().lower()
    
    # Kiểm tra Edge trên Windows
    if system == "windows":
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        for path in edge_paths:
            if os.path.exists(path):
                print("✅ Phát hiện Microsoft Edge")
                return "msedgedriver.exe", path, "edge"
    
    # Kiểm tra Chrome
    chrome_paths = []
    if system == "windows":
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
        ]
    else:
        chrome_paths = [
            "/usr/bin/google-chrome",
            "/usr/bin/google-chrome-stable",
            "/usr/bin/chromium-browser"
        ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            print("✅ Phát hiện Google Chrome/Chromium")
            return "chromedriver", path, "chrome"
    
    # Fallback cuối cùng
    print("⚠️ Không phát hiện trình duyệt, sử dụng mặc định")
    if system == "windows":
        return "msedgedriver.exe", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "edge"
    else:
        return "chromedriver", "/usr/bin/chromium-browser", "chrome"

# Lấy cấu hình trình duyệt
DRIVER_PATH, BROWSER_PATH, BROWSER_TYPE = detect_browser_config()

CONFIG = {
    "version": "0.5.3",
    "excel_file": "inverter_config.xlsx",
    "credentials": {
        "username": "installer",
        "password": "Mo_g010rP!"
    },
    "driver": {
        "path": DRIVER_PATH,
        "browser_path": BROWSER_PATH,
        "browser_type": BROWSER_TYPE,
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