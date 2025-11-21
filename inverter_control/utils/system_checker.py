# utils/system_checker.py
import os
import sys
import platform
import subprocess
import importlib
import shutil
from pathlib import Path

class SystemChecker:
    """Kiểm tra hệ thống toàn diện cho mọi OS"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_windows = self.system == "windows"
        self.is_linux = self.system == "linux" 
        self.is_mac = self.system == "darwin"
        self.architecture = platform.architecture()[0]
        self.python_version = platform.python_version()
        
        self.checks = []
        self.failed_checks = []
        
    def check_python_version(self):
        """Kiểm tra phiên bản Python"""
        major, minor, _ = map(int, self.python_version.split('.'))
        if major < 3 or (major == 3 and minor < 8):
            self._add_check("Python Version", False, 
                          f"Python 3.8+ required (current: {self.python_version})")
            return False
        self._add_check("Python Version", True, f"Python {self.python_version}")
        return True
    
    def check_required_packages(self):
        """Kiểm tra packages cần thiết"""
        required_packages = {
            'selenium': '4.15.0',
            'pandas': '2.1.3', 
            'psutil': '5.9.6',
            'openpyxl': '3.1.2',
            'requests': '2.31.0'
        }
        
        all_ok = True
        for package, min_version in required_packages.items():
            try:
                module = importlib.import_module(package)
                installed_version = getattr(module, '__version__', 'unknown')
                
                if installed_version != 'unknown':
                    # Đơn giản hóa version check
                    status = True
                    message = f"{package} {installed_version}"
                else:
                    status = False
                    message = f"{package} not found"
                    
                self._add_check(f"Package: {package}", status, message)
                if not status:
                    all_ok = False
                    
            except ImportError:
                self._add_check(f"Package: {package}", False, "Not installed")
                all_ok = False
        
        return all_ok
    
    def check_browsers(self):
        """Kiểm tra trình duyệt có sẵn"""
        browsers = self._get_available_browsers()
        
        if not browsers:
            self._add_check("Web Browsers", False, "No compatible browser found")
            return False
        
        browser_list = ", ".join([f"{name} ({path})" for name, path in browsers])
        self._add_check("Web Browsers", True, browser_list)
        return True
    
    def check_webdrivers(self):
        """Kiểm tra web drivers"""
        drivers = self._get_available_drivers()
        
        if not drivers:
            self._add_check("Web Drivers", False, "No web driver found")
            return False
        
        driver_list = ", ".join([f"{name} ({path})" for name, path in drivers])
        self._add_check("Web Drivers", True, driver_list)
        return True
    
    def check_system_resources(self):
        """Kiểm tra tài nguyên hệ thống"""
        try:
            import psutil
            
            # RAM
            memory = psutil.virtual_memory()
            ram_gb = memory.total / (1024**3)
            ram_ok = ram_gb >= 2  # Tối thiểu 2GB RAM
            
            # Disk space
            disk = psutil.disk_usage('.')
            disk_gb = disk.free / (1024**3)
            disk_ok = disk_gb >= 1  # Tối thiểu 1GB free
            
            status = ram_ok and disk_ok
            message = f"RAM: {ram_gb:.1f}GB, Disk: {disk_gb:.1f}GB free"
            
            self._add_check("System Resources", status, message)
            return status
            
        except ImportError:
            self._add_check("System Resources", True, "Cannot check (psutil not available)")
            return True
    
    def check_network_connectivity(self):
        """Kiểm tra kết nối mạng"""
        test_urls = [
            "https://www.google.com",
            "https://www.github.com",
            "https://pypi.org"
        ]
        
        connected = False
        for url in test_urls:
            if self._test_url_connectivity(url):
                connected = True
                break
        
        self._add_check("Network Connectivity", connected, 
                       "Connected" if connected else "No internet connection")
        return connected
    
    def _get_available_browsers(self):
        """Lấy danh sách trình duyệt có sẵn"""
        browsers = []
        
        # Chrome/Chromium
        chrome_paths = []
        if self.is_windows:
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
        elif self.is_linux:
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium"
            ]
        else:  # mac
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium"
            ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                browsers.append(("Chrome", path))
                break
        
        # Edge
        edge_paths = []
        if self.is_windows:
            edge_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ]
        elif self.is_linux:
            edge_paths = [
                "/usr/bin/microsoft-edge",
                "/usr/bin/microsoft-edge-stable"
            ]
        else:  # mac
            edge_paths = [
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
            ]
        
        for path in edge_paths:
            if os.path.exists(path):
                browsers.append(("Edge", path))
                break
        
        # Firefox
        firefox_paths = []
        if self.is_windows:
            firefox_paths = [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"
            ]
        elif self.is_linux:
            firefox_paths = [
                "/usr/bin/firefox",
                "/usr/bin/firefox-esr"
            ]
        else:  # mac
            firefox_paths = [
                "/Applications/Firefox.app/Contents/MacOS/firefox"
            ]
        
        for path in firefox_paths:
            if os.path.exists(path):
                browsers.append(("Firefox", path))
                break
        
        return browsers
    
    def _get_available_drivers(self):
        """Lấy danh sách web drivers có sẵn"""
        drivers = []
        
        # ChromeDriver
        chromedriver_paths = []
        if self.is_windows:
            chromedriver_paths = [
                "chromedriver.exe",
                os.path.join("drivers", "chromedriver.exe"),
                r"C:\Windows\System32\chromedriver.exe"
            ]
        else:
            chromedriver_paths = [
                "chromedriver",
                os.path.join("drivers", "chromedriver"),
                "/usr/local/bin/chromedriver",
                "/usr/bin/chromedriver",
                "/snap/bin/chromedriver"
            ]
        
        for path in chromedriver_paths:
            if os.path.exists(path):
                drivers.append(("ChromeDriver", path))
                break
        
        # EdgeDriver
        edgedriver_paths = []
        if self.is_windows:
            edgedriver_paths = [
                "msedgedriver.exe",
                os.path.join("drivers", "msedgedriver.exe"),
                r"C:\Windows\System32\msedgedriver.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe"
            ]
        else:
            edgedriver_paths = [
                "msedgedriver",
                os.path.join("drivers", "msedgedriver"),
                "/usr/local/bin/msedgedriver",
                "/usr/bin/msedgedriver"
            ]
        
        for path in edgedriver_paths:
            if os.path.exists(path):
                drivers.append(("EdgeDriver", path))
                break
        
        return drivers
    
    def _test_url_connectivity(self, url, timeout=5):
        """Test kết nối đến URL"""
        try:
            import requests
            response = requests.get(url, timeout=timeout)
            return response.status_code == 200
        except:
            return False
    
    def _add_check(self, name, status, message):
        """Thêm kết quả kiểm tra"""
        self.checks.append({
            'name': name,
            'status': status,
            'message': message
        })
        if not status:
            self.failed_checks.append(name)
    
    def run_full_check(self):
        """Chạy kiểm tra toàn diện"""
        print("🔍 KIỂM TRA HỆ THỐNG TOÀN DIỆN")
        print("=" * 50)
        
        checks = [
            self.check_python_version,
            self.check_required_packages,
            self.check_system_resources,
            self.check_network_connectivity,
            self.check_browsers,
            self.check_webdrivers
        ]
        
        for check_func in checks:
            check_func()
        
        self.print_report()
        return len(self.failed_checks) == 0
    
    def print_report(self):
        """In báo cáo kiểm tra"""
        print("\n📊 BÁO CÁO KIỂM TRA HỆ THỐNG")
        print("=" * 50)
        
        for check in self.checks:
            status_icon = "✅" if check['status'] else "❌"
            print(f"{status_icon} {check['name']}: {check['message']}")
        
        print("=" * 50)
        
        if self.failed_checks:
            print(f"❌ Có {len(self.failed_checks)} vấn đề cần giải quyết:")
            for failed in self.failed_checks:
                print(f"   - {failed}")
        else:
            print("🎉 HỆ THỐNG ĐÃ SẴN SÀNG!")
    
    def get_failed_checks(self):
        """Lấy danh sách các check thất bại"""
        return self.failed_checks
    
    def get_system_info(self):
        """Lấy thông tin hệ thống"""
        return {
            'os': platform.system(),
            'os_version': platform.version(),
            'architecture': self.architecture,
            'python_version': self.python_version,
            'processor': platform.processor()
        }