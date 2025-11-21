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
import queue
from collections import deque
import time
import math

# Import cấu hình hệ thống
from system_config import SYSTEM_URLS, CONTROL_REQUESTS_OFF, CONTROL_REQUESTS_ON, ON_ALL

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

# SELECTORS
SELECTORS = {
    "login": {
        "dropdown_toggle": "#login-dropdown-list > a.dropdown-toggle",
        "username_field": "login-username",
        "password_field": "login-password", 
        "login_button": "login-buttons-password",
        "user_indicator": "installer"
    },
    "grid_control": {
        "connect_link": "link-grid-disconnect",
        "status_indicator": ["Disconnect Grid", "Connect Grid"]
    },
    "monitoring": {
        "status_line": "#status-line-dsp",
        "power_active": ".js-active-power",
        "navbar": ".navbar"
    }
}

class InverterControlLogger:
    """Lớp quản lý logging - Phiên bản 0.4.1"""
    
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
    
    def log_queue_stats(self, stats):
        """Log thống kê hàng đợi"""
        self.logger.info(f"📊 Hàng đợi - Chính: {stats['primary_queue']}, Retry: {stats['retry_queue']}, "
                        f"Hoàn thành: {stats['completed']}, Thất bại: {stats['failed']}")

class DynamicDriverPool:
    """Pool quản lý driver động dựa trên số lượng tasks"""
    
    def __init__(self):
        self.available_drivers = queue.Queue()
        self.in_use_drivers = set()
        self.lock = threading.Lock()
        self.logger = InverterControlLogger()
        self.is_initialized = False
        self.pool_size = 0
    
    def initialize_pool(self, total_tasks):
        """Khởi tạo pool driver dựa trên số lượng tasks"""
        if self.is_initialized:
            self.logger.log_info("✅ Driver pool đã được khởi tạo trước đó")
            return True
            
        # Tính toán số driver cần thiết
        self.pool_size = self._calculate_optimal_pool_size(total_tasks)
        self.logger.log_info(f"🔄 Tính toán: {total_tasks} tasks → {self.pool_size} drivers")
        
        successful_drivers = 0
        
        for i in range(self.pool_size):
            driver = self._create_driver()
            if driver:
                self.available_drivers.put(driver)
                successful_drivers += 1
                self.logger.log_info(f"🚀 Đã khởi tạo driver {successful_drivers}/{self.pool_size}")
            else:
                self.logger.log_error(f"❌ Không thể khởi tạo driver {i+1}")
        
        self.is_initialized = True
        self.logger.log_info(f"✅ Đã khởi tạo thành công {successful_drivers}/{self.pool_size} drivers")
        
        return successful_drivers > 0
    
    def _calculate_optimal_pool_size(self, total_tasks):
        """Tính toán số driver tối ưu dựa trên số lượng tasks"""
        # Công thức: min(max_pool_size, max(min_pool_size, ceil(total_tasks / tasks_per_driver)))
        calculated_size = math.ceil(total_tasks / CONFIG["performance"]["tasks_per_driver"])
        
        # Giới hạn trong khoảng min_pool_size đến max_pool_size
        optimal_size = max(CONFIG["driver"]["min_pool_size"], 
                          min(CONFIG["driver"]["max_pool_size"], calculated_size))
        
        self.logger.log_info(f"📊 Tính toán pool size: {total_tasks} tasks / {CONFIG['performance']['tasks_per_driver']} tasks/driver = {optimal_size} drivers")
        return optimal_size
    
    def _create_driver(self):
        """Tạo driver mới"""
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

            # Tối ưu hiệu suất
            chrome_options.add_experimental_option(
                "prefs", {
                    "profile.managed_default_content_settings.images": 2,
                    "profile.managed_default_content_settings.stylesheets": 2,
                    "profile.managed_default_content_settings.fonts": 2,
                    "profile.managed_default_content_settings.media_stream": 2,
                    "profile.default_content_setting_values.notifications": 2,
                }
            )
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(CONFIG["driver"]["page_load_timeout"])
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except Exception as e:
            self.logger.log_error(f"❌ Tạo driver thất bại: {e}")
            return None
    
    def get_driver(self, timeout=10):
        """Lấy driver từ pool"""
        if not self.is_initialized:
            self.logger.log_error("❌ Driver pool chưa được khởi tạo!")
            return None
            
        try:
            driver = self.available_drivers.get(timeout=timeout)
            with self.lock:
                self.in_use_drivers.add(driver)
            self.logger.log_debug(f"📥 Lấy driver từ pool, còn {self.available_drivers.qsize()} drivers available")
            return driver
        except queue.Empty:
            self.logger.log_warning("⚠️ Không còn driver available")
            return None
    
    def return_driver(self, driver):
        """Trả driver về pool"""
        if driver and self.is_initialized:
            try:
                # Clear cookies và cache để tái sử dụng sạch sẽ
                driver.delete_all_cookies()
                # Quay về trang trống
                driver.get("about:blank")
            except Exception as e:
                self.logger.log_debug(f"🔧 Lỗi khi reset driver: {e}")
            
            with self.lock:
                if driver in self.in_use_drivers:
                    self.in_use_drivers.remove(driver)
            
            self.available_drivers.put(driver)
            self.logger.log_debug(f"📤 Trả driver về pool, có {self.available_drivers.qsize()} drivers available")
    
    def cleanup(self):
        """Dọn dẹp toàn bộ pool"""
        if not self.is_initialized:
            return
            
        self.logger.log_info("🧹 Đang dọn dẹp driver pool...")
        
        # Đóng tất cả driver available
        closed_count = 0
        while not self.available_drivers.empty():
            try:
                driver = self.available_drivers.get_nowait()
                driver.quit()
                closed_count += 1
            except Exception as e:
                self.logger.log_debug(f"Lỗi khi đóng driver: {e}")
        
        # Đóng tất cả driver đang sử dụng
        with self.lock:
            for driver in self.in_use_drivers:
                try:
                    driver.quit()
                    closed_count += 1
                except Exception as e:
                    self.logger.log_debug(f"Lỗi khi đóng driver đang sử dụng: {e}")
            self.in_use_drivers.clear()
        
        self.is_initialized = False
        self.logger.log_info(f"✅ Đã đóng {closed_count} drivers")
    
    def get_pool_info(self):
        """Lấy thông tin pool"""
        with self.lock:
            return {
                "pool_size": self.pool_size,
                "available": self.available_drivers.qsize(),
                "in_use": len(self.in_use_drivers),
                "is_initialized": self.is_initialized
            }

