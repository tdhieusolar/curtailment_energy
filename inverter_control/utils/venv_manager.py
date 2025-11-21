# utils/venv_manager.py
import os
import sys
import platform
import subprocess
import venv
from pathlib import Path

class VenvManager:
    """Quản lý virtual environment tự động"""
    
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
    
    def activate_venv_for_current_process(self):
        """Kích hoạt virtual environment cho process hiện tại"""
        if self.is_venv_activated():
            print("✅ Virtual environment đã được kích hoạt")
            return True
            
        if not self.is_venv_exists():
            print("❌ Virtual environment không tồn tại")
            return False
        
        print("🔧 Đang kích hoạt virtual environment cho process hiện tại...")
        
        try:
            # Thêm venv vào sys.path
            if self.is_windows:
                site_packages = self.venv_dir / "Lib" / "site-packages"
            else:
                site_packages = self.venv_dir / "lib" / f"python{sys.version_info.major}.{sys.version_info.minor}" / "site-packages"
            
            if site_packages.exists():
                sys.path.insert(0, str(site_packages))
            
            # Thay thế sys.executable và sys.prefix
            old_executable = sys.executable
            sys.executable = str(self.python_exe)
            sys.prefix = str(self.venv_dir)
            
            print(f"✅ Đã kích hoạt venv: {sys.executable}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi kích hoạt venv: {e}")
            return False
    
    def install_requirements(self, requirements_file="requirements.txt"):
        """Cài đặt requirements trong venv"""
        if not self.is_venv_exists():
            print("❌ Virtual environment không tồn tại")
            return False
        
        requirements_path = self.project_root / requirements_file
        if not requirements_path.exists():
            print(f"❌ File {requirements_file} không tồn tại")
            return False
        
        print("📦 Đang cài đặt dependencies từ requirements.txt...")
        
        try:
            # Sử dụng pip từ venv
            result = subprocess.run(
                [str(self.pip_exe), "install", "-r", str(requirements_path)],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )
            
            if result.returncode == 0:
                print("✅ Đã cài đặt tất cả dependencies")
                return True
            else:
                print(f"⚠️ Có thể có warning khi cài đặt: {result.stderr}")
                # Vẫn trả về True nếu chỉ có warning
                return "ERROR" not in result.stderr.upper()
                
        except subprocess.TimeoutExpired:
            print("❌ Timeout khi cài đặt dependencies")
            return False
        except Exception as e:
            print(f"❌ Lỗi không xác định: {e}")
            return False
    
    def install_package(self, package_name):
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
                print(f"✅ Đã cài đặt {package_name}")
                return True
            else:
                print(f"⚠️ Có thể có warning khi cài đặt {package_name}: {result.stderr}")
                return "ERROR" not in result.stderr.upper()
                
        except subprocess.TimeoutExpired:
            print(f"❌ Timeout khi cài đặt {package_name}")
            return False
    
    def get_venv_python_path(self):
        """Lấy đường dẫn Python trong venv"""
        return str(self.python_exe) if self.is_venv_exists() else sys.executable
    
    def run_main_directly(self):
        """Chạy main.py trực tiếp trong process hiện tại sau khi kích hoạt venv"""
        if not self.is_venv_exists():
            print("❌ Virtual environment không tồn tại")
            return False
        
        try:
            # Kích hoạt venv cho process hiện tại
            if not self.activate_venv_for_current_process():
                return False
            
            # Import và chạy main
            print("🔧 Đang import main module...")
            
            # Thêm project root vào sys.path
            sys.path.insert(0, str(self.project_root))
            
            # Import main
            from main import main as app_main
            
            print("🎯 Đang khởi chạy ứng dụng chính...")
            app_main()
            return True
            
        except ImportError as e:
            print(f"❌ Lỗi import: {e}")
            return False
        except Exception as e:
            print(f"❌ Lỗi khi chạy ứng dụng: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def setup_complete_environment(self):
        """Thiết lập môi trường hoàn chỉnh: venv + dependencies"""
        print("🔧 THIẾT LẬP MÔI TRƯỜNG HOÀN CHỈNH")
        print("=" * 40)
        
        # 1. Kiểm tra hoặc tạo venv
        if not self.is_venv_exists():
            print("📦 Virtual environment chưa tồn tại...")
            if not self.create_venv():
                return False
        else:
            print("✅ Virtual environment đã tồn tại")
        
        # 2. Cài đặt dependencies
        print("📦 Kiểm tra và cài đặt dependencies...")
        if not self.install_requirements():
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
                if not self.install_package(package):
                    print(f"⚠️ Không thể cài đặt {package}")
                    all_success = False
            
            if not all_success:
                print("⚠️ Một số package không thể cài đặt tự động")
        
        print("🎉 THIẾT LẬP MÔI TRƯỜNG HOÀN TẤT")
        return True