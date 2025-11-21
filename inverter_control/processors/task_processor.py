"""
Xử lý tác vụ với Dynamic Driver Pool - Phiên bản 0.4.1
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from core.driver_pool import DynamicDriverPool
from core.task_queue import SmartTaskQueue, InverterTask
from core.controller import InverterController
from core.logger import InverterControlLogger
from config.settings import CONFIG, SYSTEM_URLS

class TaskProcessor:
    """Xử lý tác vụ với Dynamic Driver Pool - Phiên bản 0.4.1"""
    
    def __init__(self):
        self.logger = InverterControlLogger()
        self.task_queue = SmartTaskQueue()
        self.driver_pool = DynamicDriverPool()  # Dynamic pool
    
    def prepare_tasks(self, control_requests):
        """Chuẩn bị tasks và tính toán số lượng"""
        tasks = []
        total_inverters = 0
        
        for zone_name, stations in SYSTEM_URLS.items():
            for station_name, inverters in stations.items():
                if station_name in control_requests:
                    request = control_requests[station_name]
                    required_action = request["action"]
                    required_count = request["count"]
                    
                    sorted_invs = sorted(inverters.items())
                    count_added = 0
                    
                    for inv_name, inv_info in sorted_invs:
                        if count_added >= required_count:
                            break
                            
                        full_inv_name = f"{station_name}-{inv_name}"
                        target_url = inv_info["url"]
                        inv_status = inv_info.get("status", "OK").upper()
                        
                        task = InverterTask(full_inv_name, target_url, required_action, inv_status)
                        tasks.append(task)
                        count_added += 1
                        total_inverters += 1
        
        return tasks, total_inverters
    
    def process_single_inverter(self, task):
        """Xử lý một inverter với driver từ pool"""
        self.logger.log_info(f"Bắt đầu xử lý {task.required_action}", task.full_inv_name)
        
        # Kiểm tra trạng thái inverter
        if task.required_action == "ON" and task.inv_status == "FAULTY":
            self.logger.log_warning("Bỏ qua do trạng thái FAULTY", task.full_inv_name)
            return task, "SKIPPED", "INV lỗi không thể bật"
        
        # LẤY DRIVER TỪ POOL (thay vì khởi tạo mới)
        driver = self.driver_pool.get_driver()
        if not driver:
            return task, "RETRY", "Không thể lấy driver từ pool"
        
        try:
            # Tạo controller với driver từ pool
            controller = InverterController(driver)
            
            # Đăng nhập và xử lý
            login_success = controller.fast_login(task.target_url)
            
            if not login_success:
                return task, "RETRY", "Đăng nhập thất bại"
            
            success, message = controller.perform_grid_action(task.required_action)
            
            if success:
                status = "SUCCESS"
                self.logger.log_success(message, task.full_inv_name)
            else:
                # Phân loại lỗi thông minh
                if "BỎ QUA" in message:
                    status = "SUCCESS"  # Coi như thành công
                    self.logger.log_info(message, task.full_inv_name)
                elif "LỖI" in message and "ngược lại" in message:
                    status = "FAILED"   # Lỗi vĩnh viễn
                    self.logger.log_error(message, task.full_inv_name)
                else:
                    status = "RETRY"    # Lỗi tạm thời
                    self.logger.log_warning(message, task.full_inv_name)
            
            return task, status, message
            
        except Exception as e:
            error_msg = f"Lỗi không xác định: {str(e)}"
            self.logger.log_error(error_msg, task.full_inv_name)
            return task, "RETRY", error_msg
        
        finally:
            # TRẢ DRIVER VỀ POOL (thay vì đóng)
            self.driver_pool.return_driver(driver)
    
    def run_parallel_optimized(self, control_requests):
        """Chạy song song với dynamic driver pool"""
        start_time = datetime.now()
        self.logger.log_info(f"🚀 Bắt đầu xử lý {len(control_requests)} yêu cầu - Phiên bản 0.4.1 (Dynamic Driver Pool)")
        
        try:
            # Chuẩn bị tasks và tính toán số lượng
            tasks, total_inverters = self.prepare_tasks(control_requests)
            total_tasks = len(tasks)
            
            self.logger.log_info(f"📊 Tổng số inverters cần xử lý: {total_inverters}")
            self.logger.log_info(f"📦 Tổng số tasks: {total_tasks}")
            
            if total_tasks == 0:
                self.logger.log_warning("⚠️ Không có tác vụ nào để xử lý!")
                return []
            
            # KHỞI TẠO DRIVER POOL DỰA TRÊN SỐ LƯỢNG TASKS
            self.logger.log_info("🔄 Đang khởi tạo driver pool...")
            pool_success = self.driver_pool.initialize_pool(total_tasks)
            
            if not pool_success:
                self.logger.log_error("❌ Không thể khởi tạo driver pool!")
                return []
            
            # Hiển thị thông tin pool
            pool_info = self.driver_pool.get_pool_info()
            self.logger.log_info(f"🎯 Driver pool: {pool_info['pool_size']} drivers (Available: {pool_info['available']}, In Use: {pool_info['in_use']})")
            
            # Thêm tasks vào hàng đợi
            self.task_queue.add_tasks(tasks)
            
            # Xử lý với driver pool
            completed_count = 0
            batch_number = 0
            
            while self.task_queue.has_pending_tasks():
                batch_number += 1
                batch_stats = self._process_batch(batch_number)
                completed_count += batch_stats["completed"]
                
                queue_stats = self.task_queue.get_stats()
                progress_percent = (completed_count / total_tasks) * 100
                
                self.logger.log_info(
                    f"📦 Batch {batch_number}: Hoàn thành {batch_stats['completed']}, "
                    f"Retry {batch_stats['retried']}, Thất bại {batch_stats['failed']}"
                )
                self.logger.log_queue_stats(queue_stats)
                self.logger.log_info(f"📈 Tiến trình tổng: {completed_count}/{total_tasks} ({progress_percent:.1f}%)")
                
                # Nếu chỉ còn retry queue và ít tasks, dừng sớm
                if queue_stats["primary_queue"] == 0 and queue_stats["retry_queue"] < 3:
                    self.logger.log_info("⏹️ Chỉ còn ít tasks retry, kết thúc sớm")
                    break
            
            # Xử lý retry cuối cùng
            final_retry_stats = self._process_final_retry()
            completed_count += final_retry_stats["completed"]
            
            # Phân tích kết quả
            final_results = self._get_final_results()
            self._analyze_results(final_results, start_time, total_tasks)
            
            return final_results
            
        finally:
            # DỌN DẸP DRIVER POOL KHI KẾT THÚC CHƯƠNG TRÌNH
            self.driver_pool.cleanup()
    
    def _process_batch(self, batch_number):
        """Xử lý một batch tasks"""
        batch_stats = {"completed": 0, "retried": 0, "failed": 0}
        
        # Lấy batch tasks để xử lý
        batch_tasks = self.task_queue.get_next_batch(CONFIG["performance"]["max_workers"])
        
        if not batch_tasks:
            return batch_stats
        
        self.logger.log_info(f"🔄 Xử lý batch {batch_number} với {len(batch_tasks)} tasks")
        
        with ThreadPoolExecutor(max_workers=CONFIG["performance"]["max_workers"]) as executor:
            # Gửi tasks để xử lý song song
            future_to_task = {
                executor.submit(self.process_single_inverter, task): task 
                for task in batch_tasks
            }
            
            # Xử lý kết quả
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    processed_task, status, message = future.result(timeout=CONFIG["driver"]["timeout"])
                    
                    if status == "SUCCESS":
                        self.task_queue.mark_completed(processed_task, status, message)
                        batch_stats["completed"] += 1
                    elif status == "SKIPPED":
                        self.task_queue.mark_completed(processed_task, status, message)
                        batch_stats["completed"] += 1
                    elif status == "RETRY":
                        if self.task_queue.add_to_retry_queue(processed_task, message):
                            batch_stats["retried"] += 1
                        else:
                            batch_stats["failed"] += 1
                    else:  # FAILED
                        self.task_queue.mark_completed(processed_task, status, message)
                        batch_stats["failed"] += 1
                        
                except Exception as e:
                    self.logger.log_error(f"Lỗi xử lý task: {e}", task.full_inv_name)
                    if self.task_queue.add_to_retry_queue(task, str(e)):
                        batch_stats["retried"] += 1
                    else:
                        batch_stats["failed"] += 1
        
        return batch_stats
    
    def _process_final_retry(self):
        """Xử lý retry cuối cùng với ít workers hơn"""
        queue_stats = self.task_queue.get_stats()
        if queue_stats["retry_queue"] == 0:
            return {"completed": 0, "retried": 0, "failed": 0}
        
        self.logger.log_info(f"🔄 Xử lý {queue_stats['retry_queue']} tasks retry cuối cùng")
        
        final_stats = {"completed": 0, "retried": 0, "failed": 0}
        retry_workers = min(2, queue_stats["retry_queue"])  # Chỉ dùng 2 workers cho retry cuối
        
        with ThreadPoolExecutor(max_workers=retry_workers) as executor:
            batch_tasks = self.task_queue.get_next_batch(queue_stats["retry_queue"])
            
            future_to_task = {
                executor.submit(self.process_single_inverter, task): task 
                for task in batch_tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    processed_task, status, message = future.result(timeout=CONFIG["driver"]["timeout"])
                    
                    if status in ["SUCCESS", "SKIPPED"]:
                        self.task_queue.mark_completed(processed_task, status, message)
                        final_stats["completed"] += 1
                    else:
                        self.task_queue.mark_completed(processed_task, "FAILED", f"Final retry failed: {message}")
                        final_stats["failed"] += 1
                        
                except Exception as e:
                    self.logger.log_error(f"Final retry timeout: {e}", task.full_inv_name)
                    self.task_queue.mark_completed(task, "FAILED", "Final retry timeout")
                    final_stats["failed"] += 1
        
        return final_stats
    
    def _get_final_results(self):
        """Lấy kết quả cuối cùng"""
        results = []
        
        for task in self.task_queue.completed_tasks:
            results.append((task.full_inv_name, task.completion_status, task.completion_message))
        
        for task in self.task_queue.failed_tasks:
            results.append((task.full_inv_name, "FAILED", f"Vượt quá số lần retry: {task.last_error}"))
        
        return results
    
    def _analyze_results(self, results, start_time, total_tasks):
        """Phân tích và báo cáo kết quả"""
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Thống kê
        stats = {"SUCCESS": 0, "FAILED": 0, "SKIPPED": 0}
        for _, status, _ in results:
            stats[status] = stats.get(status, 0) + 1
        
        queue_stats = self.task_queue.get_stats()
        pool_info = self.driver_pool.get_pool_info()
        
        # In báo cáo
        self.logger.log_info("=" * 60)
        self.logger.log_info("🎯 BÁO CÁO TỔNG KẾT - PHIÊN BẢN 0.4.1 (DYNAMIC DRIVER POOL)")
        self.logger.log_info("=" * 60)
        self.logger.log_info(f"📦 Tổng số tác vụ: {total_tasks}")
        self.logger.log_info(f"🎯 Số drivers sử dụng: {pool_info['pool_size']}")
        self.logger.log_info(f"✅ Thành công: {stats['SUCCESS']}")
        self.logger.log_info(f"❌ Thất bại: {stats['FAILED']}")
        self.logger.log_info(f"⏭️ Bỏ qua: {stats['SKIPPED']}")
        self.logger.log_info(f"🔄 Tổng số lần retry: {queue_stats['total_retries']}")
        
        if total_tasks > 0:
            success_rate = (stats['SUCCESS'] / total_tasks) * 100
            self.logger.log_info(f"📊 Tỷ lệ thành công: {success_rate:.1f}%")
        
        total_seconds = duration.total_seconds()
        if total_tasks > 0:
            avg_time = total_seconds / total_tasks
            self.logger.log_info(f"⏱️ Thời gian trung bình/task: {avg_time:.2f}s")
        
        self.logger.log_info(f"🕒 Tổng thời gian thực hiện: {duration}")
        
        # In lỗi chi tiết
        errors = [(name, msg) for name, status, msg in results if status == "FAILED"]
        if errors:
            self.logger.log_info("🔍 CHI TIẾT LỖI:")
            for name, msg in errors:
                self.logger.log_error(msg, name)