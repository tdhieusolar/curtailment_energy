from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains # Cho Double-Click
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import re

# --- HẰNG SỐ CẤU HÌNH ---
USERNAME = "installer"
PASSWORD = "Mo_g010rP!"
CHROMIUM_DRIVER_PATH = "/usr/bin/chromedriver" # Đường dẫn Driver đã xác định trên Orange Pi
MAX_WORKERS = 4

# CÁC BỘ CHỌN (SELECTORS)
# ON-OFF
SELECTOR_DROPDOWN_TOGGLE = "#login-dropdown-list > a.dropdown-toggle"
ID_USERNAME_FIELD = "login-username"
ID_PASSWORD_FIELD = "login-password"
ID_LOGIN_BUTTON = "login-buttons-password"
ID_CONNECT_GRID_LINK = "link-grid-disconnect" 
# LOGGER
SELECTOR_STATUS_LOG_BUTTON = "button.js-display-web-log" 
ID_LOG_DIALOG = "log-dlg"
SELECTOR_LOG_CONTENT = "div.k-log-view"
SELECTOR_CLOSE_BUTTON = 'button[data-dismiss="modal"]'
# -----------------------------

def initialize_driver():
    """Khởi tạo Chrome Driver với các tùy chọn cho môi trường headless/ARM."""
    try:
        service = Service(CHROMIUM_DRIVER_PATH)
        
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")

        chrome_options.add_experimental_option(
            "prefs", {
                "profile.managed_default_content_settings.images": 2,
                "profile.managed_default_content_settings.stylesheets": 2,
                "profile.managed_default_content_settings.fonts": 2,
                "profile.managed_default_content_settings.media_stream": 2,
            }
        )
        
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
        
    except Exception as e:
        print(f"❌ LỖI KHỞI TẠO DRIVER: {e}")
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
        print(f"❌ LỖI ĐĂNG NHẬP: {e}")
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
            # time.sleep(1) # Chờ trạng thái cập nhật
            WebDriverWait(driver, 3).until(
                EC.text_to_be_present_in_element((By.ID, ID_CONNECT_GRID_LINK), "Disconnect Grid")
            )
            
            text_after = driver.find_element(By.ID, ID_CONNECT_GRID_LINK).text.strip()
            
            if text_after == "Disconnect Grid":
                return True, "✅ TURN ON thành công"
            else:
                return False, f"❌ LỖI: Trạng thái không chuyển từ '{text_before}' sang 'Disconnect Grid' (Hiện tại: {text_after})"
        
        elif text_before == "Disconnect Grid":
            # Đã BẬT, BỎ QUA nhưng được xem là thành công vì đã đạt mục tiêu
            return True, "✅ BỎ QUA: Đã ở trạng thái 'Disconnect Grid' (đã BẬT)"
        
        else:
            return False, f"❌ LỖI: Trạng thái văn bản không xác định: '{text_before}'"

    except Exception as e:
        return False, f"❌ LỖI SELENIUM/TIMEOUT: {e}"
    
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
            # time.sleep(1) # Chờ trạng thái cập nhật
            WebDriverWait(driver, 3).until(
                EC.text_to_be_present_in_element((By.ID, ID_CONNECT_GRID_LINK), "Connect Grid")
            )
            
            text_after = driver.find_element(By.ID, ID_CONNECT_GRID_LINK).text.strip()
            
            if text_after == "Connect Grid":
                return True, "✅ TURN OFF thành công"
            else:
                return False, f"❌ LỖI: Trạng thái không chuyển từ '{text_before}' sang 'Connect Grid' (Hiện tại: {text_after})"
        
        elif text_before == "Connect Grid":
            # Đã TẮT, BỎ QUA nhưng được xem là thành công vì đã đạt mục tiêu
            return True, "✅ BỎ QUA: Đã ở trạng thái 'Connect Grid' (đã TẮT)"
        
        else:
            return False, f"❌ LỖI: Trạng thái văn bản không xác định: '{text_before}'"

    except Exception as e:
        return False, f"❌ LỖI SELENIUM/TIMEOUT: {e}"
    
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

        if required_action == "ON" and inv_info["status"] == "FAULTY":
            print(f"  -> ❌ INV lỗi. Không Turn ON {full_inv_name}.")
            continue
        
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
                error_log.append(f"❌ {full_inv_name} (Hành động: {required_action}): {message}")
                
        else:
            login_error_msg = f"❌ LỖI ĐĂNG NHẬP"
            print(f"   ❌ {login_error_msg}. Bỏ qua INV này.")
            error_log.append(f"{full_inv_name} (Hành động: {required_action}): {login_error_msg}")

    print(f"  --- Kết thúc xử lý {station_name}: {count_performed}/{required_count} INV đã được {required_action}.")

