# utils/system_checker.py
import os
import sys
import platform
import subprocess
import importlib
import shutil
from pathlib import Path

class SystemChecker:
    """Kiểm tra hệ thống toàn diện với kiểm tra phiên bản từ requirements.txt"""
    
    def __init__(self, venv_manager=None):
        self.system = platform.system().lower()
        self.is_windows = self.system == "windows"
        self.is_linux = self.system == "linux" 
        self.is_mac = self.system == "darwin"
        self.architecture = platform.architecture()[0]
        self.python_version = platform.python_version()
        self.venv_manager = venv_manager
        
        self.checks = []
        self.failed_checks = []
        self.package_versions = {}  # Lưu phiên bản packages
        
    def _load_requirements_from_file(self):
        """Đọc requirements từ file requirements.txt"""
        requirements_path = Path("requirements.txt")
        
        if not requirements_path.exists():
            print(f"⚠️ File requirements.txt không tồn tại, sử dụng requirements mặc định")
            return self._get_default_requirements()
        
        required_packages = {}
        
        try:
            with open(requirements_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    
                    # Bỏ qua comment và empty lines
                    if not line or line.startswith('#') or line.startswith('--'):
                        continue
                    
                    # Xử lý line requirements
                    package_spec = line.split('#')[0].strip()  # Remove comments
                    
                    if package_spec:
                        # Phân tích package specification
                        package_name, version_spec = self._parse_package_spec(package_spec)
                        if package_name:
                            required_packages[package_name] = version_spec
            
            print(f"✅ Đã đọc {len(required_packages)} packages từ requirements.txt")
            return required_packages
            
        except Exception as e:
            print(f"❌ Lỗi đọc requirements.txt: {e}")
            return self._get_default_requirements()
    
    def _parse_package_spec(self, package_spec):
        """Phân tích package specification thành tên và version requirement"""
        # Các operators phổ biến
        operators = ['==', '>=', '<=', '>', '<', '~=', '!=']
        
        # Tìm operator đầu tiên
        operator_pos = -1
        found_operator = None
        
        for op in operators:
            pos = package_spec.find(op)
            if pos != -1 and (operator_pos == -1 or pos < operator_pos):
                operator_pos = pos
                found_operator = op
        
        if operator_pos != -1 and found_operator:
            # Có version specification
            package_name = package_spec[:operator_pos].strip()
            version_spec = package_spec[operator_pos:].strip()
            
            # Chuẩn hóa version spec để so sánh
            if found_operator in ['>=', '==']:
                # Giữ nguyên cho >= và ==
                return package_name, version_spec
            elif found_operator == '~=':
                # Compatible release ~= → chuyển thành >=
                base_version = version_spec[len(found_operator):].strip()
                return package_name, f">={base_version}"
            else:
                # Các operators khác → chỉ lấy tên package, bỏ qua version constraint phức tạp
                return package_name, None
        else:
            # Không có version specification
            return package_spec.strip(), None
    
    def _get_default_requirements(self):
        """Requirements mặc định nếu không có file"""
        return {
            'selenium': '>=4.15.0',
            'pandas': '>=2.1.3', 
            'psutil': '>=5.9.6',
            'openpyxl': '>=3.1.2',
            'requests': '>=2.31.0',
            'webdriver-manager': '>=4.0.1'
        }
    
    def check_python_environment(self):
        """Kiểm tra môi trường Python (system vs venv)"""
        if self.venv_manager and self.venv_manager.is_venv_activated():
            env_type = "Virtual Environment"
            python_path = sys.executable
            status = True
            message = f"VENV: {python_path}"
        else:
            env_type = "System Python" 
            python_path = sys.executable
            status = True
            message = f"SYSTEM: {python_path}"
        
        self._add_check("Python Environment", status, message)
        return status
    
    def check_python_version(self):
        """Kiểm tra phiên bản Python"""
        major, minor, _ = map(int, self.python_version.split('.'))
        if major < 3 or (major == 3 and minor < 8):
            self._add_check("Python Version", False, 
                          f"Python 3.8+ required (current: {self.python_version})")
            return False
        self._add_check("Python Version", True, f"Python {self.python_version}")
        return True
    
    def check_required_packages(self):
        """Kiểm tra packages cần thiết từ requirements.txt"""
        # Đọc requirements từ file
        required_packages = self._load_requirements_from_file()
        
        if not required_packages:
            self._add_check("Requirements File", False, "No requirements found")
            return False
        
        all_ok = True
        for package, required_spec in required_packages.items():
            try:
                # Thử import package
                module = importlib.import_module(package)
                installed_version = getattr(module, '__version__', 'unknown')
                
                # Lưu phiên bản hiện tại
                self.package_versions[package] = installed_version
                
                if installed_version != 'unknown':
                    # Kiểm tra version nếu có requirement
                    if required_spec:
                        version_ok = self._check_version_compatibility(installed_version, required_spec)
                        
                        if version_ok:
                            status = True
                            message = f"{package} {installed_version} ✓"
                        else:
                            status = False
                            message = f"{package} {installed_version} (need {required_spec})"
                    else:
                        # Không có version requirement → chỉ cần có package
                        status = True
                        message = f"{package} {installed_version} ✓"
                        
                    self._add_check(f"Package: {package}", status, message)
                    if not status:
                        all_ok = False
                else:
                    # Có package nhưng không lấy được version
                    status = True
                    message = f"{package} (version unknown)"
                    self._add_check(f"Package: {package}", status, message)
                    
            except ImportError:
                # Package chưa được cài đặt
                self.package_versions[package] = None
                requirement_msg = f" (need {required_spec})" if required_spec else ""
                self._add_check(f"Package: {package}", False, f"Not installed{requirement_msg}")
                all_ok = False
        
        return all_ok
    
    def _check_version_compatibility(self, installed_version, required_spec):
        """Kiểm tra compatibility giữa version installed và requirement"""
        if installed_version in (None, "", "unknown"):
            return False

        try:
            from packaging import version
            from packaging.specifiers import SpecifierSet
            
            installed = version.parse(installed_version)
            
            # Phân tích requirement specification
            if required_spec.startswith('>='):
                min_version = version.parse(required_spec[2:].strip())
                return installed >= min_version
            elif required_spec.startswith('=='):
                exact_version = version.parse(required_spec[2:].strip())
                return installed == exact_version
            elif required_spec.startswith('>'):
                min_version = version.parse(required_spec[1:].strip())
                return installed > min_version
            elif required_spec.startswith('<='):
                max_version = version.parse(required_spec[2:].strip())
                return installed <= max_version
            elif required_spec.startswith('<'):
                max_version = version.parse(required_spec[1:].strip())
                return installed < max_version
            else:
                # Sử dụng SpecifierSet cho các trường hợp phức tạp
                specifier = SpecifierSet(required_spec)
                return specifier.contains(installed_version)
                
        except ImportError:
            # Fallback: so sánh đơn giản cho >=
            if required_spec.startswith('>='):
                required_version = required_spec[2:].strip()
                return self._simple_version_compare(installed_version, required_version) >= 0
            else:
                # Không thể kiểm tra phức tạp without packaging → trả về True để tránh false negative
                return True
    
    def _simple_version_compare(self, v1, v2):
        """So sánh version đơn giản (chỉ cho numeric versions)"""
        try:
            def parse_version(v):
                # Chỉ lấy phần số, bỏ qua suffixes như .dev, .post, etc.
                parts = []
                for part in v.split('.'):
                    # Chỉ lấy phần số
                    numeric_part = ''
                    for char in part:
                        if char.isdigit():
                            numeric_part += char
                        else:
                            break
                    if numeric_part:
                        parts.append(int(numeric_part))
                return tuple(parts)
            
            v1_parts = parse_version(v1)
            v2_parts = parse_version(v2)
            
            # So sánh từng phần
            for i in range(max(len(v1_parts), len(v2_parts))):
                v1_part = v1_parts[i] if i < len(v1_parts) else 0
                v2_part = v2_parts[i] if i < len(v2_parts) else 0
                
                if v1_part < v2_part:
                    return -1
                elif v1_part > v2_part:
                    return 1
            
            return 0
            
        except:
            # Fallback cuối cùng: so sánh string
            return (v1 >= v2) - (v1 < v2)
    
    def get_packages_to_install(self):
        """Lấy danh sách packages cần cài đặt (chưa có hoặc phiên bản không phù hợp)"""
        required_packages = self._load_requirements_from_file()
        
        if not required_packages:
            return {}
        
        packages_to_install = {}
        
        for package, required_spec in required_packages.items():
            installed_version = self.package_versions.get(package)
            
            if installed_version is None:
                # Package chưa cài đặt
                packages_to_install[package] = required_spec
            elif required_spec and not self._check_version_compatibility(installed_version, required_spec):
                # Package có phiên bản không phù hợp
                packages_to_install[package] = required_spec
        
        return packages_to_install
    
    def check_browsers(self):
        """Kiểm tra trình duyệt có sẵn"""
        browsers = self._get_available_browsers()
        
        if not browsers:
            self._add_check("Web Browsers", False, "No compatible browser found")
            return False
        
        browser_list = ", ".join([f"{name}" for name, path in browsers])
        self._add_check("Web Browsers", True, browser_list)
        return True
    
    def check_webdrivers(self):
        """Kiểm tra web drivers"""
        drivers = self._get_available_drivers()
        
        if not drivers:
            self._add_check("Web Drivers", False, "No web driver found")
            return False
        
        driver_list = ", ".join([f"{name}" for name, path in drivers])
        self._add_check("Web Drivers", True, driver_list)
        return True
    
    def check_system_resources(self):
        """Kiểm tra tài nguyên hệ thống"""
        try:
            import psutil
            
            # RAM
            memory = psutil.virtual_memory()
            ram_gb = memory.total / (1024**3)
            ram_ok = ram_gb >= 2  # Tối thiểu 2GB RAM
            
            # Disk space
            disk = psutil.disk_usage('.')
            disk_gb = disk.free / (1024**3)
            disk_ok = disk_gb >= 1  # Tối thiểu 1GB free
            
            status = ram_ok and disk_ok
            message = f"RAM: {ram_gb:.1f}GB, Disk: {disk_gb:.1f}GB free"
            
            self._add_check("System Resources", status, message)
            return status
            
        except ImportError:
            self._add_check("System Resources", False, "psutil not available")
            return False
    
    def check_network_connectivity(self):
        """Kiểm tra kết nối mạng"""
        try:
            import requests
            
            test_urls = [
                "https://www.google.com",
                "https://www.github.com",
                "https://pypi.org"
            ]
            
            connected = False
            for url in test_urls:
                try:
                    response = requests.get(url, timeout=5)
                    if response.status_code == 200:
                        connected = True
                        break
                except:
                    continue
            
            self._add_check("Network Connectivity", connected, 
                           "Connected" if connected else "No internet connection")
            return connected
            
        except ImportError:
            self._add_check("Network Connectivity", False, "requests not available")
            return False
    
    def _get_available_browsers(self):
        """Lấy danh sách trình duyệt có sẵn"""
        browsers = []
        
        # Chrome/Chromium
        chrome_paths = []
        if self.is_windows:
            chrome_paths = [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
            ]
        elif self.is_linux:
            chrome_paths = [
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium-browser",
                "/usr/bin/chromium",
                "/snap/bin/chromium"
            ]
        else:  # mac
            chrome_paths = [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium"
            ]
        
        for path in chrome_paths:
            if os.path.exists(path):
                browsers.append(("Chrome", path))
                break
        
        # Edge
        edge_paths = []
        if self.is_windows:
            edge_paths = [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            ]
        elif self.is_linux:
            edge_paths = [
                "/usr/bin/microsoft-edge",
                "/usr/bin/microsoft-edge-stable"
            ]
        else:  # mac
            edge_paths = [
                "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"
            ]
        
        for path in edge_paths:
            if os.path.exists(path):
                browsers.append(("Edge", path))
                break
        
        return browsers
    
    def _get_available_drivers(self):
        """Lấy danh sách web drivers có sẵn"""
        drivers = []
        
        # ChromeDriver
        chromedriver_paths = []
        if self.is_windows:
            chromedriver_paths = [
                "chromedriver.exe",
                os.path.join("drivers", "chromedriver.exe"),
                r"C:\Windows\System32\chromedriver.exe"
            ]
        else:
            chromedriver_paths = [
                "chromedriver",
                os.path.join("drivers", "chromedriver"),
                "/usr/local/bin/chromedriver",
                "/usr/bin/chromedriver",
                "/snap/bin/chromedriver"
            ]
        
        for path in chromedriver_paths:
            if os.path.exists(path):
                drivers.append(("ChromeDriver", path))
                break
        
        # EdgeDriver
        edgedriver_paths = []
        if self.is_windows:
            edgedriver_paths = [
                "msedgedriver.exe",
                os.path.join("drivers", "msedgedriver.exe"),
                r"C:\Windows\System32\msedgedriver.exe",
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe"
            ]
        else:
            edgedriver_paths = [
                "msedgedriver",
                os.path.join("drivers", "msedgedriver"),
                "/usr/local/bin/msedgedriver",
                "/usr/bin/msedgedriver"
            ]
        
        for path in edgedriver_paths:
            if os.path.exists(path):
                drivers.append(("EdgeDriver", path))
                break
        
        return drivers
    
    def _add_check(self, name, status, message):
        """Thêm kết quả kiểm tra"""
        self.checks.append({
            'name': name,
            'status': status,
            'message': message
        })
        if not status:
            self.failed_checks.append(name)
    
    def run_full_check(self):
        """Chạy kiểm tra toàn diện"""
        print("🔍 KIỂM TRA HỆ THỐNG TOÀN DIỆN")
        if self.venv_manager and self.venv_manager.is_venv_activated():
            print("📍 Môi trường: VIRTUAL ENVIRONMENT")
        else:
            print("📍 Môi trường: SYSTEM PYTHON")
        print("=" * 50)
        
        checks = [
            self.check_python_environment,
            self.check_python_version,
            self.check_required_packages,
            self.check_system_resources,
            self.check_network_connectivity,
            self.check_browsers,
            self.check_webdrivers
        ]
        
        for check_func in checks:
            check_func()
        
        self.print_report()
        return len(self.failed_checks) == 0
    
    def print_report(self):
        """In báo cáo kiểm tra"""
        print("\n📊 BÁO CÁO KIỂM TRA HỆ THỐNG")
        print("=" * 50)
        
        for check in self.checks:
            status_icon = "✅" if check['status'] else "❌"
            print(f"{status_icon} {check['name']}: {check['message']}")
        
        print("=" * 50)
        
        # Hiển thị packages cần cài đặt
        packages_to_install = self.get_packages_to_install()
        if packages_to_install:
            print(f"📦 Cần cài đặt/update {len(packages_to_install)} packages:")
            for package, required_spec in packages_to_install.items():
                current_version = self.package_versions.get(package, "Not installed")
                requirement_msg = f" (need {required_spec})" if required_spec else ""
                print(f"   - {package}: {current_version} → {package}{requirement_msg}")
        
        if self.failed_checks:
            print(f"❌ Có {len(self.failed_checks)} vấn đề cần giải quyết:")
            for failed in self.failed_checks:
                print(f"   - {failed}")
        else:
            print("🎉 HỆ THỐNG ĐÃ SẴN SÀNG!")
    
    def get_failed_checks(self):
        """Lấy danh sách các check thất bại"""
        return self.failed_checks
    
    def get_packages_status(self):
        """Lấy trạng thái tất cả packages"""
        return self.package_versions.copy()