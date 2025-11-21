"""
Lớp điều khiển inverter với driver từ pool
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException

from core.logger import InverterControlLogger
from config.settings import CONFIG
from config.selectors import SELECTORS

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