# -----------------------------
def process_inv_list(task_list):
    """
    Hàm worker: Khởi tạo Driver một lần, xử lý toàn bộ INV trong danh sách, và hủy Driver một lần.
    task_list: Danh sách các tuple (full_inv_name, target_url, required_action)
    Trả về: Danh sách các tuple lỗi (full_inv_name, is_success, message)
    """
    
    # Dùng thread name để phân biệt log giữa các luồng
    thread_name = threading.current_thread().name.split("-")[1]

    print(f"\n[{thread_name}] ⚙️ {len(task_list)} INV. Khởi tạo Driver...")
    
    # 1. KHỞI TẠO DRIVER DUY NHẤT CHO TOÀN BỘ DANH SÁCH
    driver = initialize_driver()
    if driver is None:
        print(f"❌ [{thread_name}] LỖI NGHIÊM TRỌNG: Khởi tạo Driver thất bại cho luồng này.")
        return [(task[0], False, "❌ LỖI: Khởi tạo Driver thất bại.") for task in task_list]

    local_error_log = []

    try:
        # 2. LẶP QUA TẤT CẢ CÁC INV TRONG DANH SÁCH (Sử dụng lại driver)
        for i, (full_inv_name, target_url, required_action, inv_status) in enumerate(task_list):
            
            # Log đầu mỗi tác vụ
            log_prefix = f"[{thread_name}] ({i+1}/{len(task_list)}) {full_inv_name} ({required_action})"
            print(f"\n{log_prefix} ⚙️...")

            if required_action == "ON" and inv_status == "FAULTY":
                message = "❌ BỎ QUA: INV lỗi không khởi động INV (OFF)."
                print(f"{log_prefix} ⚠️ {message}")
                continue
            
            # 2.1 Đăng nhập
            login_success = login(driver, target_url, USERNAME, PASSWORD)
            
            if not login_success:
                local_error_log.append((full_inv_name, False, "LỖI ĐĂNG NHẬP"))
                print(f"{log_prefix} ❌ Đăng nhập thất bại. Chuyển sang INV tiếp theo.")
                continue # Bỏ qua điều khiển nếu đăng nhập lỗi

            # 2.2 Điều khiển
            action_function = turn_off_grid if required_action == "OFF" else turn_on_grid
            is_success, message = action_function(driver)
            
            # Log kết quả điều khiển
            if is_success:
                print(f"{log_prefix} ✅ THÀNH CÔNG: {message}")
            else:
                local_error_log.append((full_inv_name, False, message))
                print(f"{log_prefix} ❌ LỖI ĐIỀU KHIỂN: {message}")

    except Exception as e:
        local_error_log.append(("", False, f"❌ LỖI TOÀN CỤC LUỒNG: {e}"))
        print(f"❌ [{thread_name}] LỖI BẤT THƯỜNG: {e}")

    finally:
        # 3. CHỈ HUỶ DRIVER MỘT LẦN KHI TẤT CẢ TÁC VỤ KẾT THÚC
        if driver:
            print(f"[{thread_name}] Hoàn thành danh sách. Đóng Driver.")
            driver.quit()
            
    return local_error_log

# -----------------------------

