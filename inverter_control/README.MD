# Inverter Control System - Phiên bản 0.5.2

## 📋 Giới thiệu

Hệ thống điều khiển inverter tự động với khả năng đọc cấu hình từ file Excel, quản lý driver thông minh sử dụng Semaphore và hỗ trợ Bật/tắt 1 INV xác định.

## 🆕 Tính năng mới trong v0.5.2

### 🔌 Bật/tắt 1 INV xác định
- **Điều khiển chính xác**: Bật/tắt từng inverter riêng lẻ
- **Định dạng đơn giản**: `[Station-Inverter] [ON/OFF]`
- **Ví dụ**: `B3R1-INV-01 ON`, `B4R2-INV-05 OFF`
- **Auto-complete**: Tự động tìm station và inverter
- **Xác nhận an toàn**: Hiển thị thông tin chi tiết trước khi thực hiện

### 🔍 Tìm kiếm inverter
- **Tìm kiếm thông minh**: Theo tên inverter, station, URL, info
- **Ví dụ**: `INV-01`, `B3R1`, `121`, ...
- **Kết quả chi tiết**: Hiển thị đầy đủ thông tin inverter

### 🎯 Menu mới
📋 MENU CHÍNH:

Tắt một số inverter

Bật một số inverter

Bật tất cả inverter

Bật/tắt 1 inverter ← MỚI: Điều khiển riêng lẻ

Tùy chỉnh

Xem trạng thái hệ thống

Quản lý cấu hình Excel

Thoát chương trình

text

### 📊 Hệ thống trạng thái mở rộng
- **Tìm kiếm inverter**: Menu tìm kiếm thông minh
- **Danh sách chi tiết**: Hiển thị tất cả inverters với đầy đủ thông tin
- **Thống kê nâng cao**: Phân tích trạng thái hệ thống

## 🚀 Tính năng chính

- ✅ **Excel Configuration**: Đọc cấu hình từ file Excel
- ⚡ **Semaphore-based Driver Pool**: Quản lý driver thông minh không dùng sleep
- 🔌 **Bật/tắt 1 INV**: Điều khiển chính xác từng inverter
- 🔍 **Tìm kiếm thông minh**: Tìm inverter theo nhiều tiêu chí
- 🔌 **Bật tất cả INV**: Hỗ trợ toàn bộ hệ thống
- 📊 **Interactive Menu**: Menu tương tác với tính năng Quay lại
- 🔄 **Smart Retry Mechanism**: Xử lý thông minh với cơ chế retry

## 🔧 Cách sử dụng Bật/tắt 1 INV

### 1. Sử dụng Menu chính
Chọn menu: 4
Định dạng: [Station-Inverter] [ON/OFF]
Ví dụ: B3R1-INV-01 ON
Ví dụ: B4R2-INV-05 OFF

text

### 2. Lệnh đặc biệt trong menu
- `list` - Xem danh sách tất cả inverters
- `back` - Quay lại menu chính

### 3. Tìm kiếm inverter
Chọn menu: 6 (Xem trạng thái hệ thống)
Chọn: 5 (Tìm kiếm inverter)
Nhập từ khóa: INV-01, B3R1, 121, ...

text

## 📊 Thống kê hệ thống

**Tổng số inverter**: 143 inverter  
**Tổng số stations**: 14 stations  
**Zones**: 1 zone (Zone B)

### Ví dụ điều khiển:
- `B3R1-INV-01 ON` - Bật inverter đầu tiên của station B3R1
- `B4R2-INV-05 OFF` - Tắt inverter thứ 5 của station B4R2  
- `B8-INV-03 ON` - Bật inverter thứ 3 của station B8

## 🏗️ Cấu trúc dự án
inverter_control/
├── 📁 config/ # Cấu hình hệ thống
│ ├── init.py
│ ├── excel_reader.py # Đọc cấu hình từ Excel
│ ├── selectors.py # CSS Selectors cho web elements
│ ├── settings.py # Cấu hình chung (v0.5.2)
│ └── system_config.py # Cấu hình hệ thống mặc định
├── 📁 core/ # Core components
│ ├── init.py
│ ├── controller.py # Điều khiển inverter (v0.5.2 tối ưu)
│ ├── driver_pool.py # Quản lý driver pool (v0.5.2 - Semaphore)
│ ├── logger.py # Hệ thống logging
│ └── task_queue.py # Hàng đợi thông minh
├── 📁 processors/ # Xử lý tác vụ
│ ├── init.py
│ └── task_processor.py # Xử lý task với rate limiting (v0.5.2)
├── 📁 utils/ # Tiện ích
│ ├── init.py
│ └── helpers.py # Hàm utility hỗ trợ
├── 📄 main.py # Entry point chính
├── 📊 inverter_config.xlsx # File cấu hình Excel
└── 📋 requirements.txt # Thư viện dependencies

text

## 📊 Cấu trúc dữ liệu

### File Excel Configuration

#### Sheet "Stations"
| Cột | Mô tả | Ví dụ |
|-----|-------|-------|
| Zone | Vùng/khu vực | Zone B |
| Station | Trạm inverter | B3R1 |
| Inverter | Tên inverter | INV-01 |
| URL | Địa chỉ IP | 10.10.10.121 |
| Status | Trạng thái | OK |
| Info | Thông tin mô tả | Inverter số 1 |

#### Sheet "Control_Scenarios"
| Cột | Mô tả | Ví dụ |
|-----|-------|-------|
| Station | Trạm cần điều khiển | B3R1 |
| Action | Hành động (ON/OFF) | OFF |
| Count | Số lượng inverter | 4 |

## ⚡ Hiệu suất

### Xử lý Bật/tắt 1 INV:
- **Thời gian**: ~10-15 giây cho 1 inverter
- **Driver sử dụng**: 1 driver
- **Tỷ lệ thành công**: > 98%
- **Phản hồi nhanh**: Xử lý ngay lập tức

### Xử lý Bật tất cả:
- **Tổng thời gian**: ~15-20 phút cho 143 inverter
- **Driver sử dụng**: 8 drivers đồng thời
- **Tỷ lệ thành công**: > 95%

## 🛡️ Safety Features

- **Xác nhận kép** cho mọi thao tác
- **Hiển thị thông tin chi tiết** trước khi thực hiện
- **Kiểm tra tồn tại** station và inverter
- **Log chi tiết** toàn bộ quá trình
- **Error recovery** tự động

---

**Developer**: Inverter Control Team  
**Version**: 0.5.2 - Bật/tắt 1 INV  
**Total Inverters**: 143  
**Stations**: 14  
**Performance**: 8 luồng ổn định