# app_launcher.py
#!/usr/bin/env python3
"""
Inverter Control System - Universal Launcher
CÀI ĐẶT THÔNG MINH: Chỉ cài đặt khi cần thiết
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
    """Hàm chính - CÀI ĐẶT THÔNG MINH"""
    try:
        setup_environment()
        
        # Thêm utils vào path
        sys.path.insert(0, str(Path(__file__).parent))
        
        # Import các module
        from utils.venv_manager import VenvManager
        from utils.system_checker import SystemChecker
        from utils.dependency_manager import DependencyManager
        
        # 1. KIỂM TRA HỆ THỐNG BAN ĐẦU (trong system Python)
        print("\n🔍 BƯỚC 1: KIỂM TRA HỆ THỐNG BAN ĐẦU...")
        initial_checker = SystemChecker()
        initial_status = initial_checker.run_full_check()
        
        # 2. THIẾT LẬP VENV THÔNG MINH
        print("\n🔧 BƯỚC 2: THIẾT LẬP VIRTUAL ENVIRONMENT THÔNG MINH...")
        venv_manager = VenvManager()
        
        # Thiết lập venv với thông tin từ system checker
        venv_ready = venv_manager.setup_venv_smart(initial_checker)
        
        if not venv_ready:
            print("⚠️ Không thể thiết lập venv, tiếp tục với system Python")
            final_checker = initial_checker
        else:
            # 3. KIỂM TRA LẠI TRONG VENV
            print("\n🔍 BƯỚC 3: KIỂM TRA HỆ THỐNG TRONG VENV...")
            final_checker = SystemChecker(venv_manager=venv_manager)
            final_status = final_checker.run_full_check()
        
        # 4. CÀI ĐẶT SYSTEM DEPENDENCIES NẾU CẦN
        system_ready = final_checker.run_full_check() if 'final_checker' in locals() else initial_status
        
        if not system_ready:
            print("\n🔧 BƯỚC 4: CÀI ĐẶT SYSTEM DEPENDENCIES (NẾU CẦN)...")
            print("=" * 40)
            
            manager = DependencyManager()
            
            # Chỉ cài đặt system dependencies nếu thực sự cần
            failed_checks = final_checker.get_failed_checks()
            
            if "Web Browsers" in failed_checks:
                print("\n🔧 Trình duyệt không tìm thấy, đang cài đặt...")
                if not manager.install_system_dependencies():
                    print("⚠️ Có thể cần cài đặt thủ công trình duyệt")
            
            if "Web Drivers" in failed_checks:
                print("\n🚗 Web drivers không tìm thấy, đang cài đặt...")
                if not manager.install_webdrivers():
                    print("⚠️ Có thể cần cài đặt thủ công web drivers")
            
            # Kiểm tra lại sau khi cài đặt system dependencies
            print("\n🔍 KIỂM TRA LẠI SAU KHI CÀI ĐẶT...")
            system_ready = final_checker.run_full_check()
        
        # 5. CHẠY ỨNG DỤNG CHÍNH
        if system_ready:
            print("\n🎉 BƯỚC 5: KHỞI CHẠY ỨNG DỤNG CHÍNH...")
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