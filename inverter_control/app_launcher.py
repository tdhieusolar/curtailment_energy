# app_launcher.py (Phiên bản rút gọn)
import sys
import os
from pathlib import Path

# Thêm đường dẫn để import utils
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print(f"🐍 Python Runtime: {sys.executable}")
    
    # Kiểm tra an toàn: Đảm bảo đang chạy trong Venv
    # (Dù launch.sh đã làm, nhưng check lại không thừa)
    is_venv = (sys.prefix != sys.base_prefix)
    if not is_venv:
        print("⚠️ CẢNH BÁO: Bạn đang KHÔNG chạy trong môi trường ảo!")
        print("   Vui lòng chạy file launch.sh hoặc launch.bat")
        # Tùy bạn: có thể return False để ép buộc dùng launch.sh
    
    try:
        from utils.system_checker import SystemChecker
        from utils.dependency_manager import DependencyManager
        
        # 1. Kiểm tra lại lần cuối (Browser, Driver, v.v.)
        checker = SystemChecker()
        if not checker.run_full_check():
            print("🔧 Đang khắc phục các vấn đề còn thiếu...")
            dep_manager = DependencyManager()
            
            # Logic cài Chrome/Driver nếu thiếu...
            # (Copy logic cũ của bạn vào đây)
            
        # 2. Chạy Main App
        print("\n🚀 Starting Main Application...")
        from main import main as app_main
        app_main()
        return True

    except ImportError as e:
        print(f"❌ Lỗi thư viện: {e}")
        print("👉 Hãy chạy: pip install -r requirements.txt")
        return False
    except Exception as e:
        print(f"❌ Lỗi không xác định: {e}")
        return False

if __name__ == "__main__":
    main()