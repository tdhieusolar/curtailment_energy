# config/excel_reader.py
"""
Đọc cấu hình từ file Excel - Phiên bản 0.5.1
"""

import pandas as pd
import os

class ExcelConfigReader:
    """Lớp đọc cấu hình từ file Excel"""
    
    def __init__(self, excel_file_path="inverter_config.xlsx"):
        self.excel_file_path = excel_file_path
        self.logger = self._create_logger()
        self.required_sheets = ['Stations', 'Control_Scenarios']
    
    def _create_logger(self):
        """Tạo logger cục bộ để tránh circular import"""
        import logging
        import sys
        
        class SimpleLogger:
            def __init__(self):
                logging.basicConfig(
                    level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - [ExcelReader] - %(message)s",
                    handlers=[
                        logging.StreamHandler(sys.stdout)
                    ]
                )
                self.logger = logging.getLogger(__name__)
            
            def log_info(self, message):
                self.logger.info(f"ℹ️ {message}")
            
            def log_error(self, message):
                self.logger.error(f"❌ {message}")
            
            def log_warning(self, message):
                self.logger.warning(f"⚠️ {message}")
        
        return SimpleLogger()
    
    def check_excel_file(self):
        """Kiểm tra file Excel tồn tại và cấu trúc"""
        if not os.path.exists(self.excel_file_path):
            self.logger.log_error(f"File Excel không tồn tại: {self.excel_file_path}")
            return False
        
        try:
            # Kiểm tra các sheet required
            excel_file = pd.ExcelFile(self.excel_file_path)
            missing_sheets = []
            
            for sheet in self.required_sheets:
                if sheet not in excel_file.sheet_names:
                    missing_sheets.append(sheet)
            
            if missing_sheets:
                self.logger.log_error(f"Thiếu sheets: {', '.join(missing_sheets)}")
                return False
            
            self.logger.log_info(f"✅ File Excel hợp lệ: {self.excel_file_path}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Lỗi kiểm tra file Excel: {e}")
            return False
    
    def read_stations_config(self):
        """Đọc cấu hình stations từ Excel"""
        try:
            df = pd.read_excel(self.excel_file_path, sheet_name='Stations')
            
            # Kiểm tra cột bắt buộc
            required_columns = ['Zone', 'Station', 'Inverter', 'URL', 'Status']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.log_error(f"Thiếu cột trong sheet Stations: {', '.join(missing_columns)}")
                return None
            
            # Xây dựng cấu trúc SYSTEM_URLS
            system_urls = {}
            
            for _, row in df.iterrows():
                zone = row['Zone']
                station = row['Station']
                inverter = row['Inverter']
                url = row['URL']
                status = row.get('Status', 'OK')
                info = row.get('Info', f'Inverter {inverter}')
                
                if zone not in system_urls:
                    system_urls[zone] = {}
                
                if station not in system_urls[zone]:
                    system_urls[zone][station] = {}
                
                system_urls[zone][station][inverter] = {
                    "url": url,
                    "info": info,
                    "status": status
                }
            
            self.logger.log_info(f"✅ Đã đọc cấu hình {len(system_urls)} zones từ Excel")
            return system_urls
            
        except Exception as e:
            self.logger.log_error(f"Lỗi đọc stations từ Excel: {e}")
            return None
    
    def read_control_scenarios(self):
        """Đọc scenarios điều khiển từ Excel - KHÔNG CÓ Scenario_Name"""
        try:
            df = pd.read_excel(self.excel_file_path, sheet_name='Control_Scenarios')
            
            # Kiểm tra cột bắt buộc (đã bỏ Scenario_Name)
            required_columns = ['Station', 'Action', 'Count']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.logger.log_error(f"Thiếu cột trong sheet Control_Scenarios: {', '.join(missing_columns)}")
                return {}
            
            # Xây dựng scenarios - Tự động phân loại ON/OFF
            scenarios = {
                "Tắt một số inverter": {},
                "Bật một số inverter": {}
            }
            
            for _, row in df.iterrows():
                station = row['Station']
                action = row['Action']
                count = row['Count']
                
                # Phân loại theo action
                if action == 'OFF':
                    scenario_name = "Tắt một số inverter"
                elif action == 'ON':
                    scenario_name = "Bật một số inverter"
                else:
                    self.logger.log_warning(f"Action không hợp lệ: {action}, bỏ qua")
                    continue
                
                scenarios[scenario_name][station] = {
                    "action": action,
                    "count": count
                }
            
            self.logger.log_info(f"✅ Đã đọc {len(scenarios)} scenarios từ Excel")
            return scenarios
            
        except Exception as e:
            self.logger.log_error(f"Lỗi đọc scenarios từ Excel: {e}")
            return {}
    
    def get_available_scenarios(self):
        """Lấy danh sách scenarios có sẵn"""
        scenarios = self.read_control_scenarios()
        if not scenarios:
            self.logger.log_warning("⚠️ Không có scenarios nào trong file Excel")
            return {}
        
        scenario_list = {}
        index = 1
        
        for scenario_name, requests in scenarios.items():
            if requests:  # Chỉ thêm scenario nếu có requests
                scenario_list[str(index)] = {
                    "name": scenario_name,
                    "requests": requests
                }
                index += 1
        
        self.logger.log_info(f"✅ Đã tạo {len(scenario_list)} scenarios cho menu")
        return scenario_list
    
    def validate_scenario_with_system(self, scenario_requests, system_urls):
        """Validate scenario với system config"""
        errors = []
        warnings = []
        
        for station, request in scenario_requests.items():
            # Kiểm tra station tồn tại
            station_exists = False
            for zone_name, stations in system_urls.items():
                if station in stations:
                    station_exists = True
                    
                    # Kiểm tra số lượng inverter
                    available_inverters = len(stations[station])
                    requested_count = request["count"]
                    
                    if requested_count > available_inverters:
                        warnings.append(f"Station {station}: Yêu cầu {requested_count} nhưng chỉ có {available_inverters} inverter")
                    
                    # Kiểm tra action hợp lệ
                    action = request["action"]
                    if action not in ['ON', 'OFF']:
                        errors.append(f"Station {station}: Action '{action}' không hợp lệ (phải là ON hoặc OFF)")
                    
                    break
            
            if not station_exists:
                errors.append(f"Station '{station}' không tồn tại trong hệ thống")
        
        return errors, warnings

    def create_excel_template(self):
        """Tạo file Excel template với format mới"""
        try:
            # Tạo DataFrame cho Stations
            stations_data = {
                'Zone': ['Zone B', 'Zone B', 'Zone B', 'Zone B', 'Zone B', 'Zone B', 'Zone B', 'Zone B'],
                'Station': ['B3R1', 'B3R1', 'B3R1', 'B4R2', 'B4R2', 'B5R2', 'B5R2', 'B8'],
                'Inverter': ['INV-01', 'INV-02', 'INV-03', 'INV-01', 'INV-02', 'INV-01', 'INV-02', 'INV-01'],
                'URL': ['10.10.10.121', '10.10.10.122', '10.10.10.123', '10.10.10.131', '10.10.10.132', 
                       '10.10.10.151', '10.10.10.152', '10.10.10.201'],
                'Status': ['OK', 'OK', 'OK', 'OK', 'OK', 'OK', 'OK', 'OK'],
                'Info': ['Inverter số 1', 'Inverter số 2', 'Inverter số 3', 'Inverter số 1', 'Inverter số 2', 
                        'Inverter số 1', 'Inverter số 2', 'Inverter số 1']
            }
            df_stations = pd.DataFrame(stations_data)
            
            # Tạo DataFrame cho Control_Scenarios - KHÔNG CÓ Scenario_Name
            scenarios_data = {
                'Station': ['B3R1', 'B4R2', 'B5R2', 'B8', 'B3R1', 'B4R2', 'B5R2', 'B8'],
                'Action': ['OFF', 'OFF', 'OFF', 'OFF', 'ON', 'ON', 'ON', 'ON'],
                'Count': [9, 10, 10, 4, 9, 10, 10, 4]
            }
            df_scenarios = pd.DataFrame(scenarios_data)
            
            # Ghi file Excel
            with pd.ExcelWriter(self.excel_file_path, engine='openpyxl') as writer:
                df_stations.to_excel(writer, sheet_name='Stations', index=False)
                df_scenarios.to_excel(writer, sheet_name='Control_Scenarios', index=False)
            
            self.logger.log_info(f"✅ Đã tạo file template: {self.excel_file_path}")
            return True
            
        except Exception as e:
            self.logger.log_error(f"Lỗi tạo template Excel: {e}")
            return False