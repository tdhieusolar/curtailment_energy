# system_check.py
import os
import sys
import platform
import subprocess
import webbrowser
from pathlib import Path

class SystemChecker:
    def __init__(self):
        self.system = platform.system().lower()
        self.is_windows = self.system == "windows"
        self.is_linux = self.system == "linux"
        self.is_mac = self.system == "darwin"
        
        self.browsers = {
            'chrome': {
                'windows': [
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                ],
                'linux': [
                    "/usr/bin/google-chrome",
                    "/usr/bin/google-chrome-stable",
                    "/usr/bin/chromium-browser",
                    "/usr/bin/chromium",
                    "/snap/bin/chromium"
                ],
                'mac': [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                ]
            },
            'edge': {
                'windows': [
                    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
                ],
                'linux': [
                    "/usr/bin/microsoft-edge",
                    "/usr/bin/microsoft-edge-stable"
                ],
                'mac': [
                    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
                ]
            },
            'firefox': {
                'windows': [
                    r"C:\Program Files\Mozilla Firefox\firefox.exe",
                    r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
                ],
                'linux': [
                    "/usr/bin/firefox",
                    "/usr/bin/firefox-esr"
                ],
                'mac': [
                    "/Applications/Firefox.app/Contents/MacOS/firefox"
                ]
            }
        }
    
    def check_browser(self, browser_name):
        """Kiểm tra trình duyệt có tồn tại không"""
        if browser_name not in self.browsers:
            return None
            
        paths = self.browsers[browser_name].get(self.system, [])
        for path in paths:
            if os.path.exists(path):
                return path
        return None
    
    def check_chromedriver(self):
        """Kiểm tra ChromeDriver"""
        possible_paths = []
        
        if self.is_windows:
            possible_paths.extend([
                "chromedriver.exe",
                os.path.join("drivers", "chromedriver.exe"),
                r"C:\Windows\System32\chromedriver.exe"
            ])
        else:
            possible_paths.extend([
                "chromedriver",
                os.path.join("drivers", "chromedriver"),
                "/usr/local/bin/chromedriver",
                "/usr/bin/chromedriver",
                "/snap/bin/chromedriver"
            ])
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def check_edgedriver(self):
        """Kiểm tra EdgeDriver"""
        possible_paths = []
        
        if self.is_windows:
            possible_paths.extend([
                "msedgedriver.exe",
                os.path.join("drivers", "msedgedriver.exe"),
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedgedriver.exe"
            ])
        else:
            possible_paths.extend([
                "msedgedriver",
                os.path.join("drivers", "msedgedriver"),
                "/usr/local/bin/msedgedriver",
                "/usr/bin/msedgedriver"
            ])
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        return None
    
    def get_user_choice(self, prompt, options):
        """Hiển thị menu lựa chọn cho người dùng"""
        print(f"\n{prompt}")
        for i, option in enumerate(options, 1):
            print(f"{i}. {option}")
        
        while True:
            try:
                choice = input(f"\nChọn (1-{len(options)}): ").strip()
                if choice.isdigit() and 1 <= int(choice) <= len(options):
                    return options[int(choice) - 1]
                print("❌ Lựa chọn không hợp lệ!")
            except KeyboardInterrupt:
                print("\n👋 Thoát chương trình")
                sys.exit(0)
    
    def install_chromedriver_auto(self):
        """Tự động cài đặt ChromeDriver"""
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.core.os_manager import ChromeType
            
            print("📥 Đang tải ChromeDriver...")
            driver_path = ChromeDriverManager().install()
            print(f"✅ Đã cài đặt ChromeDriver: {driver_path}")
            return driver_path
        except Exception as e:
            print(f"❌ Lỗi cài đặt ChromeDriver: {e}")
            return None
    
    def install_edgedriver_auto(self):
        """Tự động cài đặt EdgeDriver"""
        try:
            from webdriver_manager.microsoft import EdgeDriverManager
            
            print("📥 Đang tải EdgeDriver...")
            driver_path = EdgeDriverManager().install()
            print(f"✅ Đã cài đặt EdgeDriver: {driver_path}")
            return driver_path
        except Exception as e:
            print(f"❌ Lỗi cài đặt EdgeDriver: {e}")
            return None
    
    def suggest_browser_install(self):
        """Đề xuất cài đặt trình duyệt"""
        if self.is_windows:
            browsers = [
                ("Microsoft Edge", "https://www.microsoft.com/en-us/edge"),
                ("Google Chrome", "https://www.google.com/chrome/"),
                ("Mozilla Firefox", "https://www.mozilla.org/firefox/")
            ]
        else:
            browsers = [
                ("Google Chrome", "https://www.google.com/chrome/"),
                ("Microsoft Edge", "https://www.microsoft.com/en-us/edge"),
                ("Chromium", "sudo apt install chromium-browser" if self.is_linux else "brew install chromium")
            ]
        
        print("\n🔍 Không tìm thấy trình duyệt tương thích!")
        print("📦 Các trình duyệt được đề xuất:")
        
        for i, (name, install_info) in enumerate(browsers, 1):
            print(f"   {i}. {name}")
        
        choice = self.get_user_choice(
            "Bạn muốn cài đặt trình duyệt nào?",
            [name for name, _ in browsers]
        )
        
        for name, install_info in browsers:
            if name == choice:
                if install_info.startswith(("http", "https")):
                    print(f"🌐 Mở trình duyệt để tải: {install_info}")
                    webbrowser.open(install_info)
                    input("👆 Nhấn Enter sau khi cài đặt xong...")
                else:
                    print(f"🔧 Chạy lệnh: {install_info}")
                    if input("Tự động chạy lệnh cài đặt? (y/n): ").lower() == 'y':
                        try:
                            subprocess.run(install_info.split(), check=True)
                            print("✅ Cài đặt thành công!")
                        except Exception as e:
                            print(f"❌ Lỗi cài đặt: {e}")
                return True
        return False
    
    def run_check(self):
        """Chạy kiểm tra toàn diện"""
        print("🔍 KIỂM TRA HỆ THỐNG TỰ ĐỘNG")
        print("=" * 50)
        
        # Kiểm tra trình duyệt
        available_browsers = []
        for browser in ['chrome', 'edge', 'firefox']:
            path = self.check_browser(browser)
            if path:
                available_browsers.append((browser, path))
                print(f"✅ {browser.upper()}: {path}")
            else:
                print(f"❌ {browser.upper()}: Không tìm thấy")
        
        if not available_browsers:
            print("\n⚠️ Không tìm thấy trình duyệt nào!")
            if not self.suggest_browser_install():
                return None, None
            # Kiểm tra lại sau khi cài đặt
            available_browsers = []
            for browser in ['chrome', 'edge', 'firefox']:
                path = self.check_browser(browser)
                if path:
                    available_browsers.append((browser, path))
        
        if not available_browsers:
            print("❌ Vẫn không tìm thấy trình duyệt sau khi cài đặt")
            return None, None
        
        # Chọn trình duyệt
        if len(available_browsers) == 1:
            selected_browser, browser_path = available_browsers[0]
        else:
            browser_options = [f"{browser.upper()} ({path})" for browser, path in available_browsers]
            selected_option = self.get_user_choice(
                "Chọn trình duyệt để sử dụng:",
                browser_options
            )
            for browser, path in available_browsers:
                if f"{browser.upper()} ({path})" == selected_option:
                    selected_browser, browser_path = browser, path
                    break
        
        # Kiểm tra driver
        if selected_browser == 'chrome':
            driver_path = self.check_chromedriver()
            if not driver_path:
                print("❌ Không tìm thấy ChromeDriver")
                if input("Tự động cài đặt ChromeDriver? (y/n): ").lower() == 'y':
                    driver_path = self.install_chromedriver_auto()
        elif selected_browser == 'edge':
            driver_path = self.check_edgedriver()
            if not driver_path:
                print("❌ Không tìm thấy EdgeDriver")
                if input("Tự động cài đặt EdgeDriver? (y/n): ").lower() == 'y':
                    driver_path = self.install_edgedriver_auto()
        else:  # firefox
            driver_path = None  # Firefox sử dụng GeckoDriver, cần xử lý riêng
        
        if not driver_path:
            print("❌ Không tìm thấy driver phù hợp")
            return None, None
        
        print(f"\n🎯 Đã chọn: {selected_browser.upper()}")
        print(f"📁 Trình duyệt: {browser_path}")
        print(f"📁 Driver: {driver_path}")
        
        # Lưu cấu hình
        config = {
            'browser': selected_browser,
            'browser_path': browser_path,
            'driver_path': driver_path
        }
        
        self.save_config(config)
        return selected_browser, driver_path
    
    def save_config(self, config):
        """Lưu cấu hình vào file"""
        config_content = f"""
# Auto-generated browser configuration
BROWSER = "{config['browser']}"
BROWSER_PATH = "{config['browser_path']}"
DRIVER_PATH = "{config['driver_path']}"
"""
        with open("browser_config.py", "w", encoding="utf-8") as f:
            f.write(config_content)
        print("✅ Đã lưu cấu hình vào browser_config.py")

def main():
    checker = SystemChecker()
    browser, driver_path = checker.run_check()
    
    if browser and driver_path:
        print("\n🎉 HỆ THỐNG ĐÃ SẴN SÀNG!")
        print("🚀 Bạn có thể chạy chương trình chính")
        return True
    else:
        print("\n❌ HỆ THỐNG CHƯA SẴN SÀNG!")
        print("📝 Vui lòng cài đặt trình duyệt và driver thủ công")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)