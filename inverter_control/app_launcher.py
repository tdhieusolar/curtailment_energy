# app_launcher.py
#!/usr/bin/env python3
"""
Inverter Control System - Universal Launcher
TRÌNH TỰ ĐÚNG: Venv → Dependencies → System Check → Run App
"""

import os
import sys
import platform
from pathlib import Path

def setup_environment():
    """Thiết lập môi trường chạy"""
    print("🚀 KHỞI ĐỘNG INVERTER CONTROL SYSTEM")
    print("=" * 50)
    print(f"📋 Hệ điều hành: {platform.system()} {platform.release()}")
    print(f"🐍 Python: {platform.python_version()}")
    print("=" * 50)
    
    # Tạo thư mục cần thiết
    Path("drivers").mkdir(exist_ok=True)
    Path("logs").mkdir(exist_ok=True)

def main():
    """Hàm chính - TRÌNH TỰ ĐÚNG"""
    try:
        setup_environment()
        
        # Thêm utils vào path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Import các module
        from utils.venv_manager import VenvManager
        from utils.system_checker import SystemChecker
        from utils.dependency_manager import DependencyManager
        
        # 1. THIẾT LẬP VENV ĐẦU TIÊN
        print("\n🔧 BƯỚC 1: THIẾT LẬP VIRTUAL ENVIRONMENT...")
        venv_manager = VenvManager()
        
        venv_ready = venv_manager.setup_venv_first()
        if not venv_ready:
            print("⚠️ Không thể thiết lập venv, tiếp tục với system Python")
            # Tạo system checker không có venv
            checker = SystemChecker()
        else:
            # Tạo system checker với venv đã kích hoạt
            checker = SystemChecker(venv_manager=venv_manager)
        
        # 2. KIỂM TRA HỆ THỐNG TRONG MÔI TRƯỜNG HIỆN TẠI (VENV HOẶC SYSTEM)
        print("\n🔍 BƯỚC 2: KIỂM TRA HỆ THỐNG...")
        system_ready = checker.run_full_check()
        
        # 3. CÀI ĐẶT SYSTEM DEPENDENCIES NẾU CẦN
        if not system_ready:
            print("\n🔧 BƯỚC 3: CÀI ĐẶT SYSTEM DEPENDENCIES...")
            print("=" * 40)
            
            manager = DependencyManager()
            
            # Cài đặt system dependencies (trình duyệt, drivers hệ thống)
            if any(check in checker.get_failed_checks() for check in ["Web Browsers", "Web Drivers"]):
                print("\n🔧 Cài đặt system dependencies...")
                if not manager.install_system_dependencies():
                    print("⚠️ Có thể cần cài đặt thủ công một số system dependencies")
            
            # Cài đặt web drivers
            if "Web Drivers" in checker.get_failed_checks():
                print("\n🚗 Cài đặt web drivers...")
                if not manager.install_webdrivers():
                    print("⚠️ Có thể cần cài đặt web drivers thủ công")
            
            # Kiểm tra lại sau khi cài đặt system dependencies
            print("\n🔍 KIỂM TRA LẠI SAU KHI CÀI ĐẶT...")
            system_ready = checker.run_full_check()
        
        # 4. CHẠY ỨNG DỤNG CHÍNH
        if system_ready:
            print("\n🎉 BƯỚC 4: KHỞI CHẠY ỨNG DỤNG CHÍNH...")
            print("=" * 40)
            
            # Import và chạy main
            try:
                # Thêm project root vào path
                sys.path.insert(0, str(Path(__file__).parent))
                
                from main import main as app_main
                print("🚀 Đang khởi chạy ứng dụng...")
                app_main()
                
            except ImportError as e:
                print(f"❌ Lỗi import ứng dụng: {e}")
                return False
            except Exception as e:
                print(f"❌ Lỗi khi chạy ứng dụng: {e}")
                import traceback
                traceback.print_exc()
                return False
                
        else:
            print("\n❌ KHÔNG THỂ KHỞI CHẠY")
            print("📝 Vui lòng giải quyết các vấn đề trên và chạy lại")
            return False
            
        return True
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Ứng dụng đã dừng bởi người dùng")
        return True
    except Exception as e:
        print(f"\n❌ LỖI KHÔNG XÁC ĐỊNH: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n👋 ỨNG DỤNG ĐÃ KẾT THÚC")
    else:
        print("\n💥 ỨNG DỤNG KẾT THÚC VỚI LỖI")
        sys.exit(1)