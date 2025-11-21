"""
Pool quản lý driver động dựa trên số lượng tasks
"""

import math
import queue
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from core.logger import InverterControlLogger
from config.settings import CONFIG

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