# test_chromedriver.py
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

try:
    print("🔧 Testing ChromeDriver...")
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service)
    driver.get("https://www.google.com")
    print("✅ ChromeDriver hoạt động tốt!")
    driver.quit()
except Exception as e:
    print(f"❌ Lỗi: {e}")