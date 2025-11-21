from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime
import sys
import os

# Import cấu hình hệ thống
from system_config import SYSTEM_URLS, CONTROL_REQUESTS_OFF, CONTROL_REQUESTS_ON, ON_ALL

# --- CẤU HÌNH NÂNG CAO PHIÊN BẢN 0.2 ---
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
        "action_timeout": 5
    },
    "performance": {
        "max_workers": 6,  # Giảm để ổn định hơn
        "retry_attempts": 2,
        "retry_delay": 2,
        "batch_size": 5
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s",
        "file": "inverter_control_v0.2.log"
    }
}

# SELECTORS - ĐƯỢC TỐI ƯU CHO WEBDRIVERWAIT
SELECTORS = {
    "login": {
        "dropdown_toggle": "#login-dropdown-list > a.dropdown-toggle",
        "username_field": "login-username",
        "password_field": "login-password", 
        "login_button": "login-buttons-password",
        "user_indicator": "installer"  # Text xuất hiện khi đã login
    },
    "grid_control": {
        "connect_link": "link-grid-disconnect",
        "status_indicator": ["Disconnect Grid", "Connect Grid"]
    },
    "monitoring": {
        "status_line": "#status-line-dsp",
        "power_active": ".js-active-power",
        "navbar": ".navbar"  # Element chung để chờ trang load
    }
}