class InverterTask:
    """Lớp đại diện cho một task inverter với tracking retry"""
    
    def __init__(self, full_inv_name, target_url, required_action, inv_status):
        self.full_inv_name = full_inv_name
        self.target_url = target_url
        self.required_action = required_action
        self.inv_status = inv_status
        self.retry_count = 0
        self.last_error = None
        self.created_time = datetime.now()
        self.priority = 1  # Độ ưu tiên (1: cao, 2: thấp)
    
    def __str__(self):
        return f"InverterTask({self.full_inv_name}, {self.required_action}, retry={self.retry_count})"
    
    def should_retry(self):
        """Kiểm tra xem task có nên retry không"""
        return self.retry_count < CONFIG["performance"]["max_retry_queue"]
    
    def mark_retry(self, error_msg=None):
        """Đánh dấu task cần retry"""
        self.retry_count += 1
        self.last_error = error_msg
        self.priority = 2  # Giảm độ ưu tiên sau mỗi lần retry
        return self

class SmartTaskQueue:
    """Hàng đợi thông minh quản lý task và retry"""
    
    def __init__(self):
        self.primary_queue = deque()  # Hàng đợi chính
        self.retry_queue = deque()    # Hàng đợi retry
        self.completed_tasks = []     # Task đã hoàn thành
        self.failed_tasks = []        # Task thất bại hoàn toàn
        self.logger = InverterControlLogger()
        self.lock = threading.Lock()  # Lock cho thread safety
    
    def add_tasks(self, tasks):
        """Thêm tasks vào hàng đợi chính"""
        with self.lock:
            for task in tasks:
                self.primary_queue.append(task)
            self.logger.log_info(f"📥 Đã thêm {len(tasks)} tasks vào hàng đợi chính")
    
    def get_next_batch(self, batch_size):
        """Lấy một batch tasks để xử lý song song"""
        with self.lock:
            batch = []
            
            # Ưu tiên lấy từ primary queue trước
            while self.primary_queue and len(batch) < batch_size:
                batch.append(self.primary_queue.popleft())
            
            # Nếu chưa đủ batch size, lấy từ retry queue
            while self.retry_queue and len(batch) < batch_size:
                task = self.retry_queue.popleft()
                self.logger.log_info(f"🔄 Lấy task từ retry queue: {task.full_inv_name} (retry {task.retry_count})")
                batch.append(task)
            
            return batch
    
    def add_to_retry_queue(self, task, error_msg=None):
        """Thêm task vào hàng đợi retry"""
        with self.lock:
            if task.should_retry():
                task.mark_retry(error_msg)
                self.retry_queue.append(task)
                self.logger.log_warning(f"⏳ Đã chuyển {task.full_inv_name} sang retry queue (lần {task.retry_count})")
                return True
            else:
                self.failed_tasks.append(task)
                self.logger.log_error(f"💥 Task {task.full_inv_name} đã vượt quá số lần retry tối đa")
                return False
    
    def mark_completed(self, task, status, message):
        """Đánh dấu task hoàn thành"""
        with self.lock:
            task.completion_status = status
            task.completion_message = message
            task.completed_time = datetime.now()
            self.completed_tasks.append(task)
    
    def has_pending_tasks(self):
        """Kiểm tra còn task pending không"""
        with self.lock:
            return len(self.primary_queue) > 0 or len(self.retry_queue) > 0
    
    def get_stats(self):
        """Lấy thống kê hàng đợi"""
        with self.lock:
            return {
                "primary_queue": len(self.primary_queue),
                "retry_queue": len(self.retry_queue),
                "completed": len(self.completed_tasks),
                "failed": len(self.failed_tasks),
                "total_retries": sum(task.retry_count for task in self.completed_tasks + self.failed_tasks)
            }