def run_parallel(list_request):
    
    start_time = time.time()
    print(f"Bắt đầu chương trình bằng Đa luồng (Tái sử dụng Driver, {MAX_WORKERS} luồng)...")
    
    # 1. TẠO DANH SÁCH TÁC VỤ (GIỮ NGUYÊN LOGIC CŨ)
    tasks_to_run = []
    for zone_name, stations in SYSTEM_URLS.items():
        for station_name, inverters in stations.items():
            
            if station_name in list_request:
                request = list_request[station_name]
                required_action = request["action"]
                required_count = request["count"]
                
                count_added = 0
                
                # Sắp xếp để Off/On các INV theo thứ tự (ví dụ: INV-01, INV-02,...)
                sorted_invs = sorted(inverters.items()) 

                for inv_name, inv_info in sorted_invs:
                    if count_added >= required_count:
                        break

                    full_inv_name = f"{station_name}-{inv_name}"
                    target_url = inv_info["url"]
                    inv_status = inv_info.get("status", "OK").upper()
                    
                    tasks_to_run.append((full_inv_name, target_url, required_action, inv_status))
                    count_added += 1

    
    
    print(f"Tổng cộng có {len(tasks_to_run)} tác vụ INV cần xử lý.")

    # 2. PHÂN CHIA TÁC VỤ CHO CÁC LUỒNG (ROUND-ROBIN DISTRIBUTION)
    # Đây là bước quan trọng để load-balancing
    chunked_tasks = [[] for _ in range(MAX_WORKERS)]
    for i, task in enumerate(tasks_to_run):
        worker_index = i % MAX_WORKERS
        chunked_tasks[worker_index].append(task)

    # Lọc các danh sách rỗng nếu tổng số task ít hơn MAX_WORKERS
    tasks_to_submit = [chunk for chunk in chunked_tasks if chunk]

    # 3. CHẠY ĐA LUỒNG
    final_error_log = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Gửi danh sách các chunked_tasks thay vì từng task đơn lẻ
        # Mỗi phần tử trong results là danh sách lỗi local_error_log từ mỗi luồng
        results = list(executor.map(process_inv_list, tasks_to_submit))

    # 4. PHÂN TÍCH KẾT QUẢ VÀ TỔNG HỢP LOG
    for local_error_log in results:
        for full_inv_name, is_success, message in local_error_log:
             # is_success luôn là False ở đây vì chúng ta chỉ thu thập lỗi
            final_error_log.append(f"{full_inv_name} ({message})")

    # ... (Phần báo cáo cuối cùng, tính thời gian và in log lỗi giữ nguyên) ...
    end_time = time.time()
    total_time = end_time - start_time
    
    print("\n\n==============================================")
    print("BÁO CÁO KẾT THÚC CHƯƠNG TRÌNH")
    print("==============================================")
    
    if final_error_log:
        print(f"❌ CÓ {len(final_error_log)} LỖI ĐIỀU KHIỂN/ĐĂNG NHẬP CẦN XEM XÉT:")
        for error in final_error_log:
            print(f"   - {error}")
    else:
        print("✅ KHÔNG CÓ LỖI ĐIỀU KHIỂN/ĐĂNG NHẬP NÀO ĐƯỢC GHI NHẬN.")
    
    minutes = int(total_time // 60)
    seconds = total_time % 60
    
    print(f"\n⏰ TỔNG THỜI GIAN CHẠY: {minutes} phút {seconds:.2f} giây.")
    print("Hoàn thành và đóng trình duyệt.")

# -----------------------------

def run_sequentially(list_request):
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

    print("\n⚙️ điều khiển theo số lượng INV...")

    try:
        # Vòng lặp 1 & 2: Duyệt qua Zone và Station
        for zone_name, stations in SYSTEM_URLS.items():
            for station_name, inverters in stations.items():
                
                if station_name in list_request:
                    request = list_request[station_name]
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

    finally:
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

# -----------------------------

def extract_and_log_status_code(driver, full_inv_name):
    extracted_codes_log = []
    name = threading.current_thread().name.split("-")[1]
    log_prefix = f"[{name}] {full_inv_name}"
    
    try:
        # 1. Click button Status History và chờ hộp thoại mở (Giữ nguyên)
        log_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_STATUS_LOG_BUTTON))
        )
        log_button.click()
        
        log_dialog = WebDriverWait(driver, 5).until(
            EC.visibility_of_element_located((By.ID, ID_LOG_DIALOG))
        )

        # 2. CHỜ 2 GIÂY ĐỂ DỮ LIỆU LOG LOAD (Giữ nguyên)
        time.sleep(2) 

        # 3. TÌM VÀ PHÂN TÍCH TỪNG DÒNG LOG
        log_content_container = log_dialog.find_element(By.CSS_SELECTOR, SELECTOR_LOG_CONTENT)
        log_entries = log_content_container.find_elements(By.TAG_NAME, "span")
        
        fault_messages = []       # Lỗi ưu tiên (k-log-fault)
        classified_messages = []  # Log đã phân loại (Error, Warning, Status)

        for entry in log_entries:
            entry_text = entry.text.strip()
            if not entry_text:
                continue

            # A. Kiểm tra lỗi ưu tiên (k-log-fault)
            if "k-log-fault" in entry.get_attribute("class"):
                formatted_message = f"Code Fault: ❌ {entry_text}"
                print(f"{log_prefix}    !!! {formatted_message}") 
                fault_messages.append(f"{full_inv_name}: {formatted_message}")
            
            # B. Trích xuất mã số từ ngoặc đơn
            code_match = re.search(r'\((?P<code_value>\d+)\)', entry_text)
            
            if code_match:
                code_value = int(code_match.group("code_value"))
                
                # PHÂN LOẠI LOG DỰA TRÊN MÃ SỐ
                
                if code_value in ERROR_CODES:
                    prefix = "Error Code"
                    icon = "❌"
                    
                elif code_value in WARNING_CODES:
                    prefix = "Warning Code"
                    icon = "⚠️"
                    
                elif code_value in STATUS_CODES:
                    prefix = "Status Code"
                    icon = "✅"
                    
                else:
                    # Nếu không nằm trong bất kỳ list nào, chỉ hiển thị là Status
                    prefix = "Unclassified Status"
                    icon = "❓"
                
                # Định dạng tin nhắn cuối cùng
                formatted_message = f"{prefix}: {icon} {entry_text}"
                classified_messages.append(f"{full_inv_name}: {formatted_message}")


        # 4. Xử lý Uniqueness và format cho Classified Messages
        # Lọc các thông báo trùng lặp (nếu cùng một dòng log được tạo ra nhiều lần)
        unique_classified_messages = sorted(list(set(classified_messages)))
        
        # 5. Ghi Log ra console
        for message in unique_classified_messages:
            # Tách để chỉ lấy nội dung sau tiền tố INV_NAME:
            content = message.split(': ', 1)[1] 
            print(f"{log_prefix}    -> {content}")


        # 6. Tổng hợp: Fault Codes (ưu tiên) trước, Classified Messages sau
        extracted_codes_log.extend(fault_messages)
        extracted_codes_log.extend(unique_classified_messages)
        
        if not extracted_codes_log:
             print(f"{log_prefix}    -> Không tìm thấy mã trạng thái hay lỗi nào.")

    except Exception as e:
        extracted_codes_log.append(f"{full_inv_name}: LỖI TRÍCH XUẤT LOG: {e}")
        print(f"{log_prefix} ❌ LỖI MỞ/ĐỌC LOG: {e}")
    
    finally:
        # 7. Đóng hộp thoại Log (Giữ nguyên)
        try:
            close_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, SELECTOR_CLOSE_BUTTON))
            )
            close_button.click()
            WebDriverWait(driver, 3).until(
                 EC.invisibility_of_element_located((By.ID, ID_LOG_DIALOG))
            )
        except:
            pass
            
    return extracted_codes_log