class InverterControlLogger:
    """Lớp quản lý logging nâng cao - Phiên bản 0.2"""
    
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, CONFIG["logging"]["level"]),
            format=CONFIG["logging"]["format"],
            handlers=[
                logging.FileHandler(CONFIG["logging"]["file"], encoding='utf-8'),
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

class InverterDriver:
    """Lớp quản lý WebDriver với WebDriverWait - Phiên bản 0.2"""
    
    def __init__(self):
        self.driver = None
        self.logger = InverterControlLogger()
        self.wait = None
    
    def initialize_driver(self):
        """Khởi tạo WebDriver với cấu hình tối ưu"""
        try:
            service = Service(CONFIG["driver"]["path"])
            
            chrome_options = webdriver.ChromeOptions()
            if CONFIG["driver"]["headless"]:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)

            # Tối ưu hiệu suất - Phiên bản 0.2
            chrome_options.add_experimental_option(
                "prefs", {
                    "profile.managed_default_content_settings.images": 2,
                    "profile.managed_default_content_settings.stylesheets": 2,
                    "profile.managed_default_content_settings.fonts": 2,
                    "profile.managed_default_content_settings.media_stream": 2,
                    "profile.default_content_setting_values.notifications": 2,
                    "profile.default_content_setting_values.geolocation": 2,
                    "profile.default_content_setting_values.camera": 2,
                    "profile.default_content_setting_values.microphone": 2,
                }
            )
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(CONFIG["driver"]["page_load_timeout"])
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            # Khởi tạo WebDriverWait
            self.wait = WebDriverWait(self.driver, CONFIG["driver"]["element_timeout"])
            
            self.logger.log_info("Driver khởi tạo thành công với WebDriverWait")
            return self.driver
            
        except Exception as e:
            self.logger.log_error(f"Khởi tạo Driver thất bại: {e}")
            return None
    
    def wait_for_element(self, by, value, timeout=None):
        """Chờ element xuất hiện với timeout tùy chỉnh"""
        try:
            wait_timeout = timeout or CONFIG["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            self.logger.log_debug(f"Timeout chờ element: {by}={value}")
            return None
    
    def wait_for_element_clickable(self, by, value, timeout=None):
        """Chờ element có thể click được"""
        try:
            wait_timeout = timeout or CONFIG["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            self.logger.log_debug(f"Timeout chờ element clickable: {by}={value}")
            return None
    
    def wait_for_text_present(self, by, value, text, timeout=None):
        """Chờ text xuất hiện trong element"""
        try:
            wait_timeout = timeout or CONFIG["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.text_to_be_present_in_element((by, value), text))
        except TimeoutException:
            self.logger.log_debug(f"Timeout chờ text '{text}' trong element: {by}={value}")
            return False
    
    def wait_for_page_loaded(self, timeout=None):
        """Chờ trang web load hoàn tất"""
        try:
            wait_timeout = timeout or CONFIG["driver"]["page_load_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            self.logger.log_warning("Timeout chờ trang load hoàn tất")
            return False
    
    def safe_click(self, by, value, timeout=None):
        """Click an toàn với retry mechanism"""
        for attempt in range(2):  # Retry 1 lần
            try:
                element = self.wait_for_element_clickable(by, value, timeout)
                if element:
                    element.click()
                    return True
            except StaleElementReferenceException:
                self.logger.log_debug(f"Stale element, retry click: {by}={value}")
                continue
        return False
    
    def safe_send_keys(self, by, value, keys, timeout=None):
        """Nhập text an toàn"""
        element = self.wait_for_element(by, value, timeout)
        if element:
            element.clear()
            element.send_keys(keys)
            return True
        return False
    
    def quit(self):
        """Đóng driver an toàn"""
        if self.driver:
            self.driver.quit()
            self.logger.log_info("Driver đã đóng")

class InverterController:
    """Lớp chính điều khiển inverter - Phiên bản 0.2 với WebDriverWait"""
    
    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
        self.logger = InverterControlLogger()
    
    def login(self, url, username=None, password=None):
        """Đăng nhập sử dụng WebDriverWait - KHÔNG DÙNG time.sleep"""
        username = username or CONFIG["credentials"]["username"]
        password = password or CONFIG["credentials"]["password"]
        
        # Kiểm tra driver
        if not self.driver_manager.driver:
            self.logger.log_error("Driver chưa được khởi tạo", url)
            return False
        
        for attempt in range(CONFIG["performance"]["retry_attempts"] + 1):
            try:
                if not url.startswith(('http://', 'https://')):
                    url = f"http://{url}"
                
                self.logger.log_info(f"Truy cập URL: {url} (lần {attempt + 1})")
                self.driver_manager.driver.get(url)
                
                # Chờ trang load hoàn tất
                if not self.driver_manager.wait_for_page_loaded():
                    self.logger.log_warning("Trang load chậm, tiếp tục thử...", url)
                
                # KIỂM TRA XEM ĐÃ ĐĂNG NHẬP CHƯA - Sử dụng WebDriverWait
                if self.driver_manager.wait_for_text_present(By.TAG_NAME, "body", "installer", timeout=3):
                    self.logger.log_success("Đã đăng nhập sẵn", url)
                    return True
                
                # NẾU CHƯA ĐĂNG NHẬP, THỰC HIỆN ĐĂNG NHẬP
                self.logger.log_info("Thực hiện đăng nhập...", url)
                
                # Click dropdown đăng nhập (nếu có)
                dropdown = self.driver_manager.wait_for_element_clickable(
                    By.CSS_SELECTOR, SELECTORS["login"]["dropdown_toggle"], timeout=5
                )
                if dropdown:
                    dropdown.click()
                    # Chờ dropdown mở ra
                    self.driver_manager.wait_for_element(By.ID, SELECTORS["login"]["username_field"], timeout=3)
                
                # Nhập username với WebDriverWait
                if not self.driver_manager.safe_send_keys(By.ID, SELECTORS["login"]["username_field"], username, timeout=5):
                    self.logger.log_warning("Không tìm thấy field username, có thể đã đăng nhập", url)
                    return True
                
                # Nhập password với WebDriverWait
                if not self.driver_manager.safe_send_keys(By.ID, SELECTORS["login"]["password_field"], password, timeout=5):
                    self.logger.log_warning("Không tìm thấy field password", url)
                    return False
                
                # Click nút đăng nhập với WebDriverWait
                if not self.driver_manager.safe_click(By.ID, SELECTORS["login"]["login_button"], timeout=5):
                    self.logger.log_warning("Không tìm thấy nút đăng nhập", url)
                    return False
                
                # CHỜ ĐĂNG NHẬP THÀNH CÔNG - Sử dụng WebDriverWait
                # Cách 1: Chờ text "installer" xuất hiện
                if self.driver_manager.wait_for_text_present(By.TAG_NAME, "body", "installer", timeout=10):
                    self.logger.log_success("Đăng nhập thành công", url)
                    return True
                
                # Cách 2: Chờ navbar load hoàn tất như một dấu hiệu đăng nhập thành công
                if self.driver_manager.wait_for_element(By.CSS_SELECTOR, SELECTORS["monitoring"]["navbar"], timeout=5):
                    self.logger.log_success("Đăng nhập thành công (qua navbar)", url)
                    return True
                
                self.logger.log_warning("Không xác định được trạng thái đăng nhập", url)
                # Vẫn trả về True để thử điều khiển
                return True
                    
            except Exception as e:
                self.logger.log_warning(f"Lần đăng nhập {attempt + 1} thất bại: {e}", url)
                if attempt < CONFIG["performance"]["retry_attempts"]:
                    self.logger.log_info(f"Thử lại sau {CONFIG['performance']['retry_delay']}s...", url)
                    # Sử dụng WebDriverWait thay vì time.sleep
                    self.driver_manager.wait_for_element(By.TAG_NAME, "body", timeout=CONFIG["performance"]["retry_delay"])
                else:
                    self.logger.log_error("Đăng nhập thất bại sau tất cả các lần thử", url)
        
        return False
    
    def get_grid_status(self):
        """Lấy trạng thái hiện tại của grid với WebDriverWait"""
        try:
            link_element = self.driver_manager.wait_for_element(
                By.ID, SELECTORS["grid_control"]["connect_link"], timeout=5
            )
            if link_element:
                status = link_element.text.strip()
                self.logger.log_debug(f"Trạng thái grid: {status}")
                return status
            else:
                self.logger.log_warning("Không tìm thấy element grid control")
        except Exception as e:
            self.logger.log_error(f"Lỗi khi lấy trạng thái grid: {e}")
        return None
    
    def perform_grid_action(self, target_action):
        """Thực hiện hành động ON/OFF với grid sử dụng WebDriverWait"""
        current_status = self.get_grid_status()
        
        if not current_status:
            return False, "Không thể xác định trạng thái hiện tại"
        
        expected_status_after = "Disconnect Grid" if target_action == "ON" else "Connect Grid"
        
        # Kiểm tra nếu đã ở trạng thái mong muốn
        if (target_action == "ON" and current_status == "Disconnect Grid") or \
           (target_action == "OFF" and current_status == "Connect Grid"):
            return True, f"BỎ QUA: Đã ở trạng thái mong muốn ({current_status})"
        
        # Kiểm tra nếu đang ở trạng thái ngược lại
        if (target_action == "ON" and current_status == "Connect Grid") or \
           (target_action == "OFF" and current_status == "Disconnect Grid"):
            return False, f"LỖI: Đang ở trạng thái ngược lại ({current_status})"
        
        try:
            link_element = self.driver_manager.wait_for_element_clickable(
                By.ID, SELECTORS["grid_control"]["connect_link"], timeout=5
            )
            if not link_element:
                return False, "Không tìm thấy element điều khiển grid"
            
            self.logger.log_info(f"Thực hiện {target_action} grid...")
            
            # Thực hiện double click với ActionChains
            actions = ActionChains(self.driver_manager.driver)
            actions.double_click(link_element).perform()
            
            # CHỜ TRẠNG THÁI THAY ĐỔI - Sử dụng WebDriverWait thay vì time.sleep
            status_changed = self.driver_manager.wait_for_text_present(
                By.ID, SELECTORS["grid_control"]["connect_link"], expected_status_after, timeout=10
            )
            
            if status_changed:
                new_status = self.get_grid_status()
                return True, f"THÀNH CÔNG: Chuyển từ '{current_status}' sang '{new_status}'"
            else:
                new_status = self.get_grid_status()
                return False, f"LỖI: Trạng thái không thay đổi (Hiện tại: {new_status})"
                
        except Exception as e:
            return False, f"LỖI THỰC HIỆN: {e}"

class TaskProcessor:
    """Xử lý tác vụ đa luồng - Phiên bản 0.2"""
    
    def __init__(self):
        self.logger = InverterControlLogger()
    
    def process_single_inverter(self, task_info):
        """Xử lý một inverter duy nhất - Tối ưu với WebDriverWait"""
        full_inv_name, target_url, required_action, inv_status = task_info
        
        self.logger.log_info(f"Bắt đầu xử lý {required_action}", full_inv_name)
        
        # Kiểm tra trạng thái inverter
        if required_action == "ON" and inv_status == "FAULTY":
            self.logger.log_warning("Bỏ qua do trạng thái FAULTY", full_inv_name)
            return full_inv_name, "SKIPPED", "INV lỗi không thể bật"
        
        # Khởi tạo driver cho task này
        driver_manager = InverterDriver()
        driver = driver_manager.initialize_driver()
        if not driver:
            return full_inv_name, "FAILED", "Không thể khởi tạo driver"
        
        try:
            # Tạo controller với driver manager
            controller = InverterController(driver_manager)
            
            # Đăng nhập
            login_success = controller.login(target_url)
            
            if not login_success:
                return full_inv_name, "FAILED", "Đăng nhập thất bại"
            
            # Thực hiện hành động
            success, message = controller.perform_grid_action(required_action)
            
            if success:
                status = "SUCCESS"
                self.logger.log_success(message, full_inv_name)
            else:
                status = "FAILED"
                self.logger.log_error(message, full_inv_name)
            
            return full_inv_name, status, message
            
        except Exception as e:
            error_msg = f"Lỗi không xác định: {str(e)}"
            self.logger.log_error(error_msg, full_inv_name)
            return full_inv_name, "FAILED", error_msg
        
        finally:
            # Luôn đóng driver
            driver_manager.quit()
    
    def run_parallel_optimized(self, control_requests):
        """Chạy song song tối ưu - Phiên bản 0.2"""
        start_time = datetime.now()
        self.logger.log_info(f"🚀 Bắt đầu xử lý {len(control_requests)} yêu cầu - Phiên bản 0.2")
        
        # Tạo danh sách tác vụ
        tasks = self._prepare_tasks(control_requests)
        total_tasks = len(tasks)
        
        self.logger.log_info(f"📊 Tổng số tác vụ cần xử lý: {total_tasks}")
        
        if total_tasks == 0:
            self.logger.log_warning("⚠️ Không có tác vụ nào để xử lý!")
            return []
        
        # Xử lý song song
        results = []
        with ThreadPoolExecutor(max_workers=CONFIG["performance"]["max_workers"]) as executor:
            # Gửi tất cả tác vụ
            future_to_task = {
                executor.submit(self.process_single_inverter, task): task 
                for task in tasks
            }
            
            # Theo dõi tiến trình
            completed = 0
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    result = future.result(timeout=CONFIG["driver"]["timeout"])
                    results.append(result)
                    completed += 1
                    
                    # Log tiến trình
                    progress_percent = (completed / total_tasks) * 100
                    if completed % 3 == 0 or completed == total_tasks:  # Log ít hơn để giảm I/O
                        self.logger.log_info(
                            f"📈 Đã hoàn thành {completed}/{total_tasks} tác vụ "
                            f"({progress_percent:.1f}%)"
                        )
                        
                except Exception as e:
                    inv_name = task[0] if task else "Unknown"
                    self.logger.log_error(f"Lỗi xử lý tác vụ: {e}", inv_name)
                    results.append((inv_name, "FAILED", f"Lỗi xử lý: {e}"))
        
        # Phân tích kết quả
        self._analyze_results(results, start_time)
        
        return results
    
    def _prepare_tasks(self, control_requests):
        """Chuẩn bị danh sách tác vụ từ yêu cầu điều khiển"""
        tasks = []
        
        for zone_name, stations in SYSTEM_URLS.items():
            for station_name, inverters in stations.items():
                if station_name in control_requests:
                    request = control_requests[station_name]
                    required_action = request["action"]
                    required_count = request["count"]
                    
                    # Sắp xếp và lấy số lượng cần thiết
                    sorted_invs = sorted(inverters.items())
                    count_added = 0
                    
                    for inv_name, inv_info in sorted_invs:
                        if count_added >= required_count:
                            break
                            
                        full_inv_name = f"{station_name}-{inv_name}"
                        target_url = inv_info["url"]
                        inv_status = inv_info.get("status", "OK").upper()
                        
                        tasks.append((full_inv_name, target_url, required_action, inv_status))
                        count_added += 1
        
        return tasks
    
    def _analyze_results(self, results, start_time):
        """Phân tích và báo cáo kết quả - Phiên bản 0.2"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Thống kê
        stats = {
            "SUCCESS": 0,
            "FAILED": 0,
            "SKIPPED": 0
        }
        
        for _, status, _ in results:
            stats[status] = stats.get(status, 0) + 1
        
        # In báo cáo
        self.logger.log_info("=" * 60)
        self.logger.log_info("🎯 BÁO CÁO TỔNG KẾT - PHIÊN BẢN 0.2")
        self.logger.log_info("=" * 60)
        self.logger.log_info(f"📦 Tổng số tác vụ: {len(results)}")
        self.logger.log_info(f"✅ Thành công: {stats['SUCCESS']}")
        self.logger.log_info(f"❌ Thất bại: {stats['FAILED']}")
        self.logger.log_info(f"⏭️ Bỏ qua: {stats['SKIPPED']}")
        
        if len(results) > 0:
            success_rate = (stats['SUCCESS'] / len(results)) * 100
            self.logger.log_info(f"📊 Tỷ lệ thành công: {success_rate:.1f}%")
        
        # Tính thời gian trung bình mỗi task
        total_seconds = duration.total_seconds()
        if len(results) > 0:
            avg_time = total_seconds / len(results)
            self.logger.log_info(f"⏱️ Thời gian trung bình/task: {avg_time:.1f}s")
        
        self.logger.log_info(f"🕒 Tổng thời gian thực hiện: {duration}")
        
        # In lỗi chi tiết
        errors = [(name, msg) for name, status, msg in results if status == "FAILED"]
        if errors:
            self.logger.log_info("🔍 CHI TIẾT LỖI:")
            for name, msg in errors:
                self.logger.log_error(msg, name)

def main():
    """Hàm chính với menu lựa chọn - Phiên bản 0.2"""
    processor = TaskProcessor()
    
    # Các kịch bản điều khiển
    SCENARIOS = {
        "1": {"name": "Tắt một số inverter", "requests": CONTROL_REQUESTS_OFF},
        "2": {"name": "Bật một số inverter", "requests": CONTROL_REQUESTS_ON},
        "3": {"name": "Bật tất cả inverter", "requests": ON_ALL},
        "4": {"name": "Tùy chỉnh", "requests": None}
    }
    
    print("🚀 CHƯƠNG TRÌNH ĐIỀU KHIỂN INVERTER - PHIÊN BẢN 0.2")
    print("=" * 50)
    print("🎯 Tối ưu hiệu suất với WebDriverWait")
    print("⏱️  Loại bỏ hoàn toàn time.sleep")
    print("=" * 50)
    
    for key, scenario in SCENARIOS.items():
        print(f"{key}. {scenario['name']}")
    
    choice = input("\nChọn kịch bản (1-4): ").strip()
    
    if choice in SCENARIOS:
        if choice == "4":
            # Cho phép nhập tùy chỉnh
            custom_requests = {}
            print("\n🎛️  Chế độ tùy chỉnh")
            print("📝 Định dạng: TênStation SốLượng HànhĐộng")
            print("💡 Ví dụ: B3R1 5 OFF")
            print("⏹️  Nhập 'done' để kết thúc")
            
            while True:
                line = input("Nhập: ").strip()
                if line.lower() == 'done':
                    break
                try:
                    parts = line.split()
                    if len(parts) == 3:
                        station, count, action = parts
                        custom_requests[station] = {
                            "action": action.upper(),
                            "count": int(count)
                        }
                        print(f"✅ Đã thêm: {station} - {count} INV - {action}")
                    else:
                        print("❌ Định dạng không hợp lệ! Ví dụ: B3R1 5 OFF")
                except ValueError:
                    print("❌ Số lượng phải là số nguyên!")
            
            requests = custom_requests
        else:
            requests = SCENARIOS[choice]["requests"]
        
        print(f"\n🎯 Đang xử lý kịch bản: {SCENARIOS[choice]['name']}")
        print(f"📊 Số lượng yêu cầu: {len(requests)}")
        
        confirm = input("✅ Xác nhận thực hiện? (y/n): ").strip().lower()
        if confirm == 'y':
            processor.run_parallel_optimized(requests)
        else:
            print("⏹️ Đã hủy thực hiện.")
    else:
        print("❌ Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main()