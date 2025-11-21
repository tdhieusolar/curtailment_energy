# test_inverter.py
"""
Script test để debug điều khiển inverter
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.driver_pool import DynamicDriverPool
from core.controller import InverterController
from config.settings import CONFIG

def test_single_inverter():
    """Test điều khiển một inverter"""
    print("🧪 Bắt đầu test inverter...")
    
    driver_pool = DynamicDriverPool(CONFIG)
    driver_pool.initialize_pool(1)
    
    driver = driver_pool.get_driver()
    if not driver:
        print("❌ Không thể lấy driver")
        return
    
    try:
        controller = InverterController(driver, CONFIG)
        
        # Test với một inverter cụ thể
        test_url = "10.10.10.121"  # Thay bằng URL thực tế
        print(f"🔗 Kết nối đến: {test_url}")
        
        # Đăng nhập
        login_success = controller.fast_login(test_url)
        if not login_success:
            print("❌ Đăng nhập thất bại")
            return
        
        print("✅ Đăng nhập thành công")
        
        # Lấy trạng thái hiện tại
        current_status = controller.get_grid_status()
        print(f"📊 Trạng thái hiện tại: {current_status}")
        
        # Test bật/tắt
        test_actions = ["ON", "OFF"]
        for action in test_actions:
            print(f"\n🎯 Thực hiện hành động: {action}")
            success, message = controller.perform_grid_action(action)
            
            if success:
                print(f"✅ {message}")
            else:
                print(f"❌ {message}")
            
            # Chờ giữa các lần test
            import time
            time.sleep(2)
                
    except Exception as e:
        print(f"❌ Lỗi test: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver_pool.return_driver(driver)
        driver_pool.cleanup()

if __name__ == "__main__":
    test_single_inverter()