# -----------------------------

def process_status_logging_list(task_list):
    """
    Hàm worker chuyên biệt: CHỈ truy cập URL và trích xuất log trạng thái (Status Code), 
    BỎ QUA bước đăng nhập.
    task_list: Danh sách các tuple (full_inv_name, target_url, required_action, inv_status)
    Trả về: Danh sách các log mã trạng thái (local_status_code_log)
    """
    thread_name = threading.current_thread().name.split("-")[1]
    print(f"\n[{thread_name}] Bắt đầu xử lý LOG TRẠNG THÁI cho {len(task_list)} INV. Khởi tạo Driver...")
    
    driver = initialize_driver()
    if driver is None:
        return [(task[0] + ": LỖI KHỞI TẠO DRIVER")]

    local_status_code_log = []

    try:
        for i, (full_inv_name, target_url, required_action, inv_status) in enumerate(task_list):
            
            log_prefix = f"[{thread_name}] (Log {i+1}/{len(task_list)}) {full_inv_name}"
            
            # Đảm bảo URL có protocol (ví dụ: http://)
            if not target_url.startswith(('http://', 'https://')):
                full_url = f"http://{target_url}"
            else:
                full_url = target_url
            
            try:
                # Điều hướng trực tiếp đến trang web
                driver.get(full_url)
                # print(f"{log_prefix} -> Đã truy cập URL thành công: {full_url}")
            except Exception as e:
                # Ghi lại lỗi truy cập và chuyển sang INV tiếp theo
                local_status_code_log.append(f"{full_inv_name}: Code Fault: ❌LỖI TRUY CẬP URL")
                print(f"{log_prefix} ❌ LỖI TRUY CẬP URL. Chuyển sang INV tiếp theo.")
                continue 

            # 2. TRÍCH XUẤT LOG
            # Hàm này sẽ tìm nút, click, trích xuất log và đóng hộp thoại.
            extracted_codes = extract_and_log_status_code(driver, full_inv_name)
            local_status_code_log.extend(extracted_codes) 

    except Exception as e:
        local_status_code_log.append(f"LỖI TOÀN CỤC LUỒNG LOG: {e}")
        print(f"[{thread_name}] LỖI BẤT THƯỜNG TOÀN CỤC: {e}")

    finally:
        if driver:
            print(f"[{thread_name}] Hoàn thành danh sách Log. Đóng Driver.")
            driver.quit()
            
    return local_status_code_log

