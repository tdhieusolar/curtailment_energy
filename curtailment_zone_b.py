from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains # Cho Double-Click
import time

# --- HẰNG SỐ CẤU HÌNH ---
URL_WEBSITE = "http://10.10.10.129/monitor" # Thay thế bằng URL thực tế
USERNAME = "installer"
PASSWORD = "Mo_g010rP!"
CHROMIUM_DRIVER_PATH = "/usr/bin/chromedriver" # Đường dẫn Driver đã xác định trên Orange Pi

# CÁC BỘ CHỌN (SELECTORS)
SELECTOR_DROPDOWN_TOGGLE = "#login-dropdown-list > a.dropdown-toggle"
ID_USERNAME_FIELD = "login-username"
ID_PASSWORD_FIELD = "login-password"
ID_LOGIN_BUTTON = "login-buttons-password"
ID_CONNECT_GRID_LINK = "link-grid-disconnect" 
# -----------------------------

def initialize_driver():
    """Khởi tạo Chrome Driver với các tùy chọn cho môi trường headless/ARM."""
    print("1. Khởi tạo Chrome Driver...")
    try:
        service = Service(CHROMIUM_DRIVER_PATH)
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.maximize_window()
        driver.implicitly_wait(10) 
        print(f"-> Khởi tạo thành công từ: {CHROMIUM_DRIVER_PATH}")
        return driver
        
    except Exception as e:
        print(f"LỖI KHỞI TẠO DRIVER: {e}")
        return None

# -----------------------------

def login(driver, url, username, password):
    """Điều hướng đến trang web và thực hiện quy trình đăng nhập."""
    try:
        if not url.startswith(('http://', 'https://')):
            full_url = f"http://{url}"
        else:
            full_url = url
        driver.get(full_url)
        
        # Click vào biểu tượng đăng nhập để mở dropdown
        dropdown_toggle = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, SELECTOR_DROPDOWN_TOGGLE))
        )
        dropdown_toggle.click()
        
        # Nhập thông tin đăng nhập
        username_field = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, ID_USERNAME_FIELD))
        )
        username_field.send_keys(username)
        driver.find_element(By.ID, ID_PASSWORD_FIELD).send_keys(password)
        
        # Click nút Đăng nhập
        driver.find_element(By.ID, ID_LOGIN_BUTTON).click()
        return True
        
    except Exception as e:
        print(f"LỖI ĐĂNG NHẬP: {e}")
        return False

# -----------------------------

def turn_on_grid(driver):
    """
    Kiểm tra: Nếu trạng thái là 'Connect Grid', thực hiện click đúp để BẬT.
    Trả về: (bool, message)
    """
    try:
        link_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, ID_CONNECT_GRID_LINK))
        )
        text_before = link_element.text.strip()

        if text_before == "Connect Grid":
            # Cần BẬT
            actions = ActionChains(driver)
            actions.double_click(link_element).perform()
            time.sleep(3) # Chờ trạng thái cập nhật
            
            text_after = driver.find_element(By.ID, ID_CONNECT_GRID_LINK).text.strip()
            
            if text_after == "Disconnect Grid":
                return True, "TURN ON thành công"
            else:
                return False, f"LỖI: Trạng thái không chuyển từ '{text_before}' sang 'Disconnect Grid' (Hiện tại: {text_after})"
        
        elif text_before == "Disconnect Grid":
            # Đã BẬT, BỎ QUA nhưng được xem là thành công vì đã đạt mục tiêu
            return True, "BỎ QUA: Đã ở trạng thái 'Disconnect Grid' (đã BẬT)"
        
        else:
            return False, f"LỖI: Trạng thái văn bản không xác định: '{text_before}'"

    except Exception as e:
        return False, f"LỖI SELENIUM/TIMEOUT: {e}"
    
# -----------------------------

