#!/usr/bin/env python3
"""
Entry point chính cho chương trình điều khiển inverter
Phiên bản 0.5.1 - Excel Configuration
"""

from processors.task_processor import TaskProcessor
from config.settings import load_config_from_excel, CONFIG, SYSTEM_URLS as FALLBACK_SYSTEM_URLS

class InteractiveMenu:
    """Lớp quản lý menu tương tác"""
    
    def __init__(self):
        # Load config từ Excel
        excel_system_urls, excel_control_scenarios = load_config_from_excel()
        
        # Sử dụng config từ Excel nếu có, nếu không dùng fallback
        if excel_system_urls and excel_control_scenarios:
            self.SYSTEM_URLS = excel_system_urls
            self.CONTROL_SCENARIOS = excel_control_scenarios
            print("✅ Đang sử dụng cấu hình từ Excel")
        else:
            self.SYSTEM_URLS = FALLBACK_SYSTEM_URLS
            self.CONTROL_SCENARIOS = {
                "1": {"name": "Tắt một số inverter", "requests": {
                    "B3R1": {"action": "OFF", "count": 9},
                    "B4R2": {"action": "OFF", "count": 10},
                    "B5R2": {"action": "OFF", "count": 10},
                    "B8": {"action": "OFF", "count": 4},
                }},
                "2": {"name": "Bật một số inverter", "requests": {
                    "B3R1": {"action": "ON", "count": 9},
                    "B4R2": {"action": "ON", "count": 10},
                    "B5R2": {"action": "ON", "count": 10},
                    "B8": {"action": "ON", "count": 4},
                }},
                "3": {"name": "Bật tất cả inverter", "requests": {
                    "B3R1": {"action": "ON", "count": 9},
                    "B4R2": {"action": "ON", "count": 10},
                    "B5R2": {"action": "ON", "count": 10},
                    "B8": {"action": "ON", "count": 4},
                }}
            }
            print("⚠️ Đang sử dụng cấu hình mặc định")
        
        print(f"🔍 DEBUG: SYSTEM_URLS type: {type(self.SYSTEM_URLS)}")
        print(f"🔍 DEBUG: CONTROL_SCENARIOS type: {type(self.CONTROL_SCENARIOS)}")
        
        if self.SYSTEM_URLS is None:
            print("❌ SYSTEM_URLS là None, không thể khởi động")
            exit(1)
            
        if self.CONTROL_SCENARIOS is None:
            print("❌ CONTROL_SCENARIOS là None, không thể khởi động")
            exit(1)
            
        try:
            self.processor = TaskProcessor(CONFIG, self.SYSTEM_URLS)
            
            # Xây dựng menu scenarios
            self.SCENARIOS = {
                **self.CONTROL_SCENARIOS,  # Scenarios từ Excel hoặc mặc định
                "4": {"name": "Tùy chỉnh", "requests": None},
                "5": {"name": "Xem trạng thái hệ thống", "requests": None},
                "6": {"name": "Quản lý cấu hình Excel", "requests": None},
                "0": {"name": "Thoát chương trình", "requests": None}
            }
            
            print(f"✅ Đã khởi tạo menu với {len(self.SCENARIOS)} scenarios")
            
        except Exception as e:
            print(f"❌ Lỗi khởi tạo InteractiveMenu: {e}")
            import traceback
            traceback.print_exc()
            exit(1)
    
    def display_header(self):
        """Hiển thị header chương trình"""
        print("\n" + "=" * 60)
        print(f"🚀 CHƯƠNG TRÌNH ĐIỀU KHIỂN INVERTER - PHIÊN BẢN {CONFIG['version']}")
        print("=" * 60)
        print("🎯 Excel Configuration - Đọc cấu hình từ file Excel")
        print("⚡ Dynamic Driver Pool - Tối ưu tài nguyên")
        print("📊 Interactive Menu với tính năng Quay lại")
        print("🔄 Xử lý thông minh với retry mechanism")
        print("=" * 60)
    
    def display_menu(self):
        """Hiển thị menu chính"""
        print("\n📋 MENU CHÍNH:")
        
        # Hiển thị scenarios từ Excel
        for key, scenario in self.CONTROL_SCENARIOS.items():
            print(f"{key}. {scenario['name']}")
        
        # Các chức năng khác
        print("4. Tùy chỉnh")
        print("5. Xem trạng thái hệ thống")
        print("6. Quản lý cấu hình Excel")
        print("0. Thoát chương trình")
        print("-" * 40)
    
    def get_user_choice(self):
        """Lấy lựa chọn từ người dùng"""
        max_choice = max([int(k) for k in self.SCENARIOS.keys() if k != '0'])
        
        while True:
            choice = input(f"\n👉 Chọn chức năng (0-{max_choice}): ").strip()
            if choice in self.SCENARIOS:
                return choice
            else:
                print(f"❌ Lựa chọn không hợp lệ! Vui lòng chọn từ 0-{max_choice}")
    
    def custom_scenario_menu(self):
        """Menu tùy chỉnh với quay lại"""
        custom_requests = {}
        
        while True:
            print("\n🎛️ CHẾ ĐỘ TÙY CHỈNH")
            print("=" * 40)
            print("📝 Định dạng: TênStation SốLượng HànhĐộng")
            print("💡 Ví dụ: B3R1 5 OFF")
            print("📋 Lệnh đặc biệt:")
            print("   'list' - Xem danh sách stations")
            print("   'done' - Hoàn thành nhập")
            print("   'back' - Quay lại menu chính")
            print("   'clear' - Xóa tất cả yêu cầu")
            print("   'show' - Xem yêu cầu hiện tại")
            print("-" * 40)
            
            if custom_requests:
                print("📋 Yêu cầu hiện tại:")
                for station, req in custom_requests.items():
                    print(f"   {station}: {req['count']} INV - {req['action']}")
                print("-" * 40)
            
            line = input("Nhập lệnh: ").strip()
            
            if line.lower() == 'back':
                confirm = input("❓ Quay lại menu chính? (y/n): ").strip().lower()
                if confirm == 'y':
                    return None
                else:
                    continue
            
            elif line.lower() == 'done':
                if not custom_requests:
                    print("⚠️ Chưa có yêu cầu nào! Vui lòng thêm yêu cầu trước.")
                    continue
                print("\n📋 Tổng hợp yêu cầu:")
                total_inverters = 0
                for station, req in custom_requests.items():
                    print(f"   ✅ {station}: {req['count']} INV - {req['action']}")
                    total_inverters += req['count']
                print(f"📊 Tổng số inverter: {total_inverters}")
                
                confirm = input("\n✅ Xác nhận thực hiện? (y/n): ").strip().lower()
                if confirm == 'y':
                    return custom_requests
                else:
                    continue
            
            elif line.lower() == 'clear':
                if custom_requests:
                    confirm = input("❓ Xóa tất cả yêu cầu? (y/n): ").strip().lower()
                    if confirm == 'y':
                        custom_requests = {}
                        print("✅ Đã xóa tất cả yêu cầu")
                else:
                    print("ℹ️ Không có yêu cầu nào để xóa")
            
            elif line.lower() == 'show':
                if custom_requests:
                    print("\n📋 Yêu cầu hiện tại:")
                    total_inverters = 0
                    for station, req in custom_requests.items():
                        print(f"   {station}: {req['count']} INV - {req['action']}")
                        total_inverters += req['count']
                    print(f"📊 Tổng số inverter: {total_inverters}")
                else:
                    print("ℹ️ Chưa có yêu cầu nào")
            
            elif line.lower() == 'list':
                self.display_available_stations()
            
            else:
                try:
                    parts = line.split()
                    if len(parts) == 3:
                        station, count, action = parts
                        action = action.upper()
                        
                        if action not in ['ON', 'OFF']:
                            print("❌ Hành động phải là ON hoặc OFF!")
                            continue
                        
                        try:
                            count = int(count)
                            if count <= 0:
                                print("❌ Số lượng phải lớn hơn 0!")
                                continue
                        except ValueError:
                            print("❌ Số lượng phải là số nguyên!")
                            continue
                        
                        # Kiểm tra station có tồn tại không
                        station_exists = False
                        for zone_name, stations in self.SYSTEM_URLS.items():
                            if station in stations:
                                station_exists = True
                                available_inverters = len(stations[station])
                                if count > available_inverters:
                                    print(f"⚠️ Cảnh báo: {station} chỉ có {available_inverters} inverter, bạn yêu cầu {count}")
                                break
                        
                        if not station_exists:
                            print(f"❌ Station '{station}' không tồn tại!")
                            self.display_available_stations()
                            continue
                        
                        custom_requests[station] = {
                            "action": action,
                            "count": count
                        }
                        print(f"✅ Đã thêm: {station} - {count} INV - {action}")
                        
                    else:
                        print("❌ Định dạng không hợp lệ! Ví dụ: B3R1 5 OFF")
                        
                except Exception as e:
                    print(f"❌ Lỗi: {e}")
    
    def display_available_stations(self):
        """Hiển thị danh sách stations có sẵn"""
        print("\n🏭 DANH SÁCH STATIONS:")
        print("-" * 50)
        for zone_name, stations in self.SYSTEM_URLS.items():
            print(f"\n📍 {zone_name}:")
            for station_name, inverters in stations.items():
                inv_count = len(inverters)
                print(f"   🏗️  {station_name}: {inv_count} inverter(s)")
        print("-" * 50)
    
    def system_status_menu(self):
        """Menu xem trạng thái hệ thống"""
        while True:
            print("\n📊 TRẠNG THÁI HỆ THỐNG")
            print("=" * 40)
            print("1. Xem tổng quan hệ thống")
            print("2. Xem chi tiết từng zone")
            print("3. Xem thống kê inverter")
            print("0. Quay lại menu chính")
            print("-" * 40)
            
            choice = input("Chọn chức năng: ").strip()
            
            if choice == '0':
                return
            
            elif choice == '1':
                self.display_system_overview()
            
            elif choice == '2':
                self.display_zone_details()
            
            elif choice == '3':
                self.display_inverter_stats()
            
            else:
                print("❌ Lựa chọn không hợp lệ!")
    
    def display_system_overview(self):
        """Hiển thị tổng quan hệ thống"""
        print("\n📈 TỔNG QUAN HỆ THỐNG")
        print("=" * 50)
        
        total_stations = 0
        total_inverters = 0
        
        for zone_name, stations in self.SYSTEM_URLS.items():
            zone_stations = len(stations)
            zone_inverters = sum(len(inverters) for inverters in stations.values())
            
            total_stations += zone_stations
            total_inverters += zone_inverters
            
            print(f"\n📍 {zone_name}:")
            print(f"   🏗️  Số stations: {zone_stations}")
            print(f"   ⚡ Số inverters: {zone_inverters}")
        
        print("\n" + "=" * 50)
        print(f"📊 TỔNG CỘNG:")
        print(f"   🏗️  Tổng stations: {total_stations}")
        print(f"   ⚡ Tổng inverters: {total_inverters}")
        print("=" * 50)
        
        input("\n👆 Nhấn Enter để tiếp tục...")
    
    def display_zone_details(self):
        """Hiển thị chi tiết từng zone"""
        print("\n🏭 CHI TIẾT TỪNG ZONE")
        print("=" * 60)
        
        for zone_name, stations in self.SYSTEM_URLS.items():
            print(f"\n📍 {zone_name}:")
            print("-" * 40)
            
            for station_name, inverters in stations.items():
                inv_count = len(inverters)
                status_count = {}
                
                for inv_name, inv_info in inverters.items():
                    status = inv_info.get("status", "OK")
                    status_count[status] = status_count.get(status, 0) + 1
                
                status_text = ", ".join([f"{count} {status}" for status, count in status_count.items()])
                print(f"   🏗️  {station_name}: {inv_count} inverter(s) - [{status_text}]")
        
        print("=" * 60)
        input("\n👆 Nhấn Enter để tiếp tục...")
    
    def display_inverter_stats(self):
        """Hiển thị thống kê inverter"""
        print("\n📊 THỐNG KÊ INVERTER")
        print("=" * 50)
        
        status_stats = {}
        total_inverters = 0
        
        for zone_name, stations in self.SYSTEM_URLS.items():
            for station_name, inverters in stations.items():
                for inv_name, inv_info in inverters.items():
                    total_inverters += 1
                    status = inv_info.get("status", "OK")
                    status_stats[status] = status_stats.get(status, 0) + 1
        
        print(f"🔢 Tổng số inverter: {total_inverters}")
        print("\n📈 Phân bố trạng thái:")
        for status, count in status_stats.items():
            percentage = (count / total_inverters) * 100
            print(f"   {status}: {count} inverter ({percentage:.1f}%)")
        
        print("=" * 50)
        input("\n👆 Nhấn Enter để tiếp tục...")
    
    def excel_config_menu(self):
        """Menu quản lý cấu hình Excel"""
        from config.excel_reader import ExcelConfigReader
        
        excel_reader = ExcelConfigReader()
        
        while True:
            print("\n📊 QUẢN LÝ CẤU HÌNH EXCEL")
            print("=" * 40)
            print("1. Kiểm tra file Excel")
            print("2. Xem thông tin cấu hình")
            print("3. Tạo template Excel (nếu chưa có)")
            print("4. Validate scenarios")
            print("0. Quay lại menu chính")
            print("-" * 40)
            
            choice = input("Chọn chức năng: ").strip()
            
            if choice == '0':
                return
            
            elif choice == '1':
                if excel_reader.check_excel_file():
                    print("✅ File Excel hợp lệ và đầy đủ")
                else:
                    print("❌ File Excel có vấn đề")
            
            elif choice == '2':
                self.display_excel_config_info()
            
            elif choice == '3':
                if excel_reader.create_excel_template():
                    print("✅ Đã tạo template Excel thành công")
                else:
                    print("❌ Lỗi khi tạo template")
            
            elif choice == '4':
                self.validate_scenarios()
            
            else:
                print("❌ Lựa chọn không hợp lệ!")
            
            input("\n👆 Nhấn Enter để tiếp tục...")
    
    def display_excel_config_info(self):
        """Hiển thị thông tin cấu hình từ Excel"""
        print("\n📈 THÔNG TIN CẤU HÌNH TỪ EXCEL")
        print("=" * 50)
        
        # Thống kê stations
        total_zones = len(self.SYSTEM_URLS)
        total_stations = sum(len(stations) for stations in self.SYSTEM_URLS.values())
        total_inverters = sum(len(inverters) for stations in self.SYSTEM_URLS.values() for inverters in stations.values())
        
        print(f"🏗️  Số zones: {total_zones}")
        print(f"🏭 Số stations: {total_stations}")
        print(f"⚡ Số inverters: {total_inverters}")
        
        # Thống kê scenarios
        print(f"\n📋 Số scenarios: {len(self.CONTROL_SCENARIOS)}")
        for key, scenario in self.CONTROL_SCENARIOS.items():
            scenario_name = scenario['name']
            station_count = len(scenario['requests'])
            total_inv_in_scenario = sum(req['count'] for req in scenario['requests'].values())
            print(f"   {key}. {scenario_name}: {station_count} stations, {total_inv_in_scenario} inverters")
        
        print("=" * 50)
    
    def validate_scenarios(self):
        """Validate tất cả scenarios"""
        from config.excel_reader import ExcelConfigReader
        
        excel_reader = ExcelConfigReader()
        
        print("\n🔍 VALIDATE SCENARIOS")
        print("=" * 50)
        
        all_valid = True
        
        for key, scenario in self.CONTROL_SCENARIOS.items():
            print(f"\n📋 Scenario: {scenario['name']}")
            errors, warnings = excel_reader.validate_scenario_with_system(
                scenario['requests'], self.SYSTEM_URLS
            )
            
            if errors:
                print("❌ Lỗi:")
                for error in errors:
                    print(f"   - {error}")
                all_valid = False
            
            if warnings:
                print("⚠️ Cảnh báo:")
                for warning in warnings:
                    print(f"   - {warning}")
            
            if not errors and not warnings:
                print("✅ Scenario hợp lệ")
        
        if all_valid:
            print("\n🎉 Tất cả scenarios đều hợp lệ!")
        else:
            print("\n❌ Có scenarios không hợp lệ, vui lòng kiểm tra lại file Excel")
        
        print("=" * 50)
    
    def execute_scenario(self, choice):
        """Thực thi kịch bản được chọn"""
        try:
            scenario = self.SCENARIOS[choice]
            
            if choice == "0":
                print("\n👋 Đang thoát chương trình...")
                return False
            
            elif choice == "4":
                requests = self.custom_scenario_menu()
                if requests is None:  # Người dùng chọn quay lại
                    return True
            
            elif choice == "5":
                self.system_status_menu()
                return True
            
            elif choice == "6":
                self.excel_config_menu()
                return True
            
            else:
                # Scenarios từ Excel (1, 2, 3...)
                requests = scenario["requests"]
                print(f"\n🎯 Đang xử lý: {scenario['name']}")
                print(f"📊 Số lượng stations: {len(requests)}")
                
                # Tính tổng số inverter
                total_inverters = sum(req["count"] for req in requests.values())
                print(f"🔢 Tổng số inverter cần xử lý: {total_inverters}")
                
                # Hiển thị chi tiết
                print("\n📋 Chi tiết:")
                for station, req in requests.items():
                    print(f"   🏗️  {station}: {req['count']} INV - {req['action']}")
                
                confirm = input("\n✅ Xác nhận thực hiện? (y/n): ").strip().lower()
                if confirm != 'y':
                    print("⏹️ Đã hủy thực hiện.")
                    return True
            
            # Thực hiện xử lý
            if choice not in ["5", "6"] and requests:
                print(f"\n🚀 Bắt đầu xử lý {len(requests)} yêu cầu...")
                self.processor.run_parallel_optimized(requests)
            
            input("\n👆 Nhấn Enter để tiếp tục...")
            return True
            
        except Exception as e:
            print(f"❌ Lỗi trong execute_scenario: {e}")
            import traceback
            traceback.print_exc()
            input("\n👆 Nhấn Enter để tiếp tục...")
            return True
    
    def run(self):
        """Chạy menu chính"""
        print("🔄 Khởi động chương trình...")
        
        while True:
            try:
                self.display_header()
                self.display_menu()
                choice = self.get_user_choice()
                
                should_continue = self.execute_scenario(choice)
                if not should_continue:
                    break
                    
            except KeyboardInterrupt:
                print("\n\n⏹️ Chương trình đã được dừng bởi người dùng")
                break
            except Exception as e:
                print(f"❌ Lỗi trong menu chính: {e}")
                import traceback
                traceback.print_exc()
                input("\n👆 Nhấn Enter để tiếp tục...")

def main():
    """Hàm chính - Phiên bản 0.5.1"""
    try:
        menu = InteractiveMenu()
        menu.run()
    except KeyboardInterrupt:
        print("\n\n⏹️ Chương trình đã được dừng bởi người dùng")
    except Exception as e:
        print(f"\n❌ Lỗi không mong muốn: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n👋 Cảm ơn bạn đã sử dụng chương trình!")

if __name__ == "__main__":
    main()