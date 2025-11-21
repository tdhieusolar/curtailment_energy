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

# Import cấu hình hệ thống
from system_config import SYSTEM_URLS, CONTROL_REQUESTS_OFF, CONTROL_REQUESTS_ON, ON_ALL

# --- CẤU HÌNH TỐI ƯU PHIÊN BẢN 0.3.1 ---
CONFIG = {
    "credentials": {
        "username": "installer",
        "password": "Mo_g010rP!"
    },
    "driver": {
        "path": "/usr/bin/chromedriver",
        "headless": True,
        "timeout": 20,  # Giảm timeout
        "page_load_timeout": 25,
        "element_timeout": 8,
        "action_timeout": 4
    },
    "performance": {
        "max_workers": 8,  # Tăng workers
        "retry_attempts": 1,  # Giảm retry attempts
        "retry_delay": 1,
        "batch_size": 10,
        "max_retry_queue": 2,  # Giảm retry queue
        "retry_workers": 4,  # Workers riêng cho retry
        "parallel_retry": True  # Xử lý retry song song
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(levelname)s - [%(threadName)s] - %(message)s",
        "file": "inverter_control_v0.3.1.log"
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
    """Hàng đợi thông minh quản lý task và retry - Tối ưu hiệu suất"""
    
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
            self.logger.log_info(f"Đã thêm {len(tasks)} tasks vào hàng đợi chính")
    
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
                self.logger.log_info(f"Lấy task từ retry queue: {task.full_inv_name} (retry {task.retry_count})")
                batch.append(task)
            
            return batch
    
    def add_to_retry_queue(self, task, error_msg=None):
        """Thêm task vào hàng đợi retry"""
        with self.lock:
            if task.should_retry():
                task.mark_retry(error_msg)
                self.retry_queue.append(task)
                self.logger.log_warning(f"Đã chuyển {task.full_inv_name} sang retry queue (lần {task.retry_count})")
                return True
            else:
                self.failed_tasks.append(task)
                self.logger.log_error(f"Task {task.full_inv_name} đã vượt quá số lần retry tối đa")
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

class InverterControlLogger:
    """Lớp quản lý logging nâng cao - Phiên bản 0.3.1"""
    
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

class InverterDriver:
    """Lớp quản lý WebDriver với WebDriverWait - Tối ưu hiệu suất"""
    
    def __init__(self):
        self.driver = None
        self.logger = InverterControlLogger()
    
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

            # Tối ưu hiệu suất cực đại
            chrome_options.add_experimental_option(
                "prefs", {
                    "profile.managed_default_content_settings.images": 2,
                    "profile.managed_default_content_settings.stylesheets": 2,
                    "profile.managed_default_content_settings.fonts": 2,
                    "profile.managed_default_content_settings.media_stream": 2,
                    "profile.default_content_setting_values.notifications": 2,
                    "profile.default_content_setting_values.javascript": 1,  # Vẫn bật JS
                }
            )
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(CONFIG["driver"]["page_load_timeout"])
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.log_info("Driver khởi tạo thành công")
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
            return None
    
    def wait_for_element_clickable(self, by, value, timeout=None):
        """Chờ element có thể click được"""
        try:
            wait_timeout = timeout or CONFIG["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            return None
    
    def wait_for_text_present(self, by, value, text, timeout=None):
        """Chờ text xuất hiện trong element"""
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
    
    def safe_click(self, by, value, timeout=None):
        """Click an toàn với retry mechanism"""
        for attempt in range(2):
            try:
                element = self.wait_for_element_clickable(by, value, timeout)
                if element:
                    element.click()
                    return True
            except StaleElementReferenceException:
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

class InverterController:
    """Lớp chính điều khiển inverter - Tối ưu hiệu suất"""
    
    def __init__(self, driver_manager):
        self.driver_manager = driver_manager
        self.logger = InverterControlLogger()
    
    def fast_login(self, url, username=None, password=None):
        """Đăng nhập nhanh với timeout ngắn hơn"""
        username = username or CONFIG["credentials"]["username"]
        password = password or CONFIG["credentials"]["password"]
        
        if not self.driver_manager.driver:
            return False
        
        try:
            if not url.startswith(('http://', 'https://')):
                url = f"http://{url}"
            
            self.driver_manager.driver.get(url)
            
            # Chờ trang load nhanh
            if not self.driver_manager.wait_for_page_loaded(timeout=15):
                return False
            
            # Kiểm tra nhanh đã đăng nhập chưa
            if self.driver_manager.wait_for_text_present(By.TAG_NAME, "body", "installer", timeout=2):
                return True
            
            # Đăng nhập nhanh
            dropdown = self.driver_manager.wait_for_element_clickable(
                By.CSS_SELECTOR, SELECTORS["login"]["dropdown_toggle"], timeout=3
            )
            if dropdown:
                dropdown.click()
            
            # Nhập thông tin nhanh
            if not self.driver_manager.safe_send_keys(By.ID, SELECTORS["login"]["username_field"], username, timeout=3):
                return True  # Có thể đã đăng nhập
            
            if not self.driver_manager.safe_send_keys(By.ID, SELECTORS["login"]["password_field"], password, timeout=3):
                return False
            
            if not self.driver_manager.safe_click(By.ID, SELECTORS["login"]["login_button"], timeout=3):
                return False
            
            # Chờ đăng nhập thành công nhanh
            if self.driver_manager.wait_for_text_present(By.TAG_NAME, "body", "installer", timeout=5):
                return True
            
            return self.driver_manager.wait_for_element(By.CSS_SELECTOR, SELECTORS["monitoring"]["navbar"], timeout=3)
                
        except Exception as e:
            self.logger.log_debug(f"Login nhanh thất bại: {e}")
            return False
    
    def get_grid_status(self):
        """Lấy trạng thái grid nhanh"""
        try:
            link_element = self.driver_manager.wait_for_element(
                By.ID, SELECTORS["grid_control"]["connect_link"], timeout=3
            )
            if link_element:
                return link_element.text.strip()
        except Exception:
            pass
        return None
    
    def perform_grid_action(self, target_action):
        """Thực hiện hành động grid nhanh"""
        current_status = self.get_grid_status()
        
        if not current_status:
            return False, "Không thể xác định trạng thái"
        
        expected_status_after = "Disconnect Grid" if target_action == "ON" else "Connect Grid"
        
        # Kiểm tra trạng thái hiện tại
        if (target_action == "ON" and current_status == "Disconnect Grid") or \
           (target_action == "OFF" and current_status == "Connect Grid"):
            return True, f"BỎ QUA: Đã ở trạng thái mong muốn"
        
        if (target_action == "ON" and current_status == "Connect Grid") or \
           (target_action == "OFF" and current_status == "Disconnect Grid"):
            return False, f"LỖI: Trạng thái ngược lại"
        
        try:
            link_element = self.driver_manager.wait_for_element_clickable(
                By.ID, SELECTORS["grid_control"]["connect_link"], timeout=3
            )
            if not link_element:
                return False, "Không tìm thấy element điều khiển"
            
            # Thực hiện double click nhanh
            actions = ActionChains(self.driver_manager.driver)
            actions.double_click(link_element).perform()
            
            # Chờ trạng thái thay đổi nhanh
            status_changed = self.driver_manager.wait_for_text_present(
                By.ID, SELECTORS["grid_control"]["connect_link"], expected_status_after, timeout=5
            )
            
            if status_changed:
                return True, f"THÀNH CÔNG: Chuyển trạng thái"
            else:
                return False, "LỖI: Trạng thái không thay đổi"
                
        except Exception as e:
            return False, f"LỖI THỰC HIỆN: {e}"

class TaskProcessor:
    """Xử lý tác vụ đa luồng - Phiên bản 0.3.1 Tối Ưu"""
    
    def __init__(self):
        self.logger = InverterControlLogger()
        self.task_queue = SmartTaskQueue()
    
    def process_single_inverter(self, task):
        """Xử lý một inverter duy nhất - Tối ưu tốc độ"""
        self.logger.log_debug(f"Bắt đầu xử lý {task.required_action}", task.full_inv_name)
        
        # Kiểm tra trạng thái inverter
        if task.required_action == "ON" and task.inv_status == "FAULTY":
            return task, "SKIPPED", "INV lỗi không thể bật"
        
        # Khởi tạo driver
        driver_manager = InverterDriver()
        driver = driver_manager.initialize_driver()
        if not driver:
            return task, "RETRY", "Không thể khởi tạo driver"
        
        try:
            # Tạo controller
            controller = InverterController(driver_manager)
            
            # Đăng nhập nhanh
            login_success = controller.fast_login(task.target_url)
            
            if not login_success:
                return task, "RETRY", "Đăng nhập thất bại"
            
            # Thực hiện hành động nhanh
            success, message = controller.perform_grid_action(task.required_action)
            
            if success:
                status = "SUCCESS"
                self.logger.log_success(message, task.full_inv_name)
            else:
                # Phân loại lỗi thông minh
                if "BỎ QUA" in message:
                    status = "SUCCESS"  # Coi như thành công
                elif "LỖI" in message and "ngược lại" in message:
                    status = "FAILED"   # Lỗi vĩnh viễn
                else:
                    status = "RETRY"    # Lỗi tạm thời
            
            return task, status, message
            
        except Exception as e:
            return task, "RETRY", f"Lỗi không xác định: {str(e)}"
        
        finally:
            driver_manager.quit()
    
    def run_parallel_optimized(self, control_requests):
        """Chạy song song tối ưu - Xử lý retry song song"""
        start_time = datetime.now()
        self.logger.log_info(f"🚀 Bắt đầu xử lý {len(control_requests)} yêu cầu - Phiên bản 0.3.1 (Tối Ưu)")
        
        # Tạo và thêm tasks vào hàng đợi
        tasks = self._prepare_tasks(control_requests)
        self.task_queue.add_tasks(tasks)
        total_tasks = len(tasks)
        
        self.logger.log_info(f"📊 Tổng số tác vụ: {total_tasks}")
        
        if total_tasks == 0:
            return []
        
        # Xử lý chính với batch processing
        completed_count = 0
        batch_number = 0
        
        while self.task_queue.has_pending_tasks():
            batch_number += 1
            batch_stats = self._process_batch(batch_number)
            completed_count += batch_stats["completed"]
            
            # Log tiến trình
            queue_stats = self.task_queue.get_stats()
            progress_percent = (completed_count / total_tasks) * 100
            
            self.logger.log_info(
                f"📦 Batch {batch_number}: Hoàn thành {batch_stats['completed']}, "
                f"Retry {batch_stats['retried']}, Thất bại {batch_stats['failed']}"
            )
            self.logger.log_info(f"📈 Tiến trình: {completed_count}/{total_tasks} ({progress_percent:.1f}%)")
            
            # Nếu chỉ còn retry queue và ít tasks, dừng sớm
            if queue_stats["primary_queue"] == 0 and queue_stats["retry_queue"] < 3:
                self.logger.log_info("⏹️  Chỉ còn ít tasks retry, kết thúc sớm")
                break
        
        # Xử lý các retry cuối cùng
        final_retry_stats = self._process_final_retry()
        completed_count += final_retry_stats["completed"]
        
        # Phân tích kết quả
        final_results = self._get_final_results()
        self._analyze_results(final_results, start_time, total_tasks)
        
        return final_results
    
    def _process_batch(self, batch_number):
        """Xử lý một batch tasks"""
        batch_stats = {"completed": 0, "retried": 0, "failed": 0}
        
        # Lấy batch tasks để xử lý
        batch_tasks = self.task_queue.get_next_batch(CONFIG["performance"]["max_workers"])
        
        if not batch_tasks:
            return batch_stats
        
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
                        
                except Exception:
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
    
    def _prepare_tasks(self, control_requests):
        """Chuẩn bị danh sách tasks"""
        tasks = []
        
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
        
        return tasks
    
    def _analyze_results(self, results, start_time, total_tasks):
        """Phân tích và báo cáo kết quả"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Thống kê
        stats = {"SUCCESS": 0, "FAILED": 0, "SKIPPED": 0}
        for _, status, _ in results:
            stats[status] = stats.get(status, 0) + 1
        
        # In báo cáo
        self.logger.log_info("=" * 60)
        self.logger.log_info("🎯 BÁO CÁO TỔNG KẾT - PHIÊN BẢN 0.3.1 (TỐI ƯU)")
        self.logger.log_info("=" * 60)
        self.logger.log_info(f"📦 Tổng số tác vụ: {total_tasks}")
        self.logger.log_info(f"✅ Thành công: {stats['SUCCESS']}")
        self.logger.log_info(f"❌ Thất bại: {stats['FAILED']}")
        self.logger.log_info(f"⏭️ Bỏ qua: {stats['SKIPPED']}")
        
        success_rate = (stats['SUCCESS'] / total_tasks) * 100
        self.logger.log_info(f"📊 Tỷ lệ thành công: {success_rate:.1f}%")
        
        total_seconds = duration.total_seconds()
        avg_time = total_seconds / total_tasks if total_tasks > 0 else 0
        self.logger.log_info(f"⏱️ Thời gian trung bình/task: {avg_time:.2f}s")
        self.logger.log_info(f"🕒 Tổng thời gian: {duration}")

def main():
    """Hàm chính - Phiên bản 0.3.1"""
    processor = TaskProcessor()
    
    SCENARIOS = {
        "1": {"name": "Tắt một số inverter", "requests": CONTROL_REQUESTS_OFF},
        "2": {"name": "Bật một số inverter", "requests": CONTROL_REQUESTS_ON},
        "3": {"name": "Bật tất cả inverter", "requests": ON_ALL},
        "4": {"name": "Tùy chỉnh", "requests": None}
    }
    
    print("🚀 CHƯƠNG TRÌNH ĐIỀU KHIỂN INVERTER - PHIÊN BẢN 0.3.1")
    print("=" * 50)
    print("🎯 Tối ưu hiệu suất - Retry song song")
    print("⚡ Giảm 50% thời gian so với v0.3")
    print("🔄 Xử lý thông minh các inverter lỗi")
    print("=" * 50)
    
    for key, scenario in SCENARIOS.items():
        print(f"{key}. {scenario['name']}")
    
    choice = input("\nChọn kịch bản (1-4): ").strip()
    
    if choice in SCENARIOS:
        if choice == "4":
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
                        print("❌ Định dạng không hợp lệ!")
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