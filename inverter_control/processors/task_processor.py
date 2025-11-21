# processors/task_processor.py
"""
Xử lý tác vụ với tối ưu cho ít tasks - Phiên bản 0.5.3
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

from core.driver_pool import DynamicDriverPool
from core.task_queue import SmartTaskQueue, InverterTask
from core.controller import InverterController
from core.logger import InverterControlLogger

class TaskProcessor:
    """Xử lý tác vụ với tối ưu cho ít tasks"""
    
    def __init__(self, config, system_urls):
        self.config = config
        self.system_urls = system_urls
        self.logger = InverterControlLogger(config)
        self.task_queue = SmartTaskQueue(config)
        self.driver_pool = DynamicDriverPool(config)
        self.active_tasks = 0
        self.active_lock = threading.Lock()
    
    def prepare_tasks(self, control_requests):
        """Chuẩn bị tasks và tính toán số lượng"""
        tasks = []
        total_inverters = 0
        
        for zone_name, stations in self.system_urls.items():
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
        """Xử lý một inverter"""
        with self.active_lock:
            self.active_tasks += 1
            current_active = self.active_tasks
        
        self.logger.log_debug(f"🎯 Bắt đầu xử lý {task.required_action} (active: {current_active})", task.full_inv_name)
        
        try:
            # Lấy driver với timeout
            driver = self.driver_pool.get_driver(timeout=25)
            if not driver:
                return task, "RETRY", "Không lấy được driver từ pool"
            
            # Xử lý với controller
            controller = InverterController(driver, self.config)
            login_success = controller.fast_login(task.target_url)
            
            if not login_success:
                self.driver_pool.return_driver(driver)
                return task, "RETRY", "Đăng nhập thất bại"
            
            success, message = controller.perform_grid_action(task.required_action)
            self.driver_pool.return_driver(driver)
            
            if success:
                status = "SUCCESS"
                self.logger.log_success(message, task.full_inv_name)
            else:
                if "BỎ QUA" in message:
                    status = "SUCCESS"
                    self.logger.log_info(message, task.full_inv_name)
                else:
                    status = "RETRY"
                    self.logger.log_warning(message, task.full_inv_name)
            
            return task, status, message
            
        except Exception as e:
            error_msg = f"Lỗi xử lý: {str(e)}"
            self.logger.log_error(error_msg, task.full_inv_name)
            return task, "RETRY", error_msg
        finally:
            with self.active_lock:
                self.active_tasks -= 1
    
    def run_parallel_optimized(self, control_requests):
        """Chạy song song với tối ưu cho ít tasks"""
        start_time = datetime.now()
        
        # Chuẩn bị tasks
        tasks, total_inverters = self.prepare_tasks(control_requests)
        total_tasks = len(tasks)
        
        self.logger.log_info(f"🚀 Bắt đầu xử lý {total_tasks} tasks - Phiên bản 0.5.3 (Optimized Pool)")
        
        if total_tasks == 0:
            self.logger.log_warning("⚠️ Không có tác vụ nào để xử lý!")
            return []
        
        # Khởi tạo driver pool với số lượng tối ưu
        self.logger.log_info("🔄 Đang khởi tạo driver pool...")
        if not self.driver_pool.initialize_pool(total_tasks):
            self.logger.log_error("❌ Không thể khởi tạo driver pool!")
            return []
        
        pool_info = self.driver_pool.get_pool_info()
        self.logger.log_info(f"🎯 Driver pool: {pool_info['pool_size']} drivers (Available: {pool_info['available']})")
        
        # Thêm tasks vào queue
        self.task_queue.add_tasks(tasks)
        
        # Xử lý với strategy phù hợp theo số lượng tasks
        if total_tasks == 1:
            # TỐI ƯU: Chỉ 1 task → xử lý tuần tự
            completed_count = self._process_single_task()
        elif total_tasks <= 3:
            # TỐI ƯU: Ít tasks → xử lý tuần tự hoặc song song đơn giản
            completed_count = self._process_few_tasks(total_tasks)
        else:
            # Nhiều tasks → xử lý song song với batch
            completed_count = self._process_many_tasks(total_tasks)
        
        # Kết quả
        final_results = self._get_final_results()
        self._analyze_results(final_results, start_time, total_tasks)
        
        # Cleanup
        self.driver_pool.cleanup()
        return final_results
    
    def _process_single_task(self):
        """Xử lý khi chỉ có 1 task - Tối ưu tuần tự"""
        self.logger.log_info("🔸 Chế độ tối ưu: 1 task → xử lý tuần tự")
        
        batch_tasks = self.task_queue.get_next_batch(1)
        if not batch_tasks:
            return 0
        
        task = batch_tasks[0]
        try:
            processed_task, status, message = self.process_single_inverter(task)
            
            if status in ["SUCCESS", "SKIPPED"]:
                self.task_queue.mark_completed(processed_task, status, message)
                return 1
            elif status == "RETRY":
                if self.task_queue.add_to_retry_queue(processed_task, message):
                    self.logger.log_warning(f"⏳ Task {task.full_inv_name} chuyển sang retry queue")
                else:
                    self.task_queue.mark_completed(processed_task, "FAILED", message)
            else:
                self.task_queue.mark_completed(processed_task, status, message)
                
        except Exception as e:
            self.logger.log_error(f"Lỗi xử lý task: {e}", task.full_inv_name)
            if self.task_queue.add_to_retry_queue(task, str(e)):
                self.logger.log_warning(f"⏳ Task {task.full_inv_name} chuyển sang retry queue do lỗi")
        
        return 0
    
    def _process_few_tasks(self, total_tasks):
        """Xử lý khi có ít tasks (2-3 tasks)"""
        self.logger.log_info(f"🔸 Chế độ tối ưu: {total_tasks} tasks → xử lý đơn giản")
        
        completed_count = 0
        batch_tasks = self.task_queue.get_next_batch(total_tasks)
        
        if not batch_tasks:
            return 0
        
        # Sử dụng ThreadPoolExecutor với số workers bằng số tasks
        with ThreadPoolExecutor(max_workers=len(batch_tasks)) as executor:
            future_to_task = {
                executor.submit(self.process_single_inverter, task): task 
                for task in batch_tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    processed_task, status, message = future.result(timeout=30)
                    
                    if status in ["SUCCESS", "SKIPPED"]:
                        self.task_queue.mark_completed(processed_task, status, message)
                        completed_count += 1
                    elif status == "RETRY":
                        if self.task_queue.add_to_retry_queue(processed_task, message):
                            self.logger.log_warning(f"⏳ Task {task.full_inv_name} chuyển sang retry queue")
                        else:
                            completed_count += 0  # Không tăng completed_count
                    else:
                        self.task_queue.mark_completed(processed_task, status, message)
                        completed_count += 0  # Không tăng completed_count
                        
                except Exception as e:
                    self.logger.log_error(f"Lỗi future: {e}", task.full_inv_name)
                    if self.task_queue.add_to_retry_queue(task, str(e)):
                        self.logger.log_warning(f"⏳ Task {task.full_inv_name} chuyển sang retry queue do timeout")
        
        return completed_count
    
    def _process_many_tasks(self, total_tasks):
        """Xử lý khi có nhiều tasks (>3 tasks)"""
        self.logger.log_info(f"🔸 Chế độ tiêu chuẩn: {total_tasks} tasks → xử lý song song")
        
        completed_count = 0
        batch_number = 0
        
        while self.task_queue.has_pending_tasks():
            batch_number += 1
            batch_stats = self._process_batch_with_limits(batch_number)
            completed_count += batch_stats["completed"]
            
            # Progress reporting
            queue_stats = self.task_queue.get_stats()
            progress_percent = (completed_count / total_tasks) * 100
            
            self.logger.log_info(
                f"📦 Batch {batch_number}: {batch_stats['completed']} hoàn thành, "
                f"{batch_stats['retried']} retry, {batch_stats['failed']} thất bại"
            )
            self.logger.log_info(f"📈 Tiến trình: {completed_count}/{total_tasks} ({progress_percent:.1f}%)")
            
            # Early termination for small retry queue
            if queue_stats["primary_queue"] == 0 and queue_stats["retry_queue"] < 2:
                self.logger.log_info("⏹️ Chỉ còn ít tasks retry, kết thúc sớm")
                break
        
        # Final retry
        final_retry_stats = self._process_final_retry()
        completed_count += final_retry_stats["completed"]
        
        return completed_count
    
    def _process_batch_with_limits(self, batch_number):
        """Xử lý batch với giới hạn đồng thời"""
        batch_stats = {"completed": 0, "retried": 0, "failed": 0}
        
        # Lấy batch tasks (giới hạn theo số driver available)
        pool_info = self.driver_pool.get_pool_info()
        max_concurrent = min(
            self.config["performance"]["max_workers"],
            pool_info["available"] + 2  # +2 để linh hoạt
        )
        
        batch_tasks = self.task_queue.get_next_batch(max_concurrent)
        
        if not batch_tasks:
            return batch_stats
        
        self.logger.log_debug(f"🔄 Batch {batch_number}: {len(batch_tasks)} tasks, {max_concurrent} concurrent")
        
        # Xử lý với ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=len(batch_tasks)) as executor:
            future_to_task = {
                executor.submit(self.process_single_inverter, task): task 
                for task in batch_tasks
            }
            
            for future in as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    processed_task, status, message = future.result(timeout=30)
                    
                    if status in ["SUCCESS", "SKIPPED"]:
                        self.task_queue.mark_completed(processed_task, status, message)
                        batch_stats["completed"] += 1
                    elif status == "RETRY":
                        if self.task_queue.add_to_retry_queue(processed_task, message):
                            batch_stats["retried"] += 1
                        else:
                            batch_stats["failed"] += 1
                    else:
                        self.task_queue.mark_completed(processed_task, status, message)
                        batch_stats["failed"] += 1
                        
                except Exception as e:
                    self.logger.log_error(f"Lỗi future: {e}", task.full_inv_name)
                    if self.task_queue.add_to_retry_queue(task, str(e)):
                        batch_stats["retried"] += 1
                    else:
                        batch_stats["failed"] += 1
        
        return batch_stats
    
    def _process_final_retry(self):
        """Xử lý retry cuối cùng"""
        queue_stats = self.task_queue.get_stats()
        if queue_stats["retry_queue"] == 0:
            return {"completed": 0, "retried": 0, "failed": 0}
        
        self.logger.log_info(f"🔄 Xử lý {queue_stats['retry_queue']} tasks retry cuối cùng")
        
        final_stats = {"completed": 0, "retried": 0, "failed": 0}
        
        # TỐI ƯU: Cho retry cuối, sử dụng tuần tự để đảm bảo ổn định
        batch_tasks = self.task_queue.get_next_batch(queue_stats["retry_queue"])
        
        for task in batch_tasks:
            try:
                processed_task, status, message = self.process_single_inverter(task)
                
                if status in ["SUCCESS", "SKIPPED"]:
                    self.task_queue.mark_completed(processed_task, status, message)
                    final_stats["completed"] += 1
                else:
                    self.task_queue.mark_completed(processed_task, "FAILED", f"Final retry failed: {message}")
                    final_stats["failed"] += 1
                    
            except Exception as e:
                self.logger.log_error(f"Final retry error: {e}", task.full_inv_name)
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
        
        # In báo cáo
        self.logger.log_info("=" * 60)
        self.logger.log_info(f"🎯 BÁO CÁO TỔNG KẾT - PHIÊN BẢN 0.5.3 (OPTIMIZED POOL)")
        self.logger.log_info("=" * 60)
        self.logger.log_info(f"📦 Tổng số tác vụ: {total_tasks}")
        self.logger.log_info(f"🎯 Số drivers sử dụng: {self.driver_pool.get_pool_info()['pool_size']}")
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