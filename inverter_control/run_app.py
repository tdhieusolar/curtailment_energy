# run_app.py
#!/usr/bin/env python3
"""
Simple app runner - Fallback solution
"""

import sys
import os
from pathlib import Path

def main():
    print("🚀 KHỞI CHẠY ỨNG DỤNG (Simple Mode)")
    print("=" * 40)
    
    try:
        # Thêm current directory vào path
        sys.path.insert(0, str(Path(__file__).parent))
        
        from main import main as app_main
        app_main()
        return True
        
    except ImportError as e:
        print(f"❌ Lỗi import: {e}")
        print("📝 Kiểm tra file main.py và dependencies")
        return False
    except Exception as e:
        print(f"❌ Lỗi ứng dụng: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)