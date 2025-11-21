#!/bin/bash

# File: run_inverter.sh
# Chạy chương trình inverter control trong venv

echo "🚀 Khởi động Inverter Control System v0.5.3..."
echo "================================================"

# Đường dẫn đến venv
VENV_DIR="venv"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

# Kiểm tra và kích hoạt venv
if [ -d "$VENV_DIR" ]; then
    echo "✅ Phát hiện môi trường ảo (venv)"
    source "$VENV_DIR/bin/activate"
    
    # Kiểm tra Python trong venv
    if ! "$VENV_DIR/bin/python" -c "import sys; print(f'Python {sys.version}')" &> /dev/null; then
        echo "❌ Lỗi môi trường ảo, đang tái tạo..."
        python3 -m venv "$VENV_DIR"
        source "$VENV_DIR/bin/activate"
    fi
else
    echo "📦 Tạo môi trường ảo mới..."
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
fi

# Kiểm tra và cài đặt thư viện
echo "🔍 Kiểm tra thư viện..."
if ! python -c "import selenium, pandas, psutil" &> /dev/null; then
    echo "📦 Cài đặt thư viện cần thiết..."
    pip install -r requirements.txt
fi

# Chạy chương trình
echo "✅ Khởi chạy chương trình..."
python main.py

# Deactivate venv khi kết thúc
deactivate

echo ""
echo "👋 Chương trình đã kết thúc."
read -p "Nhấn Enter để đóng..."