def turn_off_grid(driver):
    """
    Kiểm tra: Nếu trạng thái là 'Disconnect Grid', thực hiện click đúp để TẮT.
    Trả về: (bool, message)
    """
    try:
        link_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, ID_CONNECT_GRID_LINK))
        )
        text_before = link_element.text.strip()

        if text_before == "Disconnect Grid":
            # Cần TẮT
            actions = ActionChains(driver)
            actions.double_click(link_element).perform()
            time.sleep(3) # Chờ trạng thái cập nhật
            
            text_after = driver.find_element(By.ID, ID_CONNECT_GRID_LINK).text.strip()
            
            if text_after == "Connect Grid":
                return True, "TURN OFF thành công"
            else:
                return False, f"LỖI: Trạng thái không chuyển từ '{text_before}' sang 'Connect Grid' (Hiện tại: {text_after})"
        
        elif text_before == "Connect Grid":
            # Đã TẮT, BỎ QUA nhưng được xem là thành công vì đã đạt mục tiêu
            return True, "BỎ QUA: Đã ở trạng thái 'Connect Grid' (đã TẮT)"
        
        else:
            return False, f"LỖI: Trạng thái văn bản không xác định: '{text_before}'"

    except Exception as e:
        return False, f"LỖI SELENIUM/TIMEOUT: {e}"
    
# -----------------------------

def control_station_by_count(driver, station_name, inv_data, required_action, required_count, error_log):
    """
    Duyệt qua các INV trong một trạm và thực hiện hành động (ON/OFF) 
    cho đến khi đạt số lượng yêu cầu. Ghi log lỗi vào error_log.
    """
    action_function = None
    
    if required_action == "OFF":
        action_function = turn_off_grid
    elif required_action == "ON":
        action_function = turn_on_grid
    else:
        print(f"⚠️ Hành động không hợp lệ: {required_action} tại {station_name}. Bỏ qua trạm.")
        return

    sorted_invs = sorted(inv_data.items())
    count_performed = 0
    print(f"  -> Mục tiêu: {required_action} {required_count} INV.")

    for inv_name, inv_info in sorted_invs:
        if count_performed >= required_count:
            print(f"  -> ✅ Đã đạt đủ số lượng {required_count} INV. Dừng xử lý {station_name}.")
            break

        target_url = inv_info["url"]
        full_inv_name = f"{station_name}-{inv_name}"
        
        print(f"    > Xử lý INV: {full_inv_name}")

        # 1. Đăng nhập
        user = USERNAME 
        passwd = PASSWORD
        login_success = login(driver, target_url, user, passwd)

        if login_success:
            # 2. Thực hiện hành động và nhận kết quả
            is_success, message = action_function(driver)
            print(f"      -> Kết quả: {message}")
            
            if is_success:
                # Hành động thành công HOẶC BỊ BỎ QUA (nhưng trạng thái đã đúng)
                count_performed += 1
            else:
                # LỖI: Không chuyển trạng thái hoặc lỗi khác
                error_log.append(f"{full_inv_name} (Hành động: {required_action}): {message}")
                
        else:
            login_error_msg = f"LỖI ĐĂNG NHẬP"
            print(f"   ❌ {login_error_msg}. Bỏ qua INV này.")
            error_log.append(f"{full_inv_name} (Hành động: {required_action}): {login_error_msg}")

    print(f"  --- Kết thúc xử lý {station_name}: {count_performed}/{required_count} INV đã được {required_action}.")

# -----------------------------

# -----------------------------

def perform_double_click_and_read(driver):
    """Thực hiện click đúp vào thẻ <a> và đọc giá trị trước/sau."""
    print("3. Thực hiện Double-Click và đọc giá trị...")
    try:
        # Chờ thẻ <a> xuất hiện và có thể click
        connect_grid_link = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, ID_CONNECT_GRID_LINK))
        )
        
        # LẤY GIÁ TRỊ TRƯỚC KHI CLICK ĐÚP
        text_before_click = connect_grid_link.text.strip()
        print(f"   - TRƯỚC: '{text_before_click}'")
        
        # THỰC HIỆN DOUBLE-CLICK
        actions = ActionChains(driver)
        actions.double_click(connect_grid_link).perform()
        print("   - Đã Double-Click.")
        
        time.sleep(3) # Chờ trạng thái trang web cập nhật

        # LẤY GIÁ TRỊ SAU KHI CLICK ĐÚP
        text_after_click = driver.find_element(By.ID, ID_CONNECT_GRID_LINK).text.strip()
        print(f"   - SAU:  '{text_after_click}'")
        
        if text_before_click != text_after_click:
            print("-> ✅ Kết quả: Văn bản đã thay đổi.")
        else:
            print("-> ⚠️ Kết quả: Văn bản không thay đổi.")
            
    except Exception as e:
        print(f"LỖI DOUBLE-CLICK: {e}")

