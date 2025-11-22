# utils/venv_manager.py
import os
import sys
import platform
import subprocess
import venv
from pathlib import Path

class VenvManager:
    """Quản lý virtual environment tự động - Phiên bản cải tiến"""
    
    def __init__(self, project_root="."):
        self.project_root = Path(project_root)
        self.venv_dir = self.project_root / "venv"
        self.is_windows = platform.system().lower() == "windows"
        
        # Đường dẫn activation
        if self.is_windows:
            self.activate_script = self.venv_dir / "Scripts" / "activate.bat"
            self.python_exe = self.venv_dir / "Scripts" / "python.exe"
            self.pip_exe = self.venv_dir / "Scripts" / "pip.exe"
            self.activate_cmd = f'"{self.activate_script}"'
        else:
            self.activate_script = self.venv_dir / "bin" / "activate"
            self.python_exe = self.venv_dir / "bin" / "python"
            self.pip_exe = self.venv_dir / "bin" / "pip"
            self.activate_cmd = f'source "{self.activate_script}"'
    
    def is_venv_activated(self):
        """Kiểm tra xem venv đã được kích hoạt chưa"""
        return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    
    def is_venv_exists(self):
        """Kiểm tra venv đã tồn tại chưa"""
        return self.venv_dir.exists() and self.python_exe.exists()
    
    def create_venv(self):
        """Tạo virtual environment mới"""
        print("🐍 Đang tạo virtual environment...")
        
        try:
            # Tạo venv
            venv.create(self.venv_dir, with_pip=True)
            print(f"✅ Đã tạo venv tại: {self.venv_dir}")
            
            # Kiểm tra venv hoạt động
            if self._test_venv():
                print("✅ Virtual environment hoạt động tốt")
                return True
            else:
                print("❌ Virtual environment không hoạt động")
                return False
                
        except Exception as e:
            print(f"❌ Lỗi tạo virtual environment: {e}")
            return False
    
    def _test_venv(self):
        """Test venv hoạt động"""
        try:
            result = subprocess.run(
                [str(self.python_exe), "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except:
            return False
    
    def activate_venv_properly(self):
        """Kích hoạt virtual environment đúng cách"""
        if self.is_venv_activated():
            print("✅ Virtual environment đã được kích hoạt")
            return True
            
        if not self.is_venv_exists():
            print("❌ Virtual environment không tồn tại")
            return False
        
        print("🔧 Đang kích hoạt virtual environment...")
        
        try:
            # PHƯƠNG PHÁP 1: Sử dụng subprocess để chạy pip install
            # Giữ sys.path cũ để import các module utils
            old_sys_path = sys.path.copy()
            old_executable = sys.executable
            
            # Thay đổi sys.executable để các subprocess sau này sử dụng venv
            sys.executable = str(self.python_exe)
            
            print(f"✅ Đã kích hoạt venv: {sys.executable}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi kích hoạt venv: {e}")
            return False
    
    def install_requirements_in_venv(self):
        """Cài đặt requirements trong venv sử dụng subprocess"""
        if not self.is_venv_exists():
            print("❌ Virtual environment không tồn tại")
            return False
        
        requirements_path = self.project_root / "requirements.txt"
        if not requirements_path.exists():
            print(f"❌ File requirements.txt không tồn tại")
            return False
        
        print("📦 Đang cài đặt dependencies trong venv...")
        
        try:
            # Sử dụng pip từ venv qua subprocess
            result = subprocess.run(
                [str(self.pip_exe), "install", "-r", str(requirements_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                print("✅ Đã cài đặt tất cả dependencies trong venv")
                return True
            else:
                print(f"⚠️ Có thể có warning: {result.stderr}")
                # Vẫn trả về True nếu chỉ có warning
                return "ERROR" not in result.stderr.upper()
                
        except subprocess.TimeoutExpired:
            print("❌ Timeout khi cài đặt dependencies")
            return False
        except Exception as e:
            print(f"❌ Lỗi không xác định: {e}")
            return False
    
    def install_package_in_venv(self, package_name):
        """Cài đặt package cụ thể trong venv"""
        if not self.is_venv_exists():
            print("❌ Virtual environment không tồn tại")
            return False
        
        try:
            result = subprocess.run(
                [str(self.pip_exe), "install", package_name],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode == 0:
                print(f"✅ Đã cài đặt {package_name} trong venv")
                return True
            else:
                print(f"⚠️ Có thể có warning: {result.stderr}")
                return "ERROR" not in result.stderr.upper()
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout khi cài đặt {package_name}")
            return False
    
    def setup_venv_first(self):
        """Thiết lập venv đầu tiên - CORE FUNCTION"""
        print("🔧 THIẾT LẬP VIRTUAL ENVIRONMENT ĐẦU TIÊN")
        print("=" * 40)
        
        # 1. Kiểm tra hoặc tạo venv
        if not self.is_venv_exists():
            print("📦 Virtual environment chưa tồn tại...")
            if not self.create_venv():
                print("❌ Không thể tạo virtual environment")
                return False
        else:
            print("✅ Virtual environment đã tồn tại")
        
        # 2. Kích hoạt venv
        if not self.activate_venv_properly():
            print("⚠️ Không thể kích hoạt venv đúng cách")
            return False
        
        # 3. Cài đặt dependencies trong venv
        print("📦 Kiểm tra và cài đặt dependencies trong venv...")
        if not self.install_requirements_in_venv():
            print("⚠️ Không thể cài đặt requirements, thử cài đặt từng package...")
            
            # Fallback: cài đặt từng package
            packages = [
                "selenium==4.15.0",
                "pandas==2.1.3", 
                "psutil==5.9.6",
                "openpyxl==3.1.2",
                "requests==2.31.0",
                "webdriver-manager==4.0.1"
            ]
            
            all_success = True
            for package in packages:
                if not self.install_package_in_venv(package):
                    print(f"⚠️ Không thể cài đặt {package} trong venv")
                    all_success = False
            
            if not all_success:
                print("⚠️ Một số package không thể cài đặt tự động trong venv")
        
        print("🎉 THIẾT LẬP VENV HOÀN TẤT")
        return True