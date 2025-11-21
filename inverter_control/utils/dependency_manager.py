# utils/dependency_manager.py
import os
import sys
import subprocess
import importlib
import platform
from pathlib import Path

class DependencyManager:
    """Quản lý dependencies và cài đặt tự động"""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.is_windows = self.system == "windows"
        self.is_linux = self.system == "linux"
        self.is_mac = self.system == "darwin"
    
    def install_python_packages(self, packages=None):
        """Cài đặt Python packages"""
        if packages is None:
            packages = [
                'selenium==4.15.0',
                'pandas==2.1.3',
                'psutil==5.9.6', 
                'openpyxl==3.1.2',
                'requests==2.31.0'
            ]
        
        print("📦 Cài đặt Python packages...")
        
        for package in packages:
            try:
                print(f"🔧 Đang cài đặt {package}...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ Đã cài đặt {package}")
            except subprocess.CalledProcessError as e:
                print(f"❌ Lỗi cài đặt {package}: {e}")
                return False
        
        return True
    
    def install_system_dependencies(self):
        """Cài đặt system dependencies"""
        print("🔧 Cài đặt system dependencies...")
        
        if self.is_linux:
            return self._install_linux_dependencies()
        elif self.is_mac:
            return self._install_mac_dependencies()
        elif self.is_windows:
            return self._install_windows_dependencies()
        else:
            print("⚠️ Hệ điều hành không được hỗ trợ")
            return False
    
    def _install_linux_dependencies(self):
        """Cài đặt dependencies cho Linux"""
        try:
            # Cập nhật package manager
            print("🔄 Cập nhật package manager...")
            subprocess.run(["sudo", "apt", "update"], check=True)
            
            # Cài đặt dependencies
            packages = [
                "chromium-browser",
                "chromium-chromedriver", 
                "python3-pip",
                "python3-venv",
                "wget",
                "curl"
            ]
            
            print("📦 Cài đặt system packages...")
            subprocess.run(["sudo", "apt", "install", "-y"] + packages, check=True)
            
            print("✅ Đã cài đặt system dependencies")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Lỗi cài đặt system dependencies: {e}")
            return False
    
    def _install_windows_dependencies(self):
        """Cài đặt dependencies cho Windows"""
        try:
            # Kiểm tra và cài đặt Chocolatey (package manager cho Windows)
            if not self._is_chocolatey_installed():
                print("📦 Cài đặt Chocolatey...")
                install_cmd = (
                    "Set-ExecutionPolicy Bypass -Scope Process -Force; "
                    "[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
                    "iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
                )
                subprocess.run(["powershell", "-Command", install_cmd], check=True)
            
            # Cài đặt packages qua Chocolatey
            print("📦 Cài đặt packages qua Chocolatey...")
            packages = ["googlechrome", "python", "git"]
            
            for package in packages:
                subprocess.run(["choco", "install", package, "-y"], check=True)
            
            print("✅ Đã cài đặt system dependencies")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Lỗi cài đặt system dependencies: {e}")
            return False
    
    def _install_mac_dependencies(self):
        """Cài đặt dependencies cho Mac"""
        try:
            # Kiểm tra Homebrew
            if not self._is_homebrew_installed():
                print("📦 Cài đặt Homebrew...")
                install_url = "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh"
                subprocess.run(['/bin/bash', '-c', f'curl -fsSL {install_url} | bash'], check=True)
            
            # Cài đặt packages
            print("📦 Cài đặt packages qua Homebrew...")
            packages = ["chromium", "python", "git"]
            
            for package in packages:
                subprocess.run(["brew", "install", package], check=True)
            
            print("✅ Đã cài đặt system dependencies")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Lỗi cài đặt system dependencies: {e}")
            return False
    
    def _is_chocolatey_installed(self):
        """Kiểm tra Chocolatey đã cài đặt chưa"""
        try:
            subprocess.run(["choco", "--version"], capture_output=True)
            return True
        except:
            return False
    
    def _is_homebrew_installed(self):
        """Kiểm tra Homebrew đã cài đặt chưa"""
        try:
            subprocess.run(["brew", "--version"], capture_output=True)
            return True
        except:
            return False
    
    def install_webdrivers(self):
        """Cài đặt web drivers"""
        print("🚗 Cài đặt web drivers...")
        
        # Sử dụng webdriver-manager
        try:
            # Cài đặt webdriver-manager trước
            subprocess.check_call([sys.executable, "-m", "pip", "install", "webdriver-manager"])
            
            # Test cài đặt ChromeDriver
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.microsoft import EdgeDriverManager
            
            print("📥 Đang tải ChromeDriver...")
            chrome_path = ChromeDriverManager().install()
            print(f"✅ ChromeDriver: {chrome_path}")
            
            print("📥 Đang tải EdgeDriver...")
            edge_path = EdgeDriverManager().install()
            print(f"✅ EdgeDriver: {edge_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Lỗi cài đặt web drivers: {e}")
            print("🔧 Thử phương pháp manual...")
            return self._install_webdrivers_manual()
    
    def _install_webdrivers_manual(self):
        """Cài đặt web drivers manual"""
        try:
            # Tạo thư mục drivers
            drivers_dir = Path("drivers")
            drivers_dir.mkdir(exist_ok=True)
            
            if self.is_windows:
                # Tải ChromeDriver manual
                chrome_url = "https://chromedriver.storage.googleapis.com/114.0.5735.90/chromedriver_win32.zip"
                self._download_and_extract(chrome_url, drivers_dir / "chromedriver.exe")
                
                # Tải EdgeDriver manual  
                edge_url = "https://msedgedriver.azureedge.net/114.0.1823.58/edgedriver_win64.zip"
                self._download_and_extract(edge_url, drivers_dir / "msedgedriver.exe")
                
            else:
                # Linux/Mac - sử dụng system package
                if self.is_linux:
                    subprocess.run(["sudo", "apt", "install", "-y", "chromium-chromedriver"], check=True)
                else:  # mac
                    subprocess.run(["brew", "install", "chromedriver"], check=True)
            
            print("✅ Đã cài đặt web drivers manual")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi cài đặt manual: {e}")
            return False
    
    def _download_and_extract(self, url, output_path):
        """Tải và giải nén file"""
        import requests
        import zipfile
        import io
        
        print(f"📥 Đang tải {url}...")
        response = requests.get(url)
        response.raise_for_status()
        
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_file:
            # Tìm file thực thi trong zip
            for name in zip_file.namelist():
                if name.endswith(('.exe', '')) and not name.endswith('/'):
                    with zip_file.open(name) as source, open(output_path, 'wb') as target:
                        shutil.copyfileobj(source, target)
                    
                    # Cấp quyền thực thi (Linux/Mac)
                    if not self.is_windows:
                        os.chmod(output_path, 0o755)
                    
                    print(f"✅ Đã giải nén: {output_path}")
                    break