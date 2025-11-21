# create_excel_fixed.py
import pandas as pd
import os
import sys

# Thêm đường dẫn để import từ config
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.system_config import SYSTEM_URLS

def create_excel_fixed():
    """Tạo file Excel với dữ liệu từ SYSTEM_URLS"""
    
    # Tạo danh sách stations từ SYSTEM_URLS
    stations_data = {
        'Zone': [],
        'Station': [],
        'Inverter': [],
        'URL': [],
        'Status': [],
        'Info': []
    }
    
    # Đọc dữ liệu từ SYSTEM_URLS
    for zone_name, stations in SYSTEM_URLS.items():
        for station_name, inverters in stations.items():
            for inv_name, inv_info in inverters.items():
                stations_data['Zone'].append(zone_name)
                stations_data['Station'].append(station_name)
                stations_data['Inverter'].append(inv_name)
                stations_data['URL'].append(inv_info['url'])
                stations_data['Status'].append(inv_info.get('status', 'OK'))
                stations_data['Info'].append(inv_info.get('info', f'Inverter {inv_name}'))
    
    df_stations = pd.DataFrame(stations_data)
    
    # Tạo DataFrame cho Control_Scenarios - KHÔNG CÓ Scenario_Name
    scenarios_data = {
        'Station': ['B3R1', 'B4R2', 'B5R2', 'B8', 'B3R1', 'B4R2', 'B5R2', 'B8'],
        'Action': ['OFF', 'OFF', 'OFF', 'OFF', 'ON', 'ON', 'ON', 'ON'],
        'Count': [9, 10, 10, 4, 9, 10, 10, 4]
    }
    df_scenarios = pd.DataFrame(scenarios_data)
    
    # Ghi file Excel
    with pd.ExcelWriter('inverter_config.xlsx', engine='openpyxl') as writer:
        df_stations.to_excel(writer, sheet_name='Stations', index=False)
        df_scenarios.to_excel(writer, sheet_name='Control_Scenarios', index=False)
    
    print("✅ Đã tạo file Excel mới: inverter_config.xlsx")
    print("📊 Thông tin file:")
    print(f"   - Stations: {len(df_stations)} inverters")
    print(f"   - Scenarios: {len(df_scenarios)} dòng control")
    
    # Hiển thị thống kê
    print("\n📈 Thống kê Stations:")
    station_counts = df_stations['Station'].value_counts()
    for station, count in station_counts.items():
        print(f"   - {station}: {count} inverters")

if __name__ == "__main__":
    create_excel_fixed()