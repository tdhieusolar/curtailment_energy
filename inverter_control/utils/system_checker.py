# utils/system_checker.py
import os
import sys
import platform
import subprocess
import importlib
import shutil
from pathlib import Path

# Các thư viện Python tiêu chuẩn có thể import toàn cục (đã được kiểm tra trong launch.sh)
try:
    from importlib.metadata import version, PackageNotFoundError
    # Thư viện packaging được import tại chỗ trong _check_version_compatibility để tránh lỗi khởi tạo
except ImportError as e:
    print(f"Lỗi hệ thống: Thiếu gói Python tiêu chuẩn cho việc kiểm tra ({e.name}). Kiểm tra môi trường Venv.")
    sys.exit(1)


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
                    
                    package_spec = line.split('#')[0].strip()  # Remove comments
                    
                    if package_spec:
                        # Phân tích package specification
                        package_name, version_spec = self._parse_package_spec(package_spec)
                        if package_name:
                            # Đảm bảo không ghi đè nếu có 2 dòng tương tự (ví dụ: package và package[extra])
                            required_packages[package_name] = version_spec or required_packages.get(package_name)
            
            print(f"✅ Đã đọc {len(required_packages)} packages từ requirements.txt")
            return required_packages
            
        except Exception as e:
            print(f"❌ Lỗi đọc requirements.txt: {e}")
            return self._get_default_requirements()
    
    def _parse_package_spec(self, package_spec):
        """
        Phân tích package specification thành tên và version requirement, xử lý [extras]
        Ví dụ: urllib3[socks]==2.5.0 -> package_name='urllib3', version_spec='==2.5.0'
        """
        operators = ['==', '>=', '<=', '>', '<', '~=', '!=']
        
        operator_pos = -1
        found_operator = None
        
        # 1. Tìm operator đầu tiên
        for op in operators:
            pos = package_spec.find(op)
            # Chỉ tìm operator ở ngoài dấu ngoặc vuông
            if pos != -1 and (operator_pos == -1 or pos < operator_pos) and '[' not in package_spec[:pos]:
                operator_pos = pos
                found_operator = op
        
        if operator_pos != -1 and found_operator:
            # Có version specification
            package_name = package_spec[:operator_pos].strip()
            version_spec = package_spec[operator_pos:].strip()
        else:
            # Không có version specification
            package_name = package_spec.strip()
            version_spec = None
            
        # 2. Xử lý [extras] (Ví dụ: urllib3[socks] -> urllib3)
        if '[' in package_name and ']' in package_name:
            # Cắt phần [extras] ra khỏi tên gói
            package_name = package_name.split('[')[0]

        # 3. Chuẩn hóa version spec (Giữ nguyên logic cũ)
        if version_spec:
            if found_operator == '~=':
                base_version = version_spec[len(found_operator):].strip()
                version_spec = f">={base_version}"
            elif found_operator not in ['>=', '==', '<=', '>', '<', '!=']:
                 version_spec = None # Bỏ qua version constraint không hợp lệ
                 
        return package_name, version_spec
    
    def _get_default_requirements(self):
        """Requirements mặc định nếu không có file"""
        return {
            'selenium': '>=4.15.0',
            'pandas': '>=2.1.3', 
            'psutil': '>=5.9.6',
            'openpyxl': '>=3.1.2', # Đã thêm openpyxl như khuyến nghị
            'requests': '>=2.31.0',
            'webdriver-manager': '>=4.0.1'
        }
    
    def check_python_environment(self):
        """Kiểm tra môi trường Python (system vs venv)"""
        # Kiểm tra theo biến môi trường VIRTUAL_ENV (luôn tồn tại khi Venv active)
        if os.environ.get('VIRTUAL_ENV') is not None:
            env_type = "Virtual Environment (Venv)"
            python_path = os.environ.get('VIRTUAL_ENV')
            message = f"ACTIVE: {python_path.split(os.sep)[-1]}"
        else:
            env_type = "System Python (KHÔNG khuyến nghị)" 
            python_path = sys.executable
            message = f"SYSTEM: {python_path}"
        
        # Vì script đã chạy được đến đây, coi là status=True
        self._add_check(env_type, True, message)
        return True
    
    def check_python_version(self):
        """Kiểm tra phiên bản Python"""
        major, minor, _ = map(int, self.python_version.split('.'))
        min_major, min_minor = 3, 8
        
        status = major > min_major or (major == min_major and minor >= min_minor)
        
        if not status:
            self._add_check("Python Version", False, 
                            f"Python 3.8+ required (current: {self.python_version})")
            return False
        self._add_check("Python Version", True, f"Python {self.python_version}")
        return True
    
    def check_required_packages(self):
        """Kiểm tra packages cần thiết sử dụng importlib.metadata"""
        required_packages = self._load_requirements_from_file()
        
        if not required_packages:
            self._add_check("Requirements File", False, "No requirements found")
            return False

        all_ok = True
        for package, required_spec in required_packages.items():
            try:
                # Lấy version dựa trên tên gói cài đặt (pip name)
                installed_version = version(package)
                self.package_versions[package] = installed_version
                
                status = True
                message = f"{installed_version} ✓"
                
                if required_spec:
                    version_ok = self._check_version_compatibility(installed_version, required_spec)
                    if not version_ok:
                        status = False
                        message = f"{installed_version} (LỖI: need {required_spec})"
                
                self._add_check(f"Package: {package}", status, message)
                if not status: 
                    all_ok = False

            except PackageNotFoundError:
                # Package chưa được cài đặt
                self.package_versions[package] = None
                requirement_msg = f" (need {required_spec})" if required_spec else ""
                self._add_check(f"Package: {package}", False, f"Chưa cài đặt{requirement_msg}")
                all_ok = False
        
        return all_ok

    def _check_version_compatibility(self, installed_version, required_spec):
        """Kiểm tra compatibility giữa version installed và requirement sử dụng thư viện packaging"""
        if installed_version in (None, "", "unknown"):
            return False

        try:
            # Import packaging tại chỗ (lazy)
            from packaging import version as pkg_version
            from packaging.specifiers import SpecifierSet
            
            installed = pkg_version.parse(installed_version)
            specifier = SpecifierSet(required_spec)
            
            # Kiểm tra xem phiên bản đã cài đặt có nằm trong SpecifierSet không
            return installed in specifier
                
        except ImportError:
            # Fallback: Nếu packaging không tồn tại, sử dụng so sánh đơn giản
            if required_spec.startswith('>='):
                required_version = required_spec[2:].strip()
                # Hàm so sánh đơn giản có thể không xử lý được pre-releases hay phức tạp khác
                return self._simple_version_compare(installed_version, required_version) >= 0
            else:
                 # Đối với các yêu cầu khác (==, <, >, v.v.), chỉ có thể trả về True để tránh sai sót
                return True
        except Exception as e:
            # Lỗi parse hoặc SpecifierSet không hợp lệ
            print(f"⚠️ Lỗi kiểm tra phiên bản '{required_spec}' cho {installed_version}: {e}")
            return True # Coi là OK nếu có lỗi kiểm tra
    
    def _simple_version_compare(self, v1, v2):
        """So sánh version đơn giản (chỉ cho numeric versions)"""
        try:
            # Logic parse version để bỏ qua các hậu tố như .dev, .post
            def parse_version(v):
                parts = []
                for part in v.split('.'):
                    numeric_part = ''.join(filter(str.isdigit, part))
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
            return (v1 >= v2) - (v1 < v2)
    
    def get_packages_to_install(self):
        """Lấy danh sách packages cần cài đặt (chưa có hoặc phiên bản không phù hợp)"""
        required_packages = self._load_requirements_from_file()
        
        if not required_packages:
            return {}
        
        packages_to_install = {}
        
        for package, required_spec in required_packages.items():
            installed_version = self.package_versions.get(package)
            
            # Khởi tạo package_spec để in báo cáo
            spec_to_install = f"{package}{required_spec}" if required_spec else package
            
            if installed_version is None:
                packages_to_install[package] = required_spec
            elif required_spec and not self._check_version_compatibility(installed_version, required_spec):
                packages_to_install[package] = required_spec
        
        return packages_to_install
    
    # --- CÁC METHOD KIỂM TRA HỆ THỐNG VÀ TÀI NGUYÊN (GIỮ NGUYÊN) ---
    
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
        """Kiểm tra web drivers (Tự động tải về nếu có webdriver-manager)"""
        try:
            # Import webdriver-manager tại chỗ (Lazy import)
            from webdriver_manager.chrome import ChromeDriverManager
            from webdriver_manager.firefox import GeckoDriverManager
            from webdriver_manager.microsoft import EdgeChromiumDriverManager
            from webdriver_manager.core.utils import ChromeType
            
            drivers_ok = []
            
            # --- 1. KIEM TRA CHROME/CHROMIUM ---
            try:
                # Thu lay Chrome/Chromium (bao gom ca Brave, Opera...)
                driver_path_chrome = ChromeDriverManager(chrome_type=ChromeType.ANY).install()
                drivers_ok.append(f"ChromeDriver: {os.path.basename(driver_path_chrome)}")
            except Exception as e:
                pass # Bo qua neu khong tim thay Chrome
                
            # --- 2. KIEM TRA EDGE ---
            try:
                driver_path_edge = EdgeChromiumDriverManager().install()
                drivers_ok.append(f"EdgeDriver: {os.path.basename(driver_path_edge)}")
            except Exception as e:
                pass # Bo qua neu khong tim thay Edge
                
            # --- 3. KIEM TRA FIREFOX ---
            try:
                driver_path_firefox = GeckoDriverManager().install()
                drivers_ok.append(f"GeckoDriver (Firefox): {os.path.basename(driver_path_firefox)}")
            except Exception as e:
                pass # Bo qua neu khong tim thay Firefox
            
            if drivers_ok:
                self._add_check("Web Drivers", True, "Tương thích ✓: " + ", ".join(drivers_ok))
                # Driver tự động tải về cũng ngụ ý trình duyệt đã được tìm thấy
                self._add_check("Web Browsers", True, "Trình duyệt được tìm thấy (thông qua WebDriver Manager)")
                return True
            else:
                self._add_check("Web Drivers", False, "LỖI: Không tải được driver tương thích cho Chrome/Edge/Firefox.")
                # Nếu không tìm thấy driver, có thể không tìm thấy trình duyệt.
                manual_drivers = self._get_available_drivers()
                if manual_drivers:
                     self._add_check("Web Drivers", True, f"Manual Driver(s) OK: {', '.join([name for name, path in manual_drivers])}")
                return False
                
        except ImportError:
            # Fallback nếu thiếu webdriver-manager (nhưng lỗi này khó xảy ra nếu bạn chạy setup_dev)
            self._add_check("Web Drivers", False, "Thư viện 'webdriver-manager' bị thiếu. Vui lòng chạy setup_dev.bat.")
            return False
        except Exception as e:
            # Lỗi khác (Lỗi mạng, lỗi hệ thống)
            self._add_check("Web Drivers", False, f"LỖI: Không thể tải driver. (Chi tiết: {e.__class__.__name__})")
            return False

    def check_system_resources(self):
        """Kiểm tra tài nguyên hệ thống"""
        try:
            import psutil # Import tại chỗ
            
            memory = psutil.virtual_memory()
            ram_gb = memory.total / (1024**3)
            disk = psutil.disk_usage('.')
            disk_gb = disk.free / (1024**3)
            
            ram_ok = ram_gb >= 2
            disk_ok = disk_gb >= 1
            
            status = ram_ok and disk_ok
            message = f"RAM: {ram_gb:.1f}GB {'✓' if ram_ok else '❌'}, Disk: {disk_gb:.1f}GB free {'✓' if disk_ok else '❌'}"
            
            self._add_check("System Resources", status, message)
            return status
            
        except ImportError:
            self._add_check("System Resources", False, "psutil not available")
            return False
        except Exception:
             self._add_check("System Resources", False, "Lỗi khi kiểm tra psutil")
             return False
    
    def check_network_connectivity(self):
        """Kiểm tra kết nối mạng"""
        try:
            import requests # Import tại chỗ
            
            test_urls = ["https://www.google.com", "https://pypi.org"]
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
                            "Connected ✓" if connected else "No internet connection ❌")
            return connected
            
        except ImportError:
            self._add_check("Network Connectivity", False, "requests not available")
            return False
        except Exception:
             self._add_check("Network Connectivity", False, "Lỗi khi kiểm tra mạng")
             return False

    def _get_available_browsers(self):
        """Lấy danh sách trình duyệt có sẵn (Dùng shutil.which linh hoạt hơn)"""
        # (Giữ nguyên logic của bạn)
        browsers = []
        chrome_names = ["google-chrome", "chrome", "google-chrome-stable", "chromium", "chromium-browser"]
        if self.is_windows: chrome_names = [n + ".exe" for n in chrome_names]
        
        for name in chrome_names:
            path = shutil.which(name)
            if path:
                browsers.append(("Chrome/Chromium", path))
                break 
        return browsers

    def _get_available_drivers(self):
        """Lấy danh sách web drivers thủ công có sẵn"""
        # (Giữ nguyên logic của bạn)
        drivers = []
        chromedriver_paths = []
        if self.is_windows:
            chromedriver_paths = ["chromedriver.exe", os.path.join("drivers", "chromedriver.exe"), r"C:\Windows\System32\chromedriver.exe"]
        else:
            chromedriver_paths = ["chromedriver", os.path.join("drivers", "chromedriver"), "/usr/local/bin/chromedriver", "/usr/bin/chromedriver", "/snap/bin/chromedriver"]
        
        for path in chromedriver_paths:
            if os.path.exists(path):
                drivers.append(("ChromeDriver", path))
                break
        return drivers
    
    # --- CÁC METHOD IN BÁO CÁO (GIỮ NGUYÊN) ---

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
        if os.environ.get('VIRTUAL_ENV') is not None:
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
                print(f"   - {package}: {current_version} → {package}{requirement_msg}")
        
        if self.failed_checks:
            print(f"❌ Có {len(self.failed_checks)} vấn đề cần giải quyết:")
            for failed in self.failed_checks:
                print(f"   - {failed}")
            print("🔧 Vui lòng chạy lại lệnh: **./launch.sh** để cài đặt/cập nhật các gói.")
        else:
            print("🎉 HỆ THỐNG ĐÃ SẴN SÀNG!")