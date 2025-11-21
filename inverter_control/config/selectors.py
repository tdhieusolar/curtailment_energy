"""
CSS Selectors cho web elements
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
        "connect_link": "link-grid-disconnect",
        "status_indicator": ["Disconnect Grid", "Connect Grid"]
    },
    "monitoring": {
        "status_line": "#status-line-dsp",
        "power_active": ".js-active-power",
        "navbar": ".navbar"
    }
}