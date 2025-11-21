# core/driver_pool.py
"""
Pool quản lý driver động - Phiên bản 0.5.3 - Optimized Pool Size
"""

import math
import queue
import threading
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import WebDriverException
from core.logger import InverterControlLogger

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
        
        # Sử dụng Semaphore để kiểm soát truy cập
        self.driver_semaphore = threading.Semaphore(0)  # Bắt đầu với 0
        
    def initialize_pool(self, total_tasks):
        """Khởi tạo pool driver - Phiên bản tối ưu cho ít tasks"""
        if self.is_initialized:
            self.logger.log_info("✅ Driver pool đã được khởi tạo trước đó")
            return True
            
        self.pool_size = self._calculate_optimal_pool_size(total_tasks)
        
        # ĐẢM BẢO: Nếu chỉ có 1 task thì chỉ tạo 1 driver
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
                self.driver_semaphore.release()  # Tăng semaphore
                self.logger.log_debug(f"✅ Đã khởi tạo driver {successful_drivers}/{self.pool_size}")
            else:
                self.logger.log_error(f"❌ Không thể khởi tạo driver {i+1}")
        
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
        """Tính toán số driver tối ưu - Phiên bản cải tiến"""
        
        # QUAN TRỌNG: Nếu chỉ có 1 task, chỉ cần 1 driver
        if total_tasks == 1:
            return 1
        
        # QUAN TRỌNG: Nếu ít tasks, sử dụng ít drivers hơn
        if total_tasks <= 3:
            calculated_size = min(2, total_tasks)  # Tối đa 2 drivers cho ít tasks
        else:
            # Công thức gốc cho nhiều tasks
            calculated_size = math.ceil(total_tasks / self.config["performance"]["tasks_per_driver"])
        
        # Giới hạn trong khoảng min_pool_size đến max_pool_size
        optimal_size = max(self.config["driver"]["min_pool_size"], 
                          min(self.config["driver"]["max_pool_size"], calculated_size))
        
        # ĐẢM BẢO: Không vượt quá số tasks
        optimal_size = min(optimal_size, total_tasks)
        
        self.logger.log_info(f"📊 Tính toán pool size: {total_tasks} tasks → {optimal_size} drivers")
        return optimal_size
    
    def _create_driver_robust(self):
        """Tạo driver với exception handling toàn diện"""
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

            # Tối ưu hóa cho performance
            chrome_options.page_load_strategy = 'eager'  # Không chờ load hoàn toàn
            chrome_options.add_experimental_option("prefs", {
                "profile.managed_default_content_settings.images": 2,
            })
            
            driver = webdriver.Chrome(service=service, options=chrome_options)
            driver.set_page_load_timeout(self.config["driver"]["page_load_timeout"])
            driver.implicitly_wait(2)  # Giảm implicit wait
            driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            return driver
            
        except WebDriverException as e:
            self.logger.log_error(f"❌ Lỗi WebDriver: {e}")
            return None
        except Exception as e:
            self.logger.log_error(f"❌ Lỗi tạo driver: {e}")
            return None
    
    def get_driver(self, timeout=20):
        """Lấy driver từ pool sử dụng semaphore"""
        if not self.is_initialized:
            self.logger.log_error("❌ Driver pool chưa khởi tạo")
            return None
            
        # Sử dụng semaphore để chờ driver available
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
            # Nên không xảy ra vì semaphore đã được acquire
            self.driver_semaphore.release()  # Release lại nếu có lỗi
            self.logger.log_error("❌ Lỗi đồng bộ: semaphore nhưng queue rỗng")
            return None
    
    def return_driver(self, driver):
        """Trả driver về pool"""
        if driver is None:
            return
            
        if not self.is_initialized:
            try:
                driver.quit()
            except:
                pass
            return
        
        # Kiểm tra driver còn hoạt động không
        try:
            # Test nhanh driver状态
            driver.current_url
        except Exception as e:
            self.logger.log_warning(f"⚠️ Driver không hoạt động, đóng: {e}")
            try:
                driver.quit()
            except:
                pass
            
            # Tạo driver mới thay thế
            new_driver = self._create_driver_robust()
            if new_driver:
                self.available_drivers.put(new_driver)
                self.driver_semaphore.release()
                self.logger.log_info("🔄 Đã thay thế driver hỏng")
            return
        
        # Reset driver state
        try:
            driver.delete_all_cookies()
        except Exception as e:
            self.logger.log_debug(f"🔧 Lỗi reset driver: {e}")
        
        # Trả driver về pool
        with self.lock:
            if driver in self.in_use_drivers:
                self.in_use_drivers.remove(driver)
        
        self.available_drivers.put(driver)
        self.driver_semaphore.release()  # Thông báo có driver available
        
        available_count = self.available_drivers.qsize()
        self.logger.log_debug(f"📤 Trả driver, có {available_count} available")
    
    def cleanup(self):
        """Dọn dẹp pool"""
        if not self.is_initialized:
            return
            
        self.logger.log_info("🧹 Dọn dẹp driver pool...")
        
        # Đóng all available drivers
        closed_count = 0
        while not self.available_drivers.empty():
            try:
                driver = self.available_drivers.get_nowait()
                driver.quit()
                closed_count += 1
                # Giảm semaphore
                try:
                    self.driver_semaphore.acquire(blocking=False)
                except:
                    pass
            except:
                pass
        
        # Đóng all in-use drivers
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
        """Thông tin pool chi tiết"""
        with self.lock:
            return {
                "pool_size": self.pool_size,
                "available": self.available_drivers.qsize(),
                "in_use": len(self.in_use_drivers),
                "semaphore_value": self.driver_semaphore._value,
                "is_initialized": self.is_initialized
            }