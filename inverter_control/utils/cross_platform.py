# utils/cross_platform.py
import os
import sys
import platform
import subprocess
from pathlib import Path

class CrossPlatform:
    """Utilities đa nền tảng"""
    
    @staticmethod
    def get_platform_info():
        """Lấy thông tin nền tảng"""
        return {
            'system': platform.system(),
            'release': platform.release(),
            'version': platform.version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor(),
            'python_version': platform.python_version()
        }
    
    @staticmethod
    def run_command(command, shell=False):
        """Chạy command đa nền tảng"""
        try:
            if isinstance(command, str):
                command = [command] if shell else command.split()
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                shell=shell,
                timeout=30
            )
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    @staticmethod
    def get_best_browser():
        """Tìm trình duyệt tốt nhất cho hệ thống"""
        system = platform.system().lower()
        
        if system == "windows":
            browsers = [
                (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe", "edge"),
                (r"C:\Program Files\Microsoft\Edge\Application\msedge.exe", "edge"),
                (r"C:\Program Files\Google\Chrome\Application\chrome.exe", "chrome"),
                (r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe", "chrome"),
            ]
        elif system == "linux":
            browsers = [
                ("/usr/bin/google-chrome", "chrome"),
                ("/usr/bin/google-chrome-stable", "chrome"),
                ("/usr/bin/chromium-browser", "chrome"),
                ("/usr/bin/chromium", "chrome"),
                ("/usr/bin/microsoft-edge", "edge"),
                ("/usr/bin/microsoft-edge-stable", "edge"),
            ]
        else:  # mac
            browsers = [
                ("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome", "chrome"),
                ("/Applications/Chromium.app/Contents/MacOS/Chromium", "chrome"),
                ("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge", "edge"),
            ]
        
        for path, browser_type in browsers:
            if os.path.exists(path):
                return browser_type, path
        
        return None, None
    
    @staticmethod
    def get_best_driver(browser_type):
        """Tìm driver tốt nhất cho trình duyệt"""
        system = platform.system().lower()
        
        if browser_type == "chrome":
            if system == "windows":
                paths = [
                    "chromedriver.exe",
                    "drivers/chromedriver.exe",
                    r"C:\Windows\System32\chromedriver.exe"
                ]
            else:
                paths = [
                    "chromedriver",
                    "drivers/chromedriver", 
                    "/usr/local/bin/chromedriver",
                    "/usr/bin/chromedriver"
                ]
        else:  # edge
            if system == "windows":
                paths = [
                    "msedgedriver.exe",
                    "drivers/msedgedriver.exe",
                    r"C:\Windows\System32\msedgedriver.exe"
                ]
            else:
                paths = [
                    "msedgedriver",
                    "drivers/msedgedriver",
                    "/usr/local/bin/msedgedriver",
                    "/usr/bin/msedgedriver"
                ]
        
        for path in paths:
            if os.path.exists(path):
                return path
        
        return None
    
    @staticmethod
    def create_default_config():
        """Tạo cấu hình mặc định"""
        browser_type, browser_path = CrossPlatform.get_best_browser()
        driver_path = CrossPlatform.get_best_driver(browser_type) if browser_type else None
        
        config = {
            'browser': browser_type or 'auto',
            'browser_path': browser_path or '',
            'driver_path': driver_path or ('msedgedriver.exe' if platform.system() == 'Windows' else 'msedgedriver'),
            'headless': True,
            'timeout': 30
        }
        
        # Lưu cấu hình
        config_content = f"""# Auto-generated configuration
BROWSER = "{config['browser']}"
BROWSER_PATH = "{config['browser_path']}"
DRIVER_PATH = "{config['driver_path']}"
HEADLESS = {config['headless']}
TIMEOUT = {config['timeout']}
"""
        
        with open("browser_config.py", "w", encoding="utf-8") as f:
            f.write(config_content)
        
        return config