# setup_chromedriver.py
import os
import sys
import zipfile
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service

def setup_chromedriver():
    """Tự động thiết lập ChromeDriver"""
    
    print("🔧 Đang thiết lập ChromeDriver...")
    
    # Xác định hệ điều hành
    if sys.platform.startswith("win32"):
        driver_name = "chromedriver.exe"
        platform = "win32"
    elif sys.platform.startswith("linux"):
        driver_name = "chromedriver"
        platform = "linux64"
    elif sys.platform.startswith("darwin"):
        driver_name = "chromedriver"
        platform = "mac64"
    else:
        print("❌ Hệ điều hành không được hỗ trợ")
        return False
    
    driver_path = os.path.join("drivers", driver_name)
    
    # Tạo thư mục drivers nếu chưa tồn tại
    os.makedirs("drivers", exist_ok=True)
    
    # Kiểm tra nếu ChromeDriver đã tồn tại
    if os.path.exists(driver_path):
        try:
            service = Service(driver_path)
            driver = webdriver.Chrome(service=service)
            driver.quit()
            print("✅ ChromeDriver đã sẵn sàng")
            return True
        except:
            print("⚠️ ChromeDriver hiện tại bị lỗi, đang tải lại...")
    
    # Tải ChromeDriver tự động
    try:
        print("📥 Đang tải ChromeDriver...")
        
        # Lấy phiên bản Chrome
        try:
            if sys.platform.startswith("win32"):
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version = winreg.QueryValueEx(key, "version")[0]
            else:
                import subprocess
                result = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True)
                version = result.stdout.split()[-1]
        except:
            version = "114.0.5735.90"  # Fallback version
        
        major_version = version.split('.')[0]
        
        # Tải ChromeDriver
        url = f"https://storage.googleapis.com/chrome-for-testing-public/{major_version}.0.5735.90/{platform}/chromedriver-{platform}.zip"
        
        print(f"🌐 Đang tải ChromeDriver phiên bản {major_version}...")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            zip_path = "chromedriver.zip"
            with open(zip_path, "wb") as f:
                f.write(response.content)
            
            # Giải nén
            with zipfile.ZipFile(zip_path, "r") as zip_ref:
                zip_ref.extractall("drivers")
            
            # Đổi tên file nếu cần
            extracted_path = os.path.join("drivers", "chromedriver-" + platform, "chromedriver" + (".exe" if platform == "win32" else ""))
            if os.path.exists(extracted_path):
                os.rename(extracted_path, driver_path)
            
            # Dọn dẹp
            if os.path.exists(zip_path):
                os.remove(zip_path)
            
            # Cấp quyền thực thi (Linux/Mac)
            if not sys.platform.startswith("win32"):
                os.chmod(driver_path, 0o755)
            
            print("✅ Đã tải và cài đặt ChromeDriver thành công")
            return True
            
        else:
            print("❌ Không thể tải ChromeDriver, đang thử phương pháp thay thế...")
            return setup_chromedriver_fallback()
            
    except Exception as e:
        print(f"❌ Lỗi khi thiết lập ChromeDriver: {e}")
        return setup_chromedriver_fallback()

def setup_chromedriver_fallback():
    """Phương pháp fallback sử dụng webdriver-manager"""
    try:
        print("🔄 Đang thử phương pháp fallback...")
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.service import Service as ChromeService
        
        driver_path = ChromeDriverManager().install()
        print(f"✅ Đã cài đặt ChromeDriver tại: {driver_path}")
        return True
    except Exception as e:
        print(f"❌ Lỗi fallback: {e}")
        return False

if __name__ == "__main__":
    success = setup_chromedriver()
    sys.exit(0 if success else 1)