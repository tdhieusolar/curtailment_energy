"""
Lớp quản lý logging - Phiên bản 0.4.1
"""

import logging
import sys
from config.settings import CONFIG

class InverterControlLogger:
    """Lớp quản lý logging - Phiên bản 0.4.1"""
    
    def __init__(self):
        self.setup_logging()
        
    def setup_logging(self):
        logging.basicConfig(
            level=getattr(logging, CONFIG["logging"]["level"]),
            format=CONFIG["logging"]["format"],
            handlers=[
                logging.FileHandler(CONFIG["logging"]["file"], encoding='utf-8'),
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
    
    def log_queue_stats(self, stats):
        """Log thống kê hàng đợi"""
        self.logger.info(f"📊 Hàng đợi - Chính: {stats['primary_queue']}, Retry: {stats['retry_queue']}, "
                        f"Hoàn thành: {stats['completed']}, Thất bại: {stats['failed']}")