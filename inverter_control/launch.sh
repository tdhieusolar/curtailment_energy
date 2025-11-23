#!/bin/bash
# launch.sh - FINAL PROFESSIONAL DEPLOYMENT LAUNCHER

# ==========================================
# CẤU HÌNH VÀ MÀU SẮC
# ==========================================
VENV_NAME="venv"
REQUIREMENTS_FILE="requirements.txt"
MAIN_SCRIPT="app_launcher.py"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 INVERTER CONTROL SYSTEM - PROFESSIONAL LAUNCHER${NC}"
echo "==================================================="

# ==========================================
# BƯỚC 1: KIỂM TRA PYTHON & FILE TRIỂN KHAI
# ==========================================
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Lỗi: Python3 chưa được cài đặt!${NC}"
    exit 1
fi

# Dùng logic fail-fast: Đảm bảo file requirements.txt (do Developer cung cấp) phải tồn tại
if [ ! -f "$REQUIREMENTS_FILE" ] || [ ! -s "$REQUIREMENTS_FILE" ]; then
    echo -e "${RED}❌ LỖI TRIỂN KHAI: File $REQUIREMENTS_FILE bị thiếu hoặc rỗng.${NC}"
    echo -e "${YELLOW}🚨 Vui lòng đảm bảo file này được tạo từ requirements.in và Nhà phát triển đã cung cấp.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Đã tìm thấy file $REQUIREMENTS_FILE (${YELLOW}Toàn vẹn${NC})${NC}"


# ==========================================
# BƯỚC 2: KIỂM TRA & TẠO VENV
# ==========================================
if [ ! -d "$VENV_NAME" ]; then
    echo -e "${YELLOW}📦 Không tìm thấy môi trường ảo. Đang tạo mới...${NC}"
    if python3 -m venv "$VENV_NAME"; then
        echo -e "${GREEN}✅ Đã tạo venv thành công!${NC}"
    else
        echo -e "${RED}❌ Tạo venv thất bại! Cần python3-venv (trên Debian/Ubuntu).${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}✅ Đã tìm thấy môi trường ảo ($VENV_NAME).${NC}"

# ==========================================
# BƯỚC 3: KÍCH HOẠT & CÀI ĐẶT THƯ VIỆN
# ==========================================
source "$VENV_NAME/bin/activate"

echo -e "${YELLOW}🔄 Đang đồng bộ thư viện từ $REQUIREMENTS_FILE...${NC}"
pip install --upgrade pip > /dev/null 2>&1
# Sử dụng cờ --no-cache-dir để tiết kiệm dung lượng, cờ -q để im lặng (chuyên nghiệp hơn)
pip install -r "$REQUIREMENTS_FILE" --no-cache-dir -q

if [ $? -eq 0 ]; then
     echo -e "${GREEN}✅ Thư viện đã sẵn sàng trong Venv!${NC}"
else
     echo -e "${RED}❌ Lỗi khi cài đặt thư viện. Vui lòng kiểm tra requirements.txt${NC}"
     # Không exit, vẫn thử chạy app để có log chi tiết hơn
fi


# ==========================================
# BƯỚC 4: KHỞI CHẠY ỨNG DỤNG
# ==========================================
echo "---------------------------------------------------"
echo -e "${GREEN}🚀 Đang khởi chạy ứng dụng...${NC}"
echo "---------------------------------------------------"

python "$MAIN_SCRIPT"

# ==========================================
# KẾT THÚC
# ==========================================
deactivate
echo ""
echo -e "${GREEN}👋 Ứng dụng đã kết thúc.${NC}"