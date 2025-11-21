#!/bin/bash
# launch.sh - Universal Launcher for Linux/Mac

echo "🚀 Inverter Control System - Universal Launcher"
echo "================================================"

# Kiểm tra Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 không được cài đặt!"
    echo "📦 Vui lòng cài đặt Python3 trước"
    exit 1
fi

# Thử app_launcher trước, nếu lỗi thì dùng run_app
echo "🔧 Đang khởi chạy với app_launcher..."
if python3 app_launcher.py; then
    echo "✅ Ứng dụng kết thúc thành công"
else
    echo "⚠️ app_launcher gặp vấn đề, thử run_app..."
    python3 run_app.py
fi

# Giữ terminal mở
echo ""
read -p "👆 Nhấn Enter để đóng..."