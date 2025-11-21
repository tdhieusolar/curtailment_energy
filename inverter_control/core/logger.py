# core/logger.py
"""
Lớp quản lý logging - Phiên bản 0.5.1
"""

import logging
import sys

class InverterControlLogger:
    """Lớp quản lý logging - Phiên bản 0.5.1"""
    
    def __init__(self, config=None):
        self.config = config or self._get_default_config()
        self.setup_logging()
        
    def _get_default_config(self):
        """Lấy cấu hình mặc định nếu không có config từ bên ngoài"""
        return {
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(levelname)s - [%(threadName)s] - v0.5.1 - %(message)s",
                "file": "inverter_control_v0.5.1.log"
            }
        }
        
    def setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, self.config["logging"]["level"]),
            format=self.config["logging"]["format"],
            handlers=[
                logging.FileHandler(self.config["logging"]["file"], encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def log_success(self, message, inv_name=""):
        prefix = f"[{inv_name}] " if inv_name else ""
        self.logger.info(f"✅ {prefix}{message}")
    
    def log_error(self, message, inv_name=""):
        prefix = f"[{inv_name}] " if inv_name else ""
        self.logger.error(f"❌ {prefix}{message}")
    
    def log_warning(self, message, inv_name=""):
        prefix = f"[{inv_name}] " if inv_name else ""
        self.logger.warning(f"⚠️ {prefix}{message}")
    
    def log_info(self, message, inv_name=""):
        prefix = f"[{inv_name}] " if inv_name else ""
        self.logger.info(f"ℹ️ {prefix}{message}")
    
    def log_debug(self, message, inv_name=""):
        prefix = f"[{inv_name}] " if inv_name else ""
        self.logger.debug(f"🔍 {prefix}{message}")
    
    def log_version(self, version):
        """Log phiên bản chương trình"""
        self.logger.info(f"🚀 Khởi động Inverter Control v{version}")
    
    def log_queue_stats(self, stats):
        """Log thống kê hàng đợi"""
        self.logger.info(f"📊 Hàng đợi - Chính: {stats['primary_queue']}, Retry: {stats['retry_queue']}, "
                        f"Hoàn thành: {stats['completed']}, Thất bại: {stats['failed']}")