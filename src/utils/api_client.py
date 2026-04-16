import requests
from typing import Optional, Dict, Any
from src.config import WEBSITE_URL, CONTACT_INFO, WEBSITE_ADMIN

class WebsiteAPI:
    """Client for interacting with the website API"""
    
    def __init__(self, base_url: str = WEBSITE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.authenticated = False

    def authenticate_admin(self) -> bool:
        """Authenticate with website admin credentials"""
        try:
            auth_data = {
                'username': WEBSITE_ADMIN['username'],
                'password': WEBSITE_ADMIN['password']
            }
            
            response = self.session.post(f"{self.base_url}/admin/login", json=auth_data)
            
            if response.status_code == 200:
                self.authenticated = True
                return True
            return False
        except Exception as e:
            print(f"Admin authentication failed: {e}")
            return False

    def submit_order_to_website(self, order_data: Dict[str, Any]) -> bool:
        """Submit order data to website admin panel"""
        if not self.authenticated:
            if not self.authenticate_admin():
                return False
        
        try:
            response = self.session.post(f"{self.base_url}/admin/orders", json=order_data)
            return response.status_code == 201
        except Exception as e:
            print(f"Failed to submit order to website: {e}")
            return False

    def get_contact_info(self) -> Dict[str, str]:
        """Get contact information"""
        return CONTACT_INFO

    def build_quote_url(self, service: str, hours: int) -> str:
        """Build a URL for getting a quote"""
        service_map = {
            'standard_cleaning': 'standard',
            'deep_cleaning': 'deep',
            'office_cleaning': 'office',
            'mosque_cleaning': 'mosque',
            'post_construction': 'construction',
            'move_in_out': 'move'
        }
        
        service_param = service_map.get(service, service)
        return f"{self.base_url}/Quote?service={service_param}&hours={hours}"

    def build_booking_url(self, service: str) -> str:
        """Build a URL for booking a service"""
        return f"{self.base_url}/Book?service={service}"

    def get_whatsapp_url(self, message: str = "") -> str:
        """Get WhatsApp link with a preset message"""
        phone = CONTACT_INFO.get('whatsapp', '+971556865394')
        # Remove + from phone for WhatsApp URL
        phone_clean = phone.replace('+', '')
        if message:
            return f"https://wa.me/{phone_clean}?text={message}"
        return f"https://wa.me/{phone_clean}"

    def calculate_price(self, hourly_rate: float, hours: int) -> float:
        """Calculate estimated price"""
        return hourly_rate * hours
