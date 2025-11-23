#!/bin/bash
# setup_dev.sh - Script setup môi trường phát triển và tạo file requirements.txt

# ==========================================
# CẤU HÌNH VÀ MÀU SẮC
# ==========================================
VENV_NAME="venv"
REQS_IN_FILE="requirements.in"
REQS_OUT_FILE="requirements.txt"
PIP_TOOLS_PACKAGE="pip-tools"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔧 KHỞI TẠO MÔI TRƯỜNG PHÁT TRIỂN (DEV SETUP)${NC}"
echo "========================================================="

# ==========================================
# BƯỚC 1: TẠO VENV VÀ KÍCH HOẠT (Nếu chưa có)
# ==========================================
if [ ! -d "$VENV_NAME" ]; then
    echo -e "${YELLOW}📦 Đang tạo Venv và kích hoạt...${NC}"
    python3 -m venv "$VENV_NAME"
fi
source "$VENV_NAME/bin/activate"
echo -e "${GREEN}✅ Đã kích hoạt Venv.${NC}"

# ==========================================
# BƯỚC 2: TẠO requirements.in (Nếu thiếu)
# ==========================================
if [ ! -f "$REQS_IN_FILE" ]; then
    echo -e "${YELLOW}🚨 Tạo file $REQS_IN_FILE với các phụ thuộc cốt lõi mặc định...${NC}"
    
    # Danh sách các thư viện cốt lõi tối thiểu
    cat > "$REQS_IN_FILE" <<EOL
# Danh sách cac thu vien chinh ban su dung. Pip-tools se tu tim cac phu thuoc khac.
selenium
pandas
psutil
requests
EOL
    echo -e "${GREEN}✅ $REQS_IN_FILE đã sẵn sàng để chỉnh sửa.${NC}"
fi

# ==========================================
# BƯỚC 3: CÀI ĐẶT CÔNG CỤ PHÁT TRIỂN
# ==========================================
echo -e "${YELLOW}⚙️ Đang cài đặt $PIP_TOOLS_PACKAGE để quản lý dependencies...${NC}"
pip install $PIP_TOOLS_PACKAGE --upgrade > /dev/null 2>&1
echo -e "${GREEN}✅ Đã cài đặt $PIP_TOOLS_PACKAGE.${NC}"

# ==========================================
# BƯỚC 4: BIÊN DỊCH VÀ TẠO requirements.txt
# ==========================================
echo -e "${YELLOW}📝 Đang biên dịch $REQS_IN_FILE sang $REQS_OUT_FILE...${NC}"

# Lệnh chuyên nghiệp: Biên dịch các thư viện và chốt phiên bản
pip-compile "$REQS_IN_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Đã tạo $REQS_OUT_FILE thành công (Sẵn sàng triển khai).${NC}"
else
    echo -e "${RED}❌ Lỗi biên dịch. Kiểm tra $REQS_IN_FILE.${NC}"
fi

# ==========================================
# BƯỚC 5: CÀI ĐẶT THƯ VIỆN VÀO VENV HIỆN TẠI
# ==========================================
echo -e "${YELLOW}🔄 Đang cài đặt toàn bộ thư viện (Pip-sync)...${NC}"
# pip-sync sẽ cài đặt những gì có trong .txt và gỡ những gì thừa ra khỏi venv
pip-sync

echo -e "${GREEN}🎉 MÔI TRƯỜNG PHÁT TRIỂN ĐÃ SẴN SÀNG!${NC}"
echo "---------------------------------------------------------"
echo -e "👉 Bây giờ bạn có thể chạy: ${YELLOW}./launch.sh${NC}"

# Không deactivate để giữ môi trường phát triển mở