class InverterController:
    """Lớp điều khiển inverter với driver từ pool"""
    
    def __init__(self, driver):
        self.driver = driver
        self.logger = InverterControlLogger()
    
    def wait_for_element(self, by, value, timeout=None):
        """Chờ element xuất hiện"""
        try:
            wait_timeout = timeout or CONFIG["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            return None
    
    def wait_for_element_clickable(self, by, value, timeout=None):
        """Chờ element có thể click"""
        try:
            wait_timeout = timeout or CONFIG["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            return None
    
    def wait_for_text_present(self, by, value, text, timeout=None):
        """Chờ text xuất hiện"""
        try:
            wait_timeout = timeout or CONFIG["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.text_to_be_present_in_element((by, value), text))
        except TimeoutException:
            return False
    
    def wait_for_page_loaded(self, timeout=None):
        """Chờ trang web load hoàn tất"""
        try:
            wait_timeout = timeout or CONFIG["driver"]["page_load_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            return False
    
    def fast_login(self, url, username=None, password=None):
        """Đăng nhập nhanh với driver được tái sử dụng"""
        username = username or CONFIG["credentials"]["username"]
        password = password or CONFIG["credentials"]["password"]
        
        try:
            if not url.startswith(('http://', 'https://')):
                url = f"http://{url}"
            
            self.driver.get(url)
            
            # Chờ trang load
            if not self.wait_for_page_loaded(timeout=15):
                self.logger.log_debug("Trang load chậm, tiếp tục thử...")
                return False
            
            # Kiểm tra đã đăng nhập chưa
            if self.wait_for_text_present(By.TAG_NAME, "body", "installer", timeout=2):
                self.logger.log_debug("Đã đăng nhập sẵn")
                return True
            
            # Đăng nhập
            dropdown = self.wait_for_element_clickable(
                By.CSS_SELECTOR, SELECTORS["login"]["dropdown_toggle"], timeout=3
            )
            if dropdown:
                dropdown.click()
                # Chờ dropdown mở
                self.wait_for_element(By.ID, SELECTORS["login"]["username_field"], timeout=2)
            
            # Nhập username
            username_field = self.wait_for_element(By.ID, SELECTORS["login"]["username_field"], timeout=3)
            if not username_field:
                self.logger.log_debug("Không tìm thấy field username, có thể đã đăng nhập")
                return True
            
            username_field.clear()
            username_field.send_keys(username)
            
            # Nhập password
            password_field = self.wait_for_element(By.ID, SELECTORS["login"]["password_field"], timeout=3)
            if not password_field:
                self.logger.log_debug("Không tìm thấy field password")
                return False
            
            password_field.clear()
            password_field.send_keys(password)
            
            # Click đăng nhập
            login_btn = self.wait_for_element_clickable(By.ID, SELECTORS["login"]["login_button"], timeout=3)
            if not login_btn:
                self.logger.log_debug("Không tìm thấy nút đăng nhập")
                return False
            
            login_btn.click()
            
            # Chờ đăng nhập thành công
            if self.wait_for_text_present(By.TAG_NAME, "body", "installer", timeout=8):
                self.logger.log_debug("Đăng nhập thành công")
                return True
            
            # Thử cách khác để kiểm tra đăng nhập
            if self.wait_for_element(By.CSS_SELECTOR, SELECTORS["monitoring"]["navbar"], timeout=3):
                self.logger.log_debug("Đăng nhập thành công (qua navbar)")
                return True
            
            self.logger.log_debug("Không xác định được trạng thái đăng nhập")
            return False
                
        except Exception as e:
            self.logger.log_debug(f"Login thất bại: {e}")
            return False
    
    def get_grid_status(self):
        """Lấy trạng thái grid"""
        try:
            link_element = self.wait_for_element(
                By.ID, SELECTORS["grid_control"]["connect_link"], timeout=3
            )
            if link_element:
                status = link_element.text.strip()
                self.logger.log_debug(f"Trạng thái grid: {status}")
                return status
            else:
                self.logger.log_debug("Không tìm thấy element grid control")
        except Exception as e:
            self.logger.log_debug(f"Lỗi khi lấy trạng thái grid: {e}")
        return None
    
    def perform_grid_action(self, target_action):
        """Thực hiện hành động grid"""
        current_status = self.get_grid_status()
        
        if not current_status:
            return False, "Không thể xác định trạng thái hiện tại"
        
        expected_status_after = "Disconnect Grid" if target_action == "ON" else "Connect Grid"
        
        # Kiểm tra trạng thái hiện tại
        if (target_action == "ON" and current_status == "Disconnect Grid") or \
           (target_action == "OFF" and current_status == "Connect Grid"):
            return True, f"BỎ QUA: Đã ở trạng thái mong muốn ({current_status})"
        
        if (target_action == "ON" and current_status == "Connect Grid") or \
           (target_action == "OFF" and current_status == "Disconnect Grid"):
            return False, f"LỖI: Đang ở trạng thái ngược lại ({current_status})"
        
        try:
            link_element = self.wait_for_element_clickable(
                By.ID, SELECTORS["grid_control"]["connect_link"], timeout=3
            )
            if not link_element:
                return False, "Không tìm thấy element điều khiển grid"
            
            self.logger.log_debug(f"Thực hiện {target_action} grid...")
            
            # Thực hiện double click
            actions = ActionChains(self.driver)
            actions.double_click(link_element).perform()
            
            # Chờ trạng thái thay đổi
            status_changed = self.wait_for_text_present(
                By.ID, SELECTORS["grid_control"]["connect_link"], expected_status_after, timeout=8
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
    """Xử lý tác vụ với Dynamic Driver Pool - Phiên bản 0.4.1"""
    
    def __init__(self):
        self.logger = InverterControlLogger()
        self.task_queue = SmartTaskQueue()
        self.driver_pool = DynamicDriverPool()  # Dynamic pool
    
    def prepare_tasks(self, control_requests):
        """Chuẩn bị tasks và tính toán số lượng"""
        tasks = []
        total_inverters = 0
        
        for zone_name, stations in SYSTEM_URLS.items():
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
        """Xử lý một inverter với driver từ pool"""
        self.logger.log_info(f"Bắt đầu xử lý {task.required_action}", task.full_inv_name)
        
        # Kiểm tra trạng thái inverter
        if task.required_action == "ON" and task.inv_status == "FAULTY":
            self.logger.log_warning("Bỏ qua do trạng thái FAULTY", task.full_inv_name)
            return task, "SKIPPED", "INV lỗi không thể bật"
        
        # LẤY DRIVER TỪ POOL (thay vì khởi tạo mới)
        driver = self.driver_pool.get_driver()
        if not driver:
            return task, "RETRY", "Không thể lấy driver từ pool"
        
        try:
            # Tạo controller với driver từ pool
            controller = InverterController(driver)
            
            # Đăng nhập và xử lý
            login_success = controller.fast_login(task.target_url)
            
            if not login_success:
                return task, "RETRY", "Đăng nhập thất bại"
            
            success, message = controller.perform_grid_action(task.required_action)
            
            if success:
                status = "SUCCESS"
                self.logger.log_success(message, task.full_inv_name)
            else:
                # Phân loại lỗi thông minh
                if "BỎ QUA" in message:
                    status = "SUCCESS"  # Coi như thành công
                    self.logger.log_info(message, task.full_inv_name)
                elif "LỖI" in message and "ngược lại" in message:
                    status = "FAILED"   # Lỗi vĩnh viễn
                    self.logger.log_error(message, task.full_inv_name)
                else:
                    status = "RETRY"    # Lỗi tạm thời
                    self.logger.log_warning(message, task.full_inv_name)
            
            return task, status, message
            
        except Exception as e:
            error_msg = f"Lỗi không xác định: {str(e)}"
            self.logger.log_error(error_msg, task.full_inv_name)
            return task, "RETRY", error_msg
        
        finally:
            # TRẢ DRIVER VỀ POOL (thay vì đóng)
            self.driver_pool.return_driver(driver)
    
    def run_parallel_optimized(self, control_requests):
        """Chạy song song với dynamic driver pool"""
        start_time = datetime.now()
        self.logger.log_info(f"🚀 Bắt đầu xử lý {len(control_requests)} yêu cầu - Phiên bản 0.4.1 (Dynamic Driver Pool)")
        
        try:
            # Chuẩn bị tasks và tính toán số lượng
            tasks, total_inverters = self.prepare_tasks(control_requests)
            total_tasks = len(tasks)
            
            self.logger.log_info(f"📊 Tổng số inverters cần xử lý: {total_inverters}")
            self.logger.log_info(f"📦 Tổng số tasks: {total_tasks}")
            
            if total_tasks == 0:
                self.logger.log_warning("⚠️ Không có tác vụ nào để xử lý!")
                return []
            
            # KHỞI TẠO DRIVER POOL DỰA TRÊN SỐ LƯỢNG TASKS
            self.logger.log_info("🔄 Đang khởi tạo driver pool...")
            pool_success = self.driver_pool.initialize_pool(total_tasks)
            
            if not pool_success:
                self.logger.log_error("❌ Không thể khởi tạo driver pool!")
                return []
            
            # Hiển thị thông tin pool
            pool_info = self.driver_pool.get_pool_info()
            self.logger.log_info(f"🎯 Driver pool: {pool_info['pool_size']} drivers (Available: {pool_info['available']}, In Use: {pool_info['in_use']})")
            
            # Thêm tasks vào hàng đợi
            self.task_queue.add_tasks(tasks)
            
            # Xử lý với driver pool
            completed_count = 0
            batch_number = 0
            
            while self.task_queue.has_pending_tasks():
                batch_number += 1
                batch_stats = self._process_batch(batch_number)
                completed_count += batch_stats["completed"]
                
                queue_stats = self.task_queue.get_stats()
                progress_percent = (completed_count / total_tasks) * 100
                
                self.logger.log_info(
                    f"📦 Batch {batch_number}: Hoàn thành {batch_stats['completed']}, "
                    f"Retry {batch_stats['retried']}, Thất bại {batch_stats['failed']}"
                )
                self.logger.log_queue_stats(queue_stats)
                self.logger.log_info(f"📈 Tiến trình tổng: {completed_count}/{total_tasks} ({progress_percent:.1f}%)")
                
                # Nếu chỉ còn retry queue và ít tasks, dừng sớm
                if queue_stats["primary_queue"] == 0 and queue_stats["retry_queue"] < 3:
                    self.logger.log_info("⏹️ Chỉ còn ít tasks retry, kết thúc sớm")
                    break
            
            # Xử lý retry cuối cùng
            final_retry_stats = self._process_final_retry()
            completed_count += final_retry_stats["completed"]
            
            # Phân tích kết quả
            final_results = self._get_final_results()
            self._analyze_results(final_results, start_time, total_tasks)
            
            return final_results
            
        finally:
            # DỌN DẸP DRIVER POOL KHI KẾT THÚC CHƯƠNG TRÌNH
            self.driver_pool.cleanup()
    
    def _process_batch(self, batch_number):
        """Xử lý một batch tasks"""
        batch_stats = {"completed": 0, "retried": 0, "failed": 0}
        
        # Lấy batch tasks để xử lý
        batch_tasks = self.task_queue.get_next_batch(CONFIG["performance"]["max_workers"])
        
        if not batch_tasks:
            return batch_stats
        
        self.logger.log_info(f"🔄 Xử lý batch {batch_number} với {len(batch_tasks)} tasks")
        
        with ThreadPoolExecutor(max_workers=CONFIG["performance"]["max_workers"]) as executor:
            # Gửi tasks để xử lý song song
            future_to_task = {
                executor.submit(self.process_single_inverter, task): task 
                for task in batch_tasks
            }
            
            # Xử lý kết quả
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    processed_task, status, message = future.result(timeout=CONFIG["driver"]["timeout"])
                    
                    if status == "SUCCESS":
                        self.task_queue.mark_completed(processed_task, status, message)
                        batch_stats["completed"] += 1
                    elif status == "SKIPPED":
                        self.task_queue.mark_completed(processed_task, status, message)
                        batch_stats["completed"] += 1
                    elif status == "RETRY":
                        if self.task_queue.add_to_retry_queue(processed_task, message):
                            batch_stats["retried"] += 1
                        else:
                            batch_stats["failed"] += 1
                    else:  # FAILED
                        self.task_queue.mark_completed(processed_task, status, message)
                        batch_stats["failed"] += 1
                        
                except Exception as e:
                    self.logger.log_error(f"Lỗi xử lý task: {e}", task.full_inv_name)
                    if self.task_queue.add_to_retry_queue(task, str(e)):
                        batch_stats["retried"] += 1
                    else:
                        batch_stats["failed"] += 1
        
        return batch_stats
    
    def _process_final_retry(self):
        """Xử lý retry cuối cùng với ít workers hơn"""
        queue_stats = self.task_queue.get_stats()
        if queue_stats["retry_queue"] == 0:
            return {"completed": 0, "retried": 0, "failed": 0}
        
        self.logger.log_info(f"🔄 Xử lý {queue_stats['retry_queue']} tasks retry cuối cùng")
        
        final_stats = {"completed": 0, "retried": 0, "failed": 0}
        retry_workers = min(2, queue_stats["retry_queue"])  # Chỉ dùng 2 workers cho retry cuối
        
        with ThreadPoolExecutor(max_workers=retry_workers) as executor:
            batch_tasks = self.task_queue.get_next_batch(queue_stats["retry_queue"])
            
            future_to_task = {
                executor.submit(self.process_single_inverter, task): task 
                for task in batch_tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    processed_task, status, message = future.result(timeout=CONFIG["driver"]["timeout"])
                    
                    if status in ["SUCCESS", "SKIPPED"]:
                        self.task_queue.mark_completed(processed_task, status, message)
                        final_stats["completed"] += 1
                    else:
                        self.task_queue.mark_completed(processed_task, "FAILED", f"Final retry failed: {message}")
                        final_stats["failed"] += 1
                        
                except Exception as e:
                    self.logger.log_error(f"Final retry timeout: {e}", task.full_inv_name)
                    self.task_queue.mark_completed(task, "FAILED", "Final retry timeout")
                    final_stats["failed"] += 1
        
        return final_stats
    
    def _get_final_results(self):
        """Lấy kết quả cuối cùng"""
        results = []
        
        for task in self.task_queue.completed_tasks:
            results.append((task.full_inv_name, task.completion_status, task.completion_message))
        
        for task in self.task_queue.failed_tasks:
            results.append((task.full_inv_name, "FAILED", f"Vượt quá số lần retry: {task.last_error}"))
        
        return results
    
    def _analyze_results(self, results, start_time, total_tasks):
        """Phân tích và báo cáo kết quả"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Thống kê
        stats = {"SUCCESS": 0, "FAILED": 0, "SKIPPED": 0}
        for _, status, _ in results:
            stats[status] = stats.get(status, 0) + 1
        
        queue_stats = self.task_queue.get_stats()
        pool_info = self.driver_pool.get_pool_info()
        
        # In báo cáo
        self.logger.log_info("=" * 60)
        self.logger.log_info("🎯 BÁO CÁO TỔNG KẾT - PHIÊN BẢN 0.4.1 (DYNAMIC DRIVER POOL)")
        self.logger.log_info("=" * 60)
        self.logger.log_info(f"📦 Tổng số tác vụ: {total_tasks}")
        self.logger.log_info(f"🎯 Số drivers sử dụng: {pool_info['pool_size']}")
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
        
        # In lỗi chi tiết
        errors = [(name, msg) for name, status, msg in results if status == "FAILED"]
        if errors:
            self.logger.log_info("🔍 CHI TIẾT LỖI:")
            for name, msg in errors:
                self.logger.log_error(msg, name)

def main():
    """Hàm chính - Phiên bản 0.4.1"""
    processor = TaskProcessor()
    
    SCENARIOS = {
        "1": {"name": "Tắt một số inverter", "requests": CONTROL_REQUESTS_OFF},
        "2": {"name": "Bật một số inverter", "requests": CONTROL_REQUESTS_ON},
        "3": {"name": "Bật tất cả inverter", "requests": ON_ALL},
        "4": {"name": "Tùy chỉnh", "requests": None}
    }
    
    print("🚀 CHƯƠNG TRÌNH ĐIỀU KHIỂN INVERTER - PHIÊN BẢN 0.4.1")
    print("=" * 50)
    print("🎯 Dynamic Driver Pool - Tối ưu tài nguyên")
    print("⚡ Chỉ tạo driver khi cần thiết")
    print("📊 Tính toán số driver dựa trên số lượng INV")
    print("🔄 Xử lý thông minh với retry mechanism")
    print("=" * 50)
    
    for key, scenario in SCENARIOS.items():
        print(f"{key}. {scenario['name']}")
    
    choice = input("\nChọn kịch bản (1-4): ").strip()
    
    if choice in SCENARIOS:
        if choice == "4":
            custom_requests = {}
            print("\n🎛️ Chế độ tùy chỉnh")
            print("📝 Định dạng: TênStation SốLượng HànhĐộng")
            print("💡 Ví dụ: B3R1 5 OFF")
            print("⏹️ Nhập 'done' để kết thúc")
            
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
        
        print(f"\n🎯 Đang xử lý: {SCENARIOS[choice]['name']}")
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