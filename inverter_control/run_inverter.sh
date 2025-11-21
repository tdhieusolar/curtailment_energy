#!/bin/bash

echo "🚀 Khởi động Inverter Control System v0.5.3..."
echo "================================================"

VENV_DIR="venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Kiểm tra và kích hoạt venv
if [ -d "$VENV_DIR" ]; then
    echo "✅ Phát hiện môi trường ảo (venv)"
    source "$VENV_DIR/bin/activate"
else
    echo "📦 Tạo môi trường ảo mới..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
fi

# Kiểm tra và cài đặt thư viện
echo "🔍 Kiểm tra thư viện..."
if ! python -c "import selenium, pandas, psutil, webdriver_manager" &> /dev/null; then
    echo "📦 Cài đặt thư viện cần thiết..."
    pip install -r requirements.txt
fi

# Kiểm tra hệ thống trình duyệt
echo "🔧 Kiểm tra hệ thống trình duyệt..."
python system_check.py

if [ $? -ne 0 ]; then
    echo "❌ Hệ thống trình duyệt chưa sẵn sàng"
    deactivate
    exit 1
fi

# Chạy chương trình chính
echo "✅ Khởi chạy chương trình..."
python main.py

# Deactivate venv
deactivate

echo ""
echo "👋 Chương trình đã kết thúc."
read -p "Nhấn Enter để đóng..."