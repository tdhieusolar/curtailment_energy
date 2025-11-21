# core/driver_pool.py
"""
Pool quản lý driver động - Phiên bản 0.5.3 - Multi-Browser Support
Hỗ trợ: Chrome, Edge, Firefox với auto-detection và fallback
"""

import math
import queue
import threading
import os
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.common.exceptions import WebDriverException, SessionNotCreatedException
from core.logger import InverterControlLogger

class DynamicDriverPool:
    """Pool quản lý driver động với hỗ trợ đa trình duyệt và auto-recovery"""
    
    def __init__(self, config):
        self.config = config
        self.available_drivers = queue.Queue()
        self.in_use_drivers = set()
        self.lock = threading.Lock()
        self.logger = InverterControlLogger(config)
        self.is_initialized = False
        self.pool_size = 0
        self.driver_semaphore = threading.Semaphore(0)
        self.driver_creation_attempts = 0
        self.max_driver_creation_attempts = 3
        
        # Cấu hình trình duyệt
        self.browser_type = config["driver"].get("browser_type", "auto")
        self.browser_path = config["driver"].get("browser_path", "")
        self.driver_path = config["driver"].get("path", "")
        
        # WebDriver manager flags
        self.wdm_available = self._check_webdriver_manager()
        
        self.logger.log_info(f"🚀 Khởi tạo Driver Pool - Browser: {self.browser_type}")
    
    def _check_webdriver_manager(self):
        """Kiểm tra webdriver-manager availability"""
        try:
            import webdriver_manager
            return True
        except ImportError:
            self.logger.log_warning("⚠️ webdriver-manager không khả dụng, sử dụng driver manual")
            return False
    
    def detect_best_browser(self):
        """Tự động phát hiện trình duyệt tốt nhất"""
        browsers_to_check = []
        
        if sys.platform.startswith("win"):
            # Windows - Ưu tiên Edge, sau đó Chrome
            browsers_to_check = [
                ("edge", [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
                ]),
                ("chrome", [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ])
            ]
        else:
            # Linux/Mac - Ưu tiên Chrome/Chromium
            browsers_to_check = [
                ("chrome", [
                    "/usr/bin/google-chrome",
                    "/usr/bin/google-chrome-stable",
                    "/usr/bin/chromium-browser",
                    "/usr/bin/chromium"
                ]),
                ("edge", [
                    "/usr/bin/microsoft-edge",
                    "/usr/bin/microsoft-edge-stable"
                ])
            ]
        
        for browser_name, paths in browsers_to_check:
            for path in paths:
                if os.path.exists(path):
                    self.logger.log_info(f"✅ Phát hiện {browser_name.upper()} tại: {path}")
                    return browser_name, path
        
        self.logger.log_warning("⚠️ Không phát hiện trình duyệt nào, sử dụng auto-mode")
        return "auto", ""
    
    def get_driver_path(self, browser_type):
        """Lấy đường dẫn driver cho trình duyệt cụ thể"""
        # Nếu đã cấu hình đường dẫn và tồn tại
        if self.driver_path and os.path.exists(self.driver_path):
            return self.driver_path
        
        # Tự động cài đặt driver nếu webdriver-manager available
        if self.wdm_available:
            try:
                if browser_type == "chrome":
                    from webdriver_manager.chrome import ChromeDriverManager
                    driver_path = ChromeDriverManager().install()
                    self.logger.log_info(f"✅ Đã cài đặt ChromeDriver: {driver_path}")
                    return driver_path
                elif browser_type == "edge":
                    from webdriver_manager.microsoft import EdgeDriverManager
                    driver_path = EdgeDriverManager().install()
                    self.logger.log_info(f"✅ Đã cài đặt EdgeDriver: {driver_path}")
                    return driver_path
                elif browser_type == "firefox":
                    from webdriver_manager.firefox import GeckoDriverManager
                    driver_path = GeckoDriverManager().install()
                    self.logger.log_info(f"✅ Đã cài đặt GeckoDriver: {driver_path}")
                    return driver_path
            except Exception as e:
                self.logger.log_error(f"❌ Lỗi cài đặt driver tự động: {e}")
        
        # Fallback: sử dụng system driver
        if sys.platform.startswith("win"):
            if browser_type == "chrome":
                return "chromedriver.exe"
            elif browser_type == "edge":
                return "msedgedriver.exe"
            else:
                return "geckodriver.exe"
        else:
            if browser_type == "chrome":
                return "/usr/bin/chromedriver"
            elif browser_type == "edge":
                return "/usr/bin/msedgedriver"
            else:
                return "/usr/bin/geckodriver"
    
    def _create_driver_robust(self):
        """Tạo driver với robust error handling và retry mechanism"""
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                # Xác định trình duyệt để sử dụng
                if self.browser_type == "auto":
                    browser_type, browser_path = self.detect_best_browser()
                else:
                    browser_type = self.browser_type
                    browser_path = self.browser_path
                
                self.logger.log_debug(f"🔄 Tạo driver {browser_type.upper()} (lần {attempt + 1})")
                
                driver_path = self.get_driver_path(browser_type)
                
                if browser_type == "chrome":
                    driver = self._create_chrome_driver(driver_path, browser_path)
                elif browser_type == "edge":
                    driver = self._create_edge_driver(driver_path, browser_path)
                elif browser_type == "firefox":
                    driver = self._create_firefox_driver(driver_path, browser_path)
                else:
                    self.logger.log_error(f"❌ Trình duyệt không được hỗ trợ: {browser_type}")
                    return None
                
                if driver:
                    self.logger.log_debug(f"✅ Tạo driver {browser_type.upper()} thành công")
                    return driver
                
            except SessionNotCreatedException as e:
                self.logger.log_error(f"❌ Lỗi phiên driver (attempt {attempt + 1}): {e}")
                if "This version of ChromeDriver only supports" in str(e):
                    self.logger.log_warning("⚠️ Phiên bản ChromeDriver không tương thích, thử cài đặt lại...")
                    # Xóa cache driver để tải lại phiên bản mới
                    self._clean_driver_cache()
            except WebDriverException as e:
                self.logger.log_error(f"❌ Lỗi WebDriver (attempt {attempt + 1}): {e}")
            except Exception as e:
                self.logger.log_error(f"❌ Lỗi không xác định (attempt {attempt + 1}): {e}")
            
            # Chờ trước khi retry
            if attempt < max_retries:
                wait_time = 2 ** attempt  # Exponential backoff
                self.logger.log_debug(f"⏳ Chờ {wait_time}s trước khi retry...")
                time.sleep(wait_time)
        
        self.logger.log_error("❌ Không thể tạo driver sau nhiều lần thử")
        return None
    
    def _clean_driver_cache(self):
        """Dọn dẹp cache driver cũ"""
        try:
            if self.wdm_available:
                from webdriver_manager.core.driver_cache import DriverCacheManager
                cache_manager = DriverCacheManager()
                cache_manager.clean_driver_cache()
                self.logger.log_info("🧹 Đã dọn dẹp driver cache")
        except Exception as e:
            self.logger.log_debug(f"⚠️ Không thể dọn dẹp cache: {e}")
    
    def _create_chrome_driver(self, driver_path, browser_path):
        """Tạo Chrome driver"""
        service = ChromeService(driver_path)
        options = ChromeOptions()
        
        # Chỉ định Chrome binary nếu có
        if browser_path and os.path.exists(browser_path):
            options.binary_location = browser_path
            self.logger.log_debug(f"🔧 Sử dụng Chrome binary: {browser_path}")
        
        options = self._add_common_options(options)
        
        # Chrome-specific options
        options.add_argument("--disable-extensions")
        options.add_argument("--disable-plugins")
        options.add_argument("--disable-popup-blocking")
        
        driver = webdriver.Chrome(service=service, options=options)
        self._setup_driver_common(driver)
        return driver
    
    def _create_edge_driver(self, driver_path, browser_path):
        """Tạo Edge driver"""
        service = EdgeService(driver_path)
        options = EdgeOptions()
        
        # Chỉ định Edge binary nếu có
        if browser_path and os.path.exists(browser_path):
            options.binary_location = browser_path
            self.logger.log_debug(f"🔧 Sử dụng Edge binary: {browser_path}")
        
        options = self._add_common_options(options)
        
        # Edge-specific options
        options.add_argument("--disable-extensions")
        options.add_argument("--inprivate")
        
        driver = webdriver.Edge(service=service, options=options)
        self._setup_driver_common(driver)
        return driver
    
    def _create_firefox_driver(self, driver_path, browser_path):
        """Tạo Firefox driver"""
        service = FirefoxService(driver_path)
        options = FirefoxOptions()
        
        # Chỉ định Firefox binary nếu có
        if browser_path and os.path.exists(browser_path):
            options.binary_location = browser_path
            self.logger.log_debug(f"🔧 Sử dụng Firefox binary: {browser_path}")
        
        # Firefox-specific options
        if self.config["driver"]["headless"]:
            options.add_argument("--headless")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--width=1920")
        options.add_argument("--height=1080")
        
        # Firefox preferences
        options.set_preference("dom.webdriver.enabled", False)
        options.set_preference("useAutomationExtension", False)
        options.set_preference("pdfjs.disabled", True)
        options.set_preference("browser.download.folderList", 2)
        
        driver = webdriver.Firefox(service=service, options=options)
        self._setup_driver_common(driver)
        return driver
    
    def _add_common_options(self, options):
        """Thêm options chung cho tất cả trình duyệt"""
        if self.config["driver"]["headless"]:
            options.add_argument("--headless=new")
        
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-features=VizDisplayCompositor")
        options.add_argument("--disable-background-timer-throttling")
        options.add_argument("--disable-backgrounding-occluded-windows")
        options.add_argument("--disable-renderer-backgrounding")
        
        options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
        options.add_experimental_option('useAutomationExtension', False)
        options.page_load_strategy = 'eager'
        
        options.add_experimental_option("prefs", {
            "profile.managed_default_content_settings.images": 2,
            "profile.default_content_setting_values.notifications": 2,
            "profile.password_manager_enabled": False,
            "credentials_enable_service": False,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        })
        
        return options
    
    def _setup_driver_common(self, driver):
        """Thiết lập chung cho driver"""
        driver.set_page_load_timeout(self.config["driver"]["page_load_timeout"])
        driver.implicitly_wait(self.config["driver"]["element_timeout"])
        
        # Ẩn automation
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        driver.execute_cdp_cmd('Network.setUserAgentOverride', {
            "userAgent": driver.execute_script("return navigator.userAgent").replace("Headless", "")
        })
    
    def initialize_pool(self, total_tasks):
        """Khởi tạo pool driver với tính toán kích thước tối ưu"""
        if self.is_initialized:
            self.logger.log_info("✅ Driver pool đã được khởi tạo trước đó")
            return True
            
        self.pool_size = self._calculate_optimal_pool_size(total_tasks)
        
        self.logger.log_info(f"🔄 Khởi tạo {self.pool_size} drivers cho {total_tasks} tasks")
        
        successful_drivers = 0
        failed_drivers = 0
        
        for i in range(self.pool_size):
            driver = self._create_driver_robust()
            if driver:
                self.available_drivers.put(driver)
                successful_drivers += 1
                self.driver_semaphore.release()
                self.logger.log_debug(f"✅ Đã khởi tạo driver {successful_drivers}/{self.pool_size}")
            else:
                failed_drivers += 1
                self.logger.log_error(f"❌ Không thể khởi tạo driver {i+1}")
        
        if successful_drivers == 0:
            self.logger.log_error("❌ Không thể khởi tạo driver nào!")
            return False
            
        self.is_initialized = True
        
        pool_info = self.get_pool_info()
        self.logger.log_info(f"✅ Đã khởi tạo {successful_drivers}/{self.pool_size} drivers thành công")
        self.logger.log_info(f"📊 Pool info: {pool_info['available']} available, {pool_info['in_use']} in use")
        
        return True
    
    def _calculate_optimal_pool_size(self, total_tasks):
        """Tính toán số driver tối ưu"""
        if total_tasks == 1:
            return 1
        
        if total_tasks <= 3:
            calculated_size = min(2, total_tasks)
        else:
            calculated_size = math.ceil(total_tasks / self.config["performance"]["tasks_per_driver"])
        
        optimal_size = max(
            self.config["driver"]["min_pool_size"], 
            min(self.config["driver"]["max_pool_size"], calculated_size)
        )
        
        optimal_size = min(optimal_size, total_tasks)
        
        self.logger.log_info(f"📊 Tính toán pool size: {total_tasks} tasks → {optimal_size} drivers")
        return optimal_size
    
    def get_driver(self, timeout=20):
        """Lấy driver từ pool với timeout"""
        if not self.is_initialized:
            self.logger.log_error("❌ Driver pool chưa khởi tạo")
            return None
            
        start_time = time.time()
        
        # Sử dụng semaphore để chờ driver available
        if not self.driver_semaphore.acquire(timeout=timeout):
            self.logger.log_warning(f"⚠️ Timeout khi chờ driver sau {timeout}s")
            return None
        
        try:
            driver = self.available_drivers.get_nowait()
            with self.lock:
                self.in_use_drivers.add(driver)
            
            available_count = self.available_drivers.qsize()
            wait_time = time.time() - start_time
            self.logger.log_debug(f"📥 Lấy driver thành công (chờ {wait_time:.1f}s), còn {available_count} available")
            return driver
            
        except queue.Empty:
            self.driver_semaphore.release()
            self.logger.log_error("❌ Lỗi đồng bộ: semaphore nhưng queue rỗng")
            return None
    
    def return_driver(self, driver):
        """Trả driver về pool với health check"""
        if driver is None:
            return
            
        if not self.is_initialized:
            try:
                driver.quit()
            except:
                pass
            return
        
        # Kiểm tra driver health
        driver_healthy = self._check_driver_health(driver)
        
        if not driver_healthy:
            self.logger.log_warning("⚠️ Driver không healthy, đóng và thay thế...")
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
            # Quay về trang trống để giải phóng bộ nhớ
            driver.get("about:blank")
        except Exception as e:
            self.logger.log_debug(f"🔧 Lỗi reset driver: {e}")
        
        # Trả driver về pool
        with self.lock:
            if driver in self.in_use_drivers:
                self.in_use_drivers.remove(driver)
        
        self.available_drivers.put(driver)
        self.driver_semaphore.release()
        
        available_count = self.available_drivers.qsize()
        self.logger.log_debug(f"📤 Trả driver, có {available_count} available")
    
    def _check_driver_health(self, driver):
        """Kiểm tra driver có còn hoạt động không"""
        try:
            # Test cơ bản
            current_url = driver.current_url
            driver.title  # Test thêm
            return True
        except Exception as e:
            self.logger.log_debug(f"🔧 Driver health check failed: {e}")
            return False
    
    def cleanup(self):
        """Dọn dẹp pool hoàn toàn"""
        if not self.is_initialized:
            return
            
        self.logger.log_info("🧹 Dọn dẹp driver pool...")
        
        closed_count = 0
        
        # Đóng all available drivers
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
            except Exception as e:
                self.logger.log_debug(f"⚠️ Lỗi đóng available driver: {e}")
        
        # Đóng all in-use drivers
        with self.lock:
            for driver in self.in_use_drivers.copy():
                try:
                    driver.quit()
                    closed_count += 1
                except Exception as e:
                    self.logger.log_debug(f"⚠️ Lỗi đóng in-use driver: {e}")
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
                "is_initialized": self.is_initialized,
                "browser_type": self.browser_type
            }
    
    def emergency_recovery(self):
        """Khôi phục khẩn cấp khi pool gặp vấn đề"""
        self.logger.log_warning("🚨 Thực hiện emergency recovery...")
        
        self.cleanup()
        time.sleep(2)
        
        # Thử khởi tạo lại với size nhỏ
        self.pool_size = self.config["driver"]["min_pool_size"]
        successful_drivers = 0
        
        for i in range(self.pool_size):
            driver = self._create_driver_robust()
            if driver:
                self.available_drivers.put(driver)
                successful_drivers += 1
                self.driver_semaphore.release()
        
        if successful_drivers > 0:
            self.is_initialized = True
            self.logger.log_info(f"✅ Emergency recovery thành công: {successful_drivers} drivers")
            return True
        else:
            self.logger.log_error("❌ Emergency recovery thất bại")
            return False