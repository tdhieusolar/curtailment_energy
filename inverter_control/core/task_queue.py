# core/task_queue.py
"""
Hàng đợi thông minh quản lý task và retry
"""

import threading
from collections import deque
from datetime import datetime
from core.logger import InverterControlLogger

class InverterTask:
    """Lớp đại diện cho một task inverter với tracking retry"""
    
    def __init__(self, full_inv_name, target_url, required_action, inv_status):
        self.full_inv_name = full_inv_name
        self.target_url = target_url
        self.required_action = required_action
        self.inv_status = inv_status
        self.retry_count = 0
        self.last_error = None
        self.created_time = datetime.now()
        self.priority = 1  # Độ ưu tiên (1: cao, 2: thấp)
    
    def __str__(self):
        return f"InverterTask({self.full_inv_name}, {self.required_action}, retry={self.retry_count})"
    
    def should_retry(self, max_retry_queue):
        """Kiểm tra xem task có nên retry không"""
        return self.retry_count < max_retry_queue
    
    def mark_retry(self, error_msg=None):
        """Đánh dấu task cần retry"""
        self.retry_count += 1
        self.last_error = error_msg
        self.priority = 2  # Giảm độ ưu tiên sau mỗi lần retry
        return self

class SmartTaskQueue:
    """Hàng đợi thông minh quản lý task và retry"""
    
    def __init__(self, config):
        self.config = config
        self.primary_queue = deque()  # Hàng đợi chính
        self.retry_queue = deque()    # Hàng đợi retry
        self.completed_tasks = []     # Task đã hoàn thành
        self.failed_tasks = []        # Task thất bại hoàn toàn
        self.logger = InverterControlLogger(config)
        self.lock = threading.Lock()  # Lock cho thread safety
    
    def add_tasks(self, tasks):
        """Thêm tasks vào hàng đợi chính"""
        with self.lock:
            for task in tasks:
                self.primary_queue.append(task)
            self.logger.log_info(f"📥 Đã thêm {len(tasks)} tasks vào hàng đợi chính")
    
    def get_next_batch(self, batch_size):
        """Lấy một batch tasks để xử lý song song"""
        with self.lock:
            batch = []
            
            # Ưu tiên lấy từ primary queue trước
            while self.primary_queue and len(batch) < batch_size:
                batch.append(self.primary_queue.popleft())
            
            # Nếu chưa đủ batch size, lấy từ retry queue
            while self.retry_queue and len(batch) < batch_size:
                task = self.retry_queue.popleft()
                self.logger.log_info(f"🔄 Lấy task từ retry queue: {task.full_inv_name} (retry {task.retry_count})")
                batch.append(task)
            
            return batch
    
    def add_to_retry_queue(self, task, error_msg=None):
        """Thêm task vào hàng đợi retry"""
        with self.lock:
            if task.should_retry(self.config["performance"]["max_retry_queue"]):
                task.mark_retry(error_msg)
                self.retry_queue.append(task)
                self.logger.log_warning(f"⏳ Đã chuyển {task.full_inv_name} sang retry queue (lần {task.retry_count})")
                return True
            else:
                self.failed_tasks.append(task)
                self.logger.log_error(f"💥 Task {task.full_inv_name} đã vượt quá số lần retry tối đa")
                return False
    
    def mark_completed(self, task, status, message):
        """Đánh dấu task hoàn thành"""
        with self.lock:
            task.completion_status = status
            task.completion_message = message
            task.completed_time = datetime.now()
            self.completed_tasks.append(task)
    
    def has_pending_tasks(self):
        """Kiểm tra còn task pending không"""
        with self.lock:
            return len(self.primary_queue) > 0 or len(self.retry_queue) > 0
    
    def get_stats(self):
        """Lấy thống kê hàng đợi"""
        with self.lock:
            return {
                "primary_queue": len(self.primary_queue),
                "retry_queue": len(self.retry_queue),
                "completed": len(self.completed_tasks),
                "failed": len(self.failed_tasks),
                "total_retries": sum(task.retry_count for task in self.completed_tasks + self.failed_tasks)
            }