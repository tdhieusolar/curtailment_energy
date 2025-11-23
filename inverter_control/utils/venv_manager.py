# utils/venv_manager.py
import os
import sys
import platform
import subprocess
import venv
from pathlib import Path

class VenvManager:
    """Quản lý virtual environment với cài đặt thông minh"""
    
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
            # Thay đổi sys.executable để các subprocess sau này sử dụng venv
            sys.executable = str(self.python_exe)
            
            print(f"✅ Đã kích hoạt venv: {sys.executable}")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi kích hoạt venv: {e}")
            return False
    
    def install_packages_smart(self, packages_to_install):
        """Cài đặt packages thông minh từ requirements.txt"""

        if not packages_to_install:
            print("✅ Tất cả packages đã được cài đặt với phiên bản phù hợp")
            return True

        if not self.is_venv_exists():
            print("❌ Virtual environment không tồn tại")
            return False

        print(f"📦 Đang cài đặt {len(packages_to_install)} packages từ requirements.txt...")

        success_count = 0
        for package, required_spec in packages_to_install.items():
            print(f"🔧 Đang xử lý {package}...")

            try:
                if required_spec:
                    install_spec = f"{package}{required_spec}"
                else:
                    install_spec = package

                result = subprocess.run(
                    [str(self.pip_exe), "install", install_spec],
                    capture_output=True,
                    text=True,
                    timeout=120
                )

                if result.returncode == 0:
                    print(f"✅ Đã cài đặt {install_spec}")
                    success_count += 1
                else:
                    print(f"⚠️ Có vấn đề với {package}: {result.stderr}")

            except subprocess.TimeoutExpired:
                print(f"❌ Timeout khi cài đặt {package}")
            except Exception as e:
                print(f"❌ Lỗi khi cài đặt {package}: {e}")

        print(f"📊 Kết quả: {success_count}/{len(packages_to_install)} packages thành công")
        return success_count > 0



    def install_requirements_smart(self, system_checker):
        """Cài đặt requirements thông minh dựa trên kết quả kiểm tra"""
        if not self.is_venv_exists():
            print("❌ Virtual environment không tồn tại")
            return False
        
        # Lấy packages cần cài đặt từ system checker
        packages_to_install = system_checker.get_packages_to_install()
        
        if not packages_to_install:
            print("✅ Tất cả packages đã được cài đặt với phiên bản phù hợp")
            return True
        
        return self.install_packages_smart(packages_to_install)
    
    def setup_venv_smart(self, system_checker):
        """Thiết lập venv thông minh - chỉ cài đặt khi cần"""
        print("🔧 THIẾT LẬP VIRTUAL ENVIRONMENT THÔNG MINH")
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
        
        # 3. Cài đặt packages thông minh
        print("📦 Kiểm tra và cài đặt packages thông minh...")
        success = self.install_requirements_smart(system_checker)
        
        if success:
            print("🎉 THIẾT LẬP VENV THÔNG MINH HOÀN TẤT")
        else:
            print("⚠️ Có vấn đề khi cài đặt packages")
        
        return success