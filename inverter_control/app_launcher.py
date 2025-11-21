# app_launcher.py
#!/usr/bin/env python3
"""
Inverter Control System - Universal Launcher
Chạy tự động trên mọi hệ điều hành với tự động cài đặt dependencies và venv
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
    """Hàm chính"""
    try:
        setup_environment()
        
        # Thêm utils vào path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Import các module
        from utils.venv_manager import VenvManager
        from utils.system_checker import SystemChecker
        from utils.dependency_manager import DependencyManager
        
        # 1. THIẾT LẬP VENV
        print("\n🔧 THIẾT LẬP VIRTUAL ENVIRONMENT...")
        venv_manager = VenvManager()
        
        venv_ready = venv_manager.setup_complete_environment()
        if not venv_ready:
            print("⚠️ Có vấn đề với virtual environment, tiếp tục với system Python")
        
        # 2. KIỂM TRA HỆ THỐNG
        print("\n🔍 KIỂM TRA HỆ THỐNG...")
        checker = SystemChecker()
        system_ready = checker.run_full_check()
        
        # 3. CÀI ĐẶT TỰ ĐỘNG NẾU CẦN
        if not system_ready:
            print("\n🔧 TIẾN HÀNH CÀI ĐẶT TỰ ĐỘNG...")
            print("=" * 40)
            
            manager = DependencyManager()
            
            # Cài đặt system dependencies
            if any(check in checker.get_failed_checks() for check in ["Web Browsers", "Web Drivers"]):
                print("\n🔧 Cài đặt system dependencies...")
                if not manager.install_system_dependencies():
                    print("⚠️ Có thể cần cài đặt thủ công một số dependencies")
            
            # Cài đặt web drivers
            if "Web Drivers" in checker.get_failed_checks():
                print("\n🚗 Cài đặt web drivers...")
                if not manager.install_webdrivers():
                    print("⚠️ Có thể cần cài đặt web drivers thủ công")
            
            # Kiểm tra lại sau khi cài đặt
            print("\n🔍 KIỂM TRA LẠI SAU KHI CÀI ĐẶT...")
            system_ready = checker.run_full_check()
        
        # 4. CHẠY ỨNG DỤNG CHÍNH
        if system_ready:
            print("\n🎉 KHỞI CHẠY ỨNG DỤNG CHÍNH...")
            print("=" * 40)
            
            # Chạy trong venv nếu có
            if venv_manager.is_venv_exists():
                print("🐍 Chạy ứng dụng trong virtual environment...")
                success = venv_manager.run_main_directly()
                if not success:
                    print("⚠️ Không thể chạy trong venv, thử với system Python...")
                    # Fallback to system Python
                    try:
                        from main import main as app_main
                        app_main()
                    except Exception as e:
                        print(f"❌ Lỗi khi chạy với system Python: {e}")
            else:
                # Chạy với system Python
                print("🐍 Chạy ứng dụng với system Python...")
                try:
                    from main import main as app_main
                    app_main()
                except Exception as e:
                    print(f"❌ Lỗi khi chạy ứng dụng: {e}")
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