# -----------------------------

def run_logger():
    start_time = time.time()
    print(f"Bắt đầu chương trình ({MAX_WORKERS} luồng).")

    tasks_to_run = []

    # --- 1. TẠO DANH SÁCH TÁC VỤ CHO TẤT CẢ INV ---
    # Duyệt qua TẤT CẢ INV, không cần kiểm tra CONTROL_REQUESTS
    for zone_name, stations in SYSTEM_URLS.items():
        for station_name, inverters in stations.items():
            for inv_name, inv_info in inverters.items(): # Duyệt qua mọi INV
                
                full_inv_name = f"{station_name}-{inv_name}"
                target_url = inv_info["url"]
                
                # Lấy trạng thái INV (để có thể báo cáo nếu INV đó FAULTY)
                inv_status = inv_info.get("status", "OK").upper()
                
                # 'required_action' được đặt là "LOG" (Hoặc bất kỳ giá trị nào)
                # vì nó không được sử dụng trong hàm logging.
                tasks_to_run.append((full_inv_name, target_url, "LOG", inv_status)) 

    print(f"Tổng cộng có {len(tasks_to_run)} tác vụ INV cần trích xuất Log.")

    # --- 2. PHÂN CHIA TÁC VỤ CHO CÁC LUỒNG (Round-Robin) ---
    chunked_tasks = [[] for _ in range(MAX_WORKERS)]
    for i, task in enumerate(tasks_to_run):
        worker_index = i % MAX_WORKERS
        chunked_tasks[worker_index].append(task)

    tasks_to_submit = [chunk for chunk in chunked_tasks if chunk]

    final_status_code_log = [] 

    print("\n==============================================")
    print("Bắt đầu trích xuất Log Status (Song song)")
    print("==============================================")
    
    # --- 3. CHẠY TRÍCH XUẤT LOG STATUS ---
    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            # Chạy hàm logging đã được tối ưu
            results_logging = list(executor.map(process_status_logging_list, tasks_to_submit))

        # Tổng hợp log trạng thái
        for local_status_code_log in results_logging:
            final_status_code_log.extend(local_status_code_log)
            
    except Exception as e:
        print(f"LỖI XẢY RA TRONG QUÁ TRÌNH THỰC HIỆN LOGGING: {e}")

    # --- 4. BÁO CÁO KẾT QUẢ VÀ THỜI GIAN ---
    end_time = time.time()
    total_time = end_time - start_time

    # Sắp xếp log theo tên INV (phần trước dấu ": ", ví dụ: "B2-INV-01")
    final_status_code_log.sort(key=lambda x: x.split(': ', 1)[0])

    print("\n\n==============================================")
    print("BÁO CÁO KẾT THÚC CHƯƠNG TRÌNH LOG STATUS")
    print("==============================================")
    
    if final_status_code_log:
        print("\n📝 CÁC MÃ TRẠNG THÁI ĐƯỢC TRÍCH XUẤT TỪ LOGS:")
        for log_entry in final_status_code_log:
            print(f"   - {log_entry}")
    else:
        print("\n✅ KHÔNG CÓ MÃ TRẠNG THÁI NÀO ĐƯỢC TRÍCH XUẤT.")
        
    minutes = int(total_time // 60)
    seconds = total_time % 60
    
    print(f"\n⏰ TỔNG THỜI GIAN CHẠY: {minutes} phút {seconds:.2f} giây.")
    print("Hoàn thành và đóng trình duyệt.")

# -----------------------------
# -----------------------------

def main():
    run_logger()
    # run_parallel(CONTROL_REQUESTS_ON)
    # run_sequentially(CONTROL_REQUESTS_ON)

if __name__ == "__main__":
    CONTROL_REQUESTS = {
        "B2": {"action": "OFF", "count": 10},
        "B3R1": {"action": "OFF", "count": 9},
        "B4R2": {"action": "OFF", "count": 10},
        "B5R2": {"action": "OFF", "count": 10},
        "B6R2": {"action": "OFF", "count": 10},
        "B7": {"action": "OFF", "count": 10},
        "B8": {"action": "OFF", "count": 5},
        "B13-14": {"action": "OFF", "count": 10},
    } 
    CONTROL_REQUESTS_ON = {
        "B2": {"action": "ON", "count": 10},
        "B3R1": {"action": "ON", "count": 9},
        "B4R2": {"action": "ON", "count": 10},
        "B5R2": {"action": "ON", "count": 10},
        "B6R2": {"action": "ON", "count": 10},
        "B7": {"action": "ON", "count": 10},
        "B8": {"action": "ON", "count": 5},
        "B13-14": {"action": "ON", "count": 10},
        "B11": {"action": "ON", "count": 10},
    }    
    SYSTEM_URLS = {
        "Zone B": {
            "B2": {
                "INV-01": { "url": "10.10.10.101", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.102", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.103", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.104", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.105", "info": "Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.106", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.107", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.108", "info": "Inverter số 8", "status": "OK"},
                "INV-09": { "url": "10.10.10.109", "info": "Inverter số 9", "status": "OK"},
                "INV-10": { "url": "10.10.10.110", "info": "Inverter số 10", "status": "OK"},
            },
            "B3R1": {
                "INV-01": { "url": "10.10.10.121", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.122", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.123", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.124", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.125", "info": "Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.126", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.127", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.128", "info": "Inverter số 8", "status": "OK"},
                "INV-09": { "url": "10.10.10.129", "info": "Inverter số 9", "status": "FAULTY"},
            },
            "B3R2": {
                "INV-01": { "url": "10.10.10.111", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.112", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.113", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.114", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.115", "info": "Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.116", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.117", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.118", "info": "Inverter số 8", "status": "OK"},
                "INV-09": { "url": "10.10.10.119", "info": "Inverter số 9", "status": "OK"},
            },
            "B4R1": {
                "INV-01": { "url": "10.10.10.141", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.142", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.143", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.144", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.145", "info": "Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.146", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.147", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.148", "info": "Inverter số 8", "status": "OK"},
                "INV-09": { "url": "10.10.10.149", "info": "Inverter số 9", "status": "OK"},
                "INV-10": { "url": "10.10.10.150", "info": "Inverter số 10", "status": "OK"},
            },        
            "B4R2": {
                "INV-01": { "url": "10.10.10.131", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.132", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.133", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.134", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.135", "info": "Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.136", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.137", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.138", "info": "Inverter số 8", "status": "OK"},
                "INV-09": { "url": "10.10.10.139", "info": "Inverter số 9", "status": "OK"},
                "INV-10": { "url": "10.10.10.140", "info": "Inverter số 10", "status": "OK"},
            },        
            "B5R1": {
                "INV-01": { "url": "10.10.10.161", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.162", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.163", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.164", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.165", "info": "Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.166", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.167", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.168", "info": "Inverter số 8", "status": "OK"},
                "INV-09": { "url": "10.10.10.169", "info": "Inverter số 9", "status": "OK"},
                "INV-10": { "url": "10.10.10.170", "info": "Inverter số 10", "status": "OK"},
            },
            "B5R2": {
                "INV-01": { "url": "10.10.10.151", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.152", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.153", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.154", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.155", "info": "Inverter số 5", "status": "FAULTY"},
                "INV-06": { "url": "10.10.10.156", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.157", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.158", "info": "Inverter số 8", "status": "OK"},
                "INV-09": { "url": "10.10.10.159", "info": "Inverter số 9", "status": "OK"},
                "INV-10": { "url": "10.10.10.160", "info": "Inverter số 10", "status": "OK"},
            },
            "B6R1": {
                "INV-01": { "url": "10.10.10.181", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.182", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.183", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.184", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.185", "info": "Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.186", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.187", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.188", "info": "Inverter số 8", "status": "OK"},
                "INV-09": { "url": "10.10.10.189", "info": "Inverter số 9", "status": "OK"},
                "INV-10": { "url": "10.10.10.190", "info": "Inverter số 10", "status": "OK"},
            },
            "B6R2": {
                "INV-01": { "url": "10.10.10.171", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.172", "info": "Inverter số 2", "status": "FAULTY"},
                "INV-03": { "url": "10.10.10.173", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.174", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.175", "info": "Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.176", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.177", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.178", "info": "Inverter số 8", "status": "OK"},
                "INV-09": { "url": "10.10.10.179", "info": "Inverter số 9", "status": "OK"},
                "INV-10": { "url": "10.10.10.180", "info": "Inverter số 10", "status": "OK"},
            },
            "B7": {
                "INV-01": { "url": "10.10.10.191", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.192", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.193", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.194", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.195", "info": "Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.196", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.197", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.198", "info": "Inverter số 8", "status": "FAULTY"},
                "INV-09": { "url": "10.10.10.199", "info": "Inverter số 9", "status": "OK"},
                "INV-10": { "url": "10.10.10.200", "info": "Inverter số 10", "status": "OK"},
            },
            "B8": {
                "INV-01": { "url": "10.10.10.201", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.202", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.203", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.204", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.205", "info": "Inverter số 5", "status": "OK"},
            },
            "B11": {
                "INV-01": { "url": "10.10.10.211", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.212", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.213", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.214", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.215", "info": "Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.216", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.217", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.218", "info": "Inverter số 8", "status": "OK"},
                "INV-09": { "url": "10.10.10.219", "info": "Inverter số 9", "status": "OK"},
                "INV-10": { "url": "10.10.10.220", "info": "Inverter số 10", "status": "FAULTY"},
            },
            "B12": {
                "INV-01": { "url": "10.10.10.241", "info": "Inverter số 1", "status": "OK"},
                "INV-02": { "url": "10.10.10.242", "info": "Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.243", "info": "Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.244", "info": "Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.245", "info": "Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.246", "info": "Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.247", "info": "Inverter số 7", "status": "OK"},
                "INV-08": { "url": "10.10.10.248", "info": "Inverter số 8", "status": "OK"},
                "INV-09": { "url": "10.10.10.249", "info": "Inverter số 9", "status": "OK"},
                "INV-10": { "url": "10.10.10.250", "info": "Inverter số 10", "status": "OK"},
            },  
            "B13-14": {
                "INV-01": { "url": "10.10.10.221", "info": "B13 Inverter số 1", "status": "FAULTY"},
                "INV-02": { "url": "10.10.10.222", "info": "B13 Inverter số 2", "status": "OK"},
                "INV-03": { "url": "10.10.10.223", "info": "B13 Inverter số 3", "status": "OK"},
                "INV-04": { "url": "10.10.10.224", "info": "B13 Inverter số 4", "status": "OK"},
                "INV-05": { "url": "10.10.10.225", "info": "B13 Inverter số 5", "status": "OK"},
                "INV-06": { "url": "10.10.10.226", "info": "B13 Inverter số 6", "status": "OK"},
                "INV-07": { "url": "10.10.10.231", "info": "B14 Inverter số 1", "status": "OK"},
                "INV-08": { "url": "10.10.10.232", "info": "B14 Inverter số 2", "status": "OK"},
                "INV-09": { "url": "10.10.10.233", "info": "B14 Inverter số 3", "status": "OK"},
                "INV-10": { "url": "10.10.10.234", "info": "B14 Inverter số 4", "status": "OK"},
            },
        }
    }
    
    STATUS_CODES = (2, 4, 8, 9)
    WARNING_CODES = (36, 38, 41, 42, 43, 44, 45, 46, 64, 75, 73, 79)
    ERROR_CODES = (180, 181, 182, 183, 184, 185, 186, 188, 189, 190, 191, 192, 193, 194, 195, 203, 204, 205, 206, 207, 208, 209, 216, 217, 226, 227)

    main()