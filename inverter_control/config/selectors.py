# config/selectors.py
"""
CSS Selectors cho web elements - Cập nhật cho phiên bản mới
"""

SELECTORS = {
    "login": {
        "dropdown_toggle": "#login-dropdown-list > a.dropdown-toggle",
        "username_field": "login-username",
        "password_field": "login-password", 
        "login_button": "login-buttons-password",
        "user_indicator": "installer"
    },
    "grid_control": {
        "connect_link": "link-grid-disconnect",  # ID của thẻ a
        "status_indicator": ["Disconnect Grid", "Connect Grid"],  # Text trong span
        "status_image": "img[src*='flash']",  # Selector cho hình ảnh trạng thái
        "status_text": ".menu-text"  # Selector cho text trạng thái
    },
    "monitoring": {
        "status_line": "#status-line-dsp",
        "power_active": ".js-active-power",
        "navbar": ".navbar"
    }
}