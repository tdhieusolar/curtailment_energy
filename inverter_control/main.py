#!/usr/bin/env python3
"""
Entry point chính cho chương trình điều khiển inverter
Phiên bản 0.4.1 - Dynamic Driver Pool
"""

from processors.task_processor import TaskProcessor
from config.settings import CONTROL_REQUESTS_OFF, CONTROL_REQUESTS_ON, ON_ALL

def main():
    """Hàm chính - Phiên bản 0.4.1"""
    processor = TaskProcessor()
    
    SCENARIOS = {
        "1": {"name": "Tắt một số inverter", "requests": CONTROL_REQUESTS_OFF},
        "2": {"name": "Bật một số inverter", "requests": CONTROL_REQUESTS_ON},
        "3": {"name": "Bật tất cả inverter", "requests": ON_ALL},
        "4": {"name": "Tùy chỉnh", "requests": None}
    }
    
    print("🚀 CHƯƠNG TRÌNH ĐIỀU KHIỂN INVERTER - PHIÊN BẢN 0.4.1")
    print("=" * 50)
    print("🎯 Dynamic Driver Pool - Tối ưu tài nguyên")
    print("⚡ Chỉ tạo driver khi cần thiết")
    print("📊 Tính toán số driver dựa trên số lượng INV")
    print("🔄 Xử lý thông minh với retry mechanism")
    print("=" * 50)
    
    for key, scenario in SCENARIOS.items():
        print(f"{key}. {scenario['name']}")
    
    choice = input("\nChọn kịch bản (1-4): ").strip()
    
    if choice in SCENARIOS:
        if choice == "4":
            custom_requests = {}
            print("\n🎛️ Chế độ tùy chỉnh")
            print("📝 Định dạng: TênStation SốLượng HànhĐộng")
            print("💡 Ví dụ: B3R1 5 OFF")
            print("⏹️ Nhập 'done' để kết thúc")
            
            while True:
                line = input("Nhập: ").strip()
                if line.lower() == 'done':
                    break
                try:
                    parts = line.split()
                    if len(parts) == 3:
                        station, count, action = parts
                        custom_requests[station] = {
                            "action": action.upper(),
                            "count": int(count)
                        }
                        print(f"✅ Đã thêm: {station} - {count} INV - {action}")
                    else:
                        print("❌ Định dạng không hợp lệ! Ví dụ: B3R1 5 OFF")
                except ValueError:
                    print("❌ Số lượng phải là số nguyên!")
            
            requests = custom_requests
        else:
            requests = SCENARIOS[choice]["requests"]
        
        print(f"\n🎯 Đang xử lý: {SCENARIOS[choice]['name']}")
        print(f"📊 Số lượng yêu cầu: {len(requests)}")
        
        confirm = input("✅ Xác nhận thực hiện? (y/n): ").strip().lower()
        if confirm == 'y':
            processor.run_parallel_optimized(requests)
        else:
            print("⏹️ Đã hủy thực hiện.")
    else:
        print("❌ Lựa chọn không hợp lệ!")

if __name__ == "__main__":
    main()