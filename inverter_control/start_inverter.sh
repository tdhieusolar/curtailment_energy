#!/bin/bash

# File: start_inverter.sh
# Phiên bản nâng cao với venv support

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/startup.log"
VENV_DIR="$SCRIPT_DIR/venv"
CONFIG_FILE="inverter_config.xlsx"

# Hàm log
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Hàm kiểm tra và kích hoạt venv
setup_venv() {
    log "🐍 Thiết lập môi trường ảo..."
    
    if [ -d "$VENV_DIR" ]; then
        log "✅ Phát hiện venv tồn tại"
        source "$VENV_DIR/bin/activate"
        
        # Kiểm tra venv có hoạt động không
        if ! python -c "import sys; print(f'Python {sys.version.split()[0]} in venv')" &> /dev/null; then
            log "⚠️ Venv bị lỗi, tái tạo..."
            create_venv
        else
            PY_VERSION=$(python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
            log "✅ Venv hoạt động - Python $PY_VERSION"
        fi
    else
        log "📦 Tạo venv mới..."
        create_venv
    fi
}

# Hàm tạo venv
create_venv() {
    if ! python3 -m venv "$VENV_DIR"; then
        log "❌ Lỗi tạo venv!"
        return 1
    fi
    source "$VENV_DIR/bin/activate"
    log "✅ Đã tạo và kích hoạt venv"
    return 0
}

# Hàm kiểm tra thư viện
check_dependencies() {
    log "📦 Kiểm tra dependencies..."
    
    if ! python -c "import selenium, pandas, psutil, openpyxl" &> /dev/null; then
        log "⚠️ Thiếu thư viện, đang cài đặt..."
        if pip install -r requirements.txt; then
            log "✅ Cài đặt thư viện thành công"
        else
            log "❌ Lỗi cài đặt thư viện!"
            return 1
        fi
    else
        log "✅ Tất cả thư viện đã sẵn sàng"
    fi
    return 0
}

# Hàm kiểm tra file
check_files() {
    log "🔍 Kiểm tra file cần thiết..."
    
    local missing_files=()
    
    [ ! -f "main.py" ] && missing_files+=("main.py")
    [ ! -f "requirements.txt" ] && missing_files+=("requirements.txt")
    [ ! -f "$CONFIG_FILE" ] && log "⚠️  File cấu hình Excel không tồn tại, sẽ sử dụng config mặc định"
    
    if [ ${#missing_files[@]} -ne 0 ]; then
        log "❌ Thiếu file: ${missing_files[*]}"
        return 1
    fi
    
    log "✅ Tất cả file cần thiết đã tồn tại"
    return 0
}

# Hàm cleanup
cleanup() {
    log "🧹 Dọn dẹp tài nguyên..."
    deactivate 2>/dev/null
    # Kill any remaining Chrome processes
    pkill -f chromedriver 2>/dev/null
    pkill -f chrome 2>/dev/null
}

# Main execution
main() {
    log "🚀 BẮT ĐẦU KHỞI CHẠY INVERTER CONTROL SYSTEM (VENV)"
    log "===================================================="
    
    # Đảm bảo chạy từ thư mục gốc
    cd "$SCRIPT_DIR"
    
    # Kiểm tra prerequisites
    if ! check_files; then
        log "❌ Không thể khởi chạy do thiếu file"
        exit 1
    fi
    
    # Thiết lập venv
    if ! setup_venv; then
        log "❌ Không thể thiết lập venv"
        exit 1
    fi
    
    # Kiểm tra dependencies
    if ! check_dependencies; then
        log "❌ Không thể cài đặt dependencies"
        exit 1
    fi
    
    # Setup trap for cleanup
    trap cleanup EXIT
    
    # Chạy chương trình chính
    log "🎯 ĐANG KHỞI CHẠY CHƯƠNG TRÌNH CHÍNH..."
    echo ""
    
    python main.py
    EXIT_CODE=$?
    
    echo ""
    log "🔚 Chương trình đã kết thúc với mã: $EXIT_CODE"
    
    if [ $EXIT_CODE -eq 0 ]; then
        log "✅ KẾT THÚC THÀNH CÔNG"
    else
        log "❌ KẾT THÚC VỚI LỖI"
    fi
}

# Chạy main function
main