# -----------------------------

def main():
    start_time = time.time()
    print("Bắt đầu chương trình...")
    # ... (Khởi tạo driver giữ nguyên) ...
    driver = initialize_driver()
    if driver is None:
        end_time = time.time()
        total_time = end_time - start_time
        print(f"\n==============================================")
        print(f"❌ THẤT BẠI: Khởi tạo Driver. Tổng thời gian: {total_time:.2f} giây.")
        print("==============================================")
        return

    # KHỞI TẠO DANH SÁCH LOG LỖI MỚI
    error_log = [] 

    print("\nBắt đầu xử lý điều khiển theo số lượng INV...")

    try:
        # Vòng lặp 1 & 2: Duyệt qua Zone và Station
        for zone_name, stations in SYSTEM_URLS.items():
            for station_name, inverters in stations.items():
                
                if station_name in CONTROL_REQUESTS:
                    request = CONTROL_REQUESTS[station_name]
                    required_action = request["action"]
                    required_count = request["count"]
                    
                    print(f"\n==============================================")
                    print(f"YÊU CẦU: {station_name} - {required_action} {required_count} INV")
                    print(f"==============================================")
                    
                    # CHUYỂN DANH SÁCH LỖI VÀO HÀM XỬ LÝ
                    control_station_by_count(
                        driver, 
                        station_name, 
                        inverters, 
                        required_action, 
                        required_count,
                        error_log
                    )
                # else: ... (phần bỏ qua giữ nguyên)
                    
    except Exception as e:
        print(f"\nĐã xảy ra lỗi không lường trước trong main loop: {e}")
        driver.save_screenshot("main_error_screenshot.png")

    finally:
        if driver:
            driver.quit()

        end_time = time.time()
        total_time = end_time - start_time
        
        # IN LOG LỖI CUỐI CÙNG
        print("\n\n==============================================")
        print("BÁO CÁO KẾT THÚC CHƯƠNG TRÌNH")
        print("==============================================")
        
        if error_log:
            print(f"❌ CÓ {len(error_log)} LỖI ĐIỀU KHIỂN/ĐĂNG NHẬP CẦN XEM XÉT:")
            for error in error_log:
                print(f"   - {error}")
        else:
            print("✅ KHÔNG CÓ LỖI ĐIỀU KHIỂN/ĐĂNG NHẬP NÀO ĐƯỢC GHI NHẬN.")
        
        minutes = int(total_time // 60)
        seconds = total_time % 60
        
        print(f"\n⏰ TỔNG THỜI GIAN CHẠY: {minutes} phút {seconds:.2f} giây.")
        print("Hoàn thành và đóng trình duyệt.")

if __name__ == "__main__":
    CONTROL_REQUESTS = {
        "B2": {"action": "OFF", "count": 10},
        "B3R1": {"action": "OFF", "count": 9},
        "B4R2": {"action": "OFF", "count": 10},
        "B5R2": {"action": "OFF", "count": 10},
        "B6R2": {"action": "OFF", "count": 10},
        "B7": {"action": "OFF", "count": 10},
        "B8": {"action": "OFF", "count": 5},
        "B11": {"action": "OFF", "count": 10},
        "B13-14": {"action": "OFF", "count": 10},
    }   
    SYSTEM_URLS = {
        "Zone B": {
            "B2": {
                "INV-01": { "url": "10.10.10.101", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.102", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.103", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.104", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.105", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.106", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.107", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.108", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.109", "info": "Inverter số 9"},
                "INV-10": { "url": "10.10.10.110", "info": "Inverter số 10"},
            },
            "B3R1": {
                "INV-01": { "url": "10.10.10.121", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.122", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.123", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.124", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.125", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.126", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.127", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.128", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.129", "info": "Inverter số 9"},
            },
            "B3R2": {
                "INV-01": { "url": "10.10.10.111", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.112", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.113", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.114", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.115", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.116", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.117", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.118", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.119", "info": "Inverter số 9"},
            },
            "B4R1": {
                "INV-01": { "url": "10.10.10.141", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.142", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.143", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.144", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.145", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.146", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.147", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.148", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.149", "info": "Inverter số 9"},
                "INV-10": { "url": "10.10.10.150", "info": "Inverter số 10"},
            },        
            "B4R2": {
                "INV-01": { "url": "10.10.10.131", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.132", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.133", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.134", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.135", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.136", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.137", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.138", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.139", "info": "Inverter số 9"},
                "INV-10": { "url": "10.10.10.140", "info": "Inverter số 10"},
            },        
            "B5R1": {
                "INV-01": { "url": "10.10.10.161", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.162", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.163", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.164", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.165", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.166", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.167", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.168", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.169", "info": "Inverter số 9"},
                "INV-10": { "url": "10.10.10.170", "info": "Inverter số 10"},
            },
            "B5R2": {
                "INV-01": { "url": "10.10.10.151", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.152", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.153", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.154", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.155", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.156", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.157", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.158", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.159", "info": "Inverter số 9"},
                "INV-10": { "url": "10.10.10.160", "info": "Inverter số 10"},
            },
            "B6R1": {
                "INV-01": { "url": "10.10.10.181", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.182", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.183", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.184", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.185", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.186", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.187", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.188", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.189", "info": "Inverter số 9"},
                "INV-10": { "url": "10.10.10.190", "info": "Inverter số 10"},
            },
            "B6R2": {
                "INV-01": { "url": "10.10.10.171", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.172", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.173", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.174", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.175", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.176", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.177", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.178", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.179", "info": "Inverter số 9"},
                "INV-10": { "url": "10.10.10.180", "info": "Inverter số 10"},
            },
            "B7": {
                "INV-01": { "url": "10.10.10.191", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.192", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.193", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.194", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.195", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.196", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.197", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.198", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.199", "info": "Inverter số 9"},
                "INV-10": { "url": "10.10.10.200", "info": "Inverter số 10"},
            },
            "B8": {
                "INV-01": { "url": "10.10.10.201", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.202", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.203", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.204", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.205", "info": "Inverter số 5"},
            },
            "B11": {
                "INV-01": { "url": "10.10.10.211", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.212", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.213", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.214", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.215", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.216", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.217", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.218", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.219", "info": "Inverter số 9"},
                "INV-10": { "url": "10.10.10.220", "info": "Inverter số 10"},
            },
            "B12": {
                "INV-01": { "url": "10.10.10.241", "info": "Inverter số 1"},
                "INV-02": { "url": "10.10.10.242", "info": "Inverter số 2"},
                "INV-03": { "url": "10.10.10.243", "info": "Inverter số 3"},
                "INV-04": { "url": "10.10.10.244", "info": "Inverter số 4"},
                "INV-05": { "url": "10.10.10.245", "info": "Inverter số 5"},
                "INV-06": { "url": "10.10.10.246", "info": "Inverter số 6"},
                "INV-07": { "url": "10.10.10.247", "info": "Inverter số 7"},
                "INV-08": { "url": "10.10.10.248", "info": "Inverter số 8"},
                "INV-09": { "url": "10.10.10.249", "info": "Inverter số 9"},
                "INV-10": { "url": "10.10.10.250", "info": "Inverter số 10"},
            },  
            "B13-14": {
                "INV-01": { "url": "10.10.10.221", "info": "B13 Inverter số 1"},
                "INV-02": { "url": "10.10.10.222", "info": "B13 Inverter số 2"},
                "INV-03": { "url": "10.10.10.223", "info": "B13 Inverter số 3"},
                "INV-04": { "url": "10.10.10.224", "info": "B13 Inverter số 4"},
                "INV-05": { "url": "10.10.10.225", "info": "B13 Inverter số 5"},
                "INV-06": { "url": "10.10.10.226", "info": "B13 Inverter số 6"},
                "INV-07": { "url": "10.10.10.231", "info": "B14 Inverter số 1"},
                "INV-08": { "url": "10.10.10.232", "info": "B14 Inverter số 2"},
                "INV-09": { "url": "10.10.10.233", "info": "B14 Inverter số 3"},
                "INV-10": { "url": "10.10.10.234", "info": "B14 Inverter số 4"},
            },
        }
    }
    main()