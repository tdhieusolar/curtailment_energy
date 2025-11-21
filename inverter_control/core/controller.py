# core/controller.py
"""
Lớp điều khiển inverter với driver từ pool - Phiên bản 0.5.2 tối ưu
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException

from core.logger import InverterControlLogger
from config.selectors import SELECTORS

class InverterController:
    """Lớp điều khiển inverter với driver từ pool - Phiên bản tối ưu"""
    
    def __init__(self, driver, config):
        self.driver = driver
        self.config = config
        self.logger = InverterControlLogger(config)
    
    def wait_for_element(self, by, value, timeout=None):
        """Chờ element xuất hiện - Phiên bản tối ưu"""
        try:
            wait_timeout = timeout or self.config["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.presence_of_element_located((by, value)))
        except TimeoutException:
            return None
    
    def wait_for_element_clickable(self, by, value, timeout=None):
        """Chờ element có thể click - Phiên bản tối ưu"""
        try:
            wait_timeout = timeout or self.config["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.element_to_be_clickable((by, value)))
        except TimeoutException:
            return None
    
    def wait_for_text_present(self, by, value, text, timeout=None):
        """Chờ text xuất hiện - Phiên bản tối ưu"""
        try:
            wait_timeout = timeout or self.config["driver"]["element_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(EC.text_to_be_present_in_element((by, value), text))
        except TimeoutException:
            return False
    
    def wait_for_page_loaded(self, timeout=None):
        """Chờ trang web load hoàn tất - Phiên bản tối ưu"""
        try:
            wait_timeout = timeout or self.config["driver"]["page_load_timeout"]
            wait = WebDriverWait(self.driver, wait_timeout)
            return wait.until(lambda driver: driver.execute_script("return document.readyState") == "complete")
        except TimeoutException:
            return False
    
    def fast_login(self, url, username=None, password=None):
        """Đăng nhập nhanh với driver được tái sử dụng - Phiên bản tối ưu"""
        username = username or self.config["credentials"]["username"]
        password = password or self.config["credentials"]["password"]
        
        try:
            if not url.startswith(('http://', 'https://')):
                url = f"http://{url}"
            
            self.driver.get(url)
            
            # Chờ trang load với timeout ngắn hơn
            if not self.wait_for_page_loaded(timeout=10):
                self.logger.log_debug("Trang load chậm, tiếp tục thử...")
            
            # Kiểm tra đã đăng nhập chưa - nhanh hơn
            if self.wait_for_text_present(By.TAG_NAME, "body", "installer", timeout=1):
                self.logger.log_debug("Đã đăng nhập sẵn")
                return True
            
            # Đăng nhập với timeout ngắn hơn
            dropdown = self.wait_for_element_clickable(
                By.CSS_SELECTOR, SELECTORS["login"]["dropdown_toggle"], timeout=2
            )
            if dropdown:
                dropdown.click()
                # Chờ dropdown mở với timeout ngắn
                self.wait_for_element(By.ID, SELECTORS["login"]["username_field"], timeout=1)
            
            # Nhập username
            username_field = self.wait_for_element(By.ID, SELECTORS["login"]["username_field"], timeout=2)
            if not username_field:
                self.logger.log_debug("Không tìm thấy field username, có thể đã đăng nhập")
                return True
            
            username_field.clear()
            username_field.send_keys(username)
            
            # Nhập password
            password_field = self.wait_for_element(By.ID, SELECTORS["login"]["password_field"], timeout=2)
            if not password_field:
                self.logger.log_debug("Không tìm thấy field password")
                return False
            
            password_field.clear()
            password_field.send_keys(password)
            
            # Click đăng nhập
            login_btn = self.wait_for_element_clickable(By.ID, SELECTORS["login"]["login_button"], timeout=2)
            if not login_btn:
                self.logger.log_debug("Không tìm thấy nút đăng nhập")
                return False
            
            login_btn.click()
            
            # Chờ đăng nhập thành công với timeout ngắn hơn
            if self.wait_for_text_present(By.TAG_NAME, "body", "installer", timeout=5):
                self.logger.log_debug("Đăng nhập thành công")
                return True
            
            # Thử cách khác để kiểm tra đăng nhập
            if self.wait_for_element(By.CSS_SELECTOR, SELECTORS["monitoring"]["navbar"], timeout=2):
                self.logger.log_debug("Đăng nhập thành công (qua navbar)")
                return True
            
            self.logger.log_debug("Không xác định được trạng thái đăng nhập")
            return False
                
        except Exception as e:
            self.logger.log_debug(f"Login thất bại: {e}")
            return False
    
    def get_grid_status(self):
        """Lấy trạng thái grid từ text và hình ảnh - Phiên bản tối ưu"""
        try:
            # Tìm element grid control với timeout ngắn hơn
            link_element = self.wait_for_element(
                By.ID, SELECTORS["grid_control"]["connect_link"], timeout=3
            )
            
            if not link_element:
                self.logger.log_debug("Không tìm thấy element grid control")
                return None
            
            # Lấy text trạng thái từ span
            status_text_element = link_element.find_element(By.CSS_SELECTOR, SELECTORS["grid_control"]["status_text"])
            status_text = status_text_element.text.strip() if status_text_element else ""
            
            # Lấy thông tin từ hình ảnh
            img_element = link_element.find_element(By.CSS_SELECTOR, SELECTORS["grid_control"]["status_image"])
            img_src = img_element.get_attribute("src") if img_element else ""
            
            self.logger.log_debug(f"Trạng thái grid - Text: '{status_text}', Image: '{img_src}'")
            
            # Xác định trạng thái dựa trên text và hình ảnh
            if "Disconnect Grid" in status_text:
                return "Disconnect Grid"
            elif "Connect Grid" in status_text:
                return "Connect Grid"
            else:
                # Fallback: dựa vào hình ảnh
                if "flash_off" in img_src:
                    return "Disconnect Grid"
                elif "flash_on" in img_src:
                    return "Connect Grid"
                else:
                    return status_text  # Trả về text gốc nếu không xác định được
                    
        except Exception as e:
            self.logger.log_debug(f"Lỗi khi lấy trạng thái grid: {e}")
            return None
    
    def perform_grid_action(self, target_action):
        """Thực hiện hành động grid với double click - Phiên bản tối ưu"""
        current_status = self.get_grid_status()
        
        if not current_status:
            return False, "Không thể xác định trạng thái hiện tại"
        
        self.logger.log_debug(f"Trạng thái hiện tại: '{current_status}', Hành động mong muốn: '{target_action}'")
        
        # Xác định trạng thái mong muốn sau khi thực hiện
        if target_action == "ON":
            expected_status_after = "Disconnect Grid"  # Bật lên -> Disconnect Grid
            should_perform_action = current_status == "Connect Grid"
        elif target_action == "OFF":
            expected_status_after = "Connect Grid"  # Tắt đi -> Connect Grid
            should_perform_action = current_status == "Disconnect Grid"
        else:
            return False, f"Hành động không hợp lệ: {target_action}"
        
        # Kiểm tra trạng thái hiện tại
        if not should_perform_action:
            status_message = f"BỎ QUA: Đã ở trạng thái mong muốn (Hiện tại: {current_status})"
            self.logger.log_debug(status_message)
            return True, status_message
        
        try:
            # Tìm element grid control
            link_element = self.wait_for_element_clickable(
                By.ID, SELECTORS["grid_control"]["connect_link"], timeout=3
            )
            if not link_element:
                return False, "Không tìm thấy element điều khiển grid"
            
            self.logger.log_debug(f"Thực hiện {target_action} grid...")
            
            # Scroll element vào view
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", link_element)
            
            # Thực hiện double click
            actions = ActionChains(self.driver)
            actions.move_to_element(link_element).double_click().perform()
            
            self.logger.log_debug("Đã thực hiện double click, chờ trạng thái thay đổi...")
            
            # Chờ trạng thái thay đổi với timeout ngắn hơn
            status_changed = False
            for i in range(6):  # Chờ tối đa 6 giây (giảm từ 10)
                import time
                time.sleep(0.5)  # Giảm thời gian chờ giữa các lần kiểm tra
                new_status = self.get_grid_status()
                self.logger.log_debug(f"Lần {i+1}: Trạng thái mới: '{new_status}'")
                
                if new_status == expected_status_after:
                    status_changed = True
                    break
                elif new_status != current_status:
                    # Trạng thái đã thay đổi nhưng không như mong đợi
                    self.logger.log_debug(f"Trạng thái đã thay đổi từ '{current_status}' sang '{new_status}'")
                    break
            
            if status_changed:
                final_status = self.get_grid_status()
                return True, f"THÀNH CÔNG: Chuyển từ '{current_status}' sang '{final_status}'"
            else:
                final_status = self.get_grid_status()
                return False, f"LỖI: Trạng thái không thay đổi như mong đợi (Hiện tại: {final_status}, Mong đợi: {expected_status_after})"
                
        except StaleElementReferenceException:
            # Element bị stale, thử lại
            try:
                self.logger.log_debug("Element bị stale, thử lại...")
                link_element = self.wait_for_element_clickable(
                    By.ID, SELECTORS["grid_control"]["connect_link"], timeout=2
                )
                if link_element:
                    actions = ActionChains(self.driver)
                    actions.move_to_element(link_element).double_click().perform()
                    
                    # Kiểm tra kết quả
                    import time
                    time.sleep(2)
                    new_status = self.get_grid_status()
                    if new_status == expected_status_after:
                        return True, f"THÀNH CÔNG: Chuyển từ '{current_status}' sang '{new_status}'"
                    else:
                        return False, f"LỖI: Trạng thái không thay đổi (Hiện tại: {new_status})"
                else:
                    return False, "LỖI: Không thể tìm thấy element sau khi retry"
            except Exception as retry_e:
                return False, f"LỖI THỰC HIỆN (retry): {retry_e}"
                
        except Exception as e:
            return False, f"LỖI THỰC HIỆN: {str(e)}"