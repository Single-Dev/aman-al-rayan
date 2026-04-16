from src.config import SERVICES, SUBSCRIPTION_PLANS, CONTACT_INFO

def get_welcome_message(first_name: str = "Friend") -> str:
    """Get welcome message"""
    return f"""
👋 Welcome to **Aman Al Rayan** Bot, {first_name}!

🏠 Your **Professional Cleaning Service** companion.

✨ We offer:
🧹 Standard Cleaning
✨ Deep Cleaning
🏢 Office Cleaning
🕌 Mosque Cleaning
🏗️ Post-Construction Cleaning
📦 Move-In/Move-Out Services

📱 **Quick Actions:**
• Browse our services
• Get instant quotes
• Book a cleaning session
• Subscribe for recurring services
• Chat with us on WhatsApp

🎯 All UAE Emirates - Eco-friendly & Professional

Let's get started! 🚀
    """

def get_services_message() -> str:
    """Get services list message"""
    message = "🧹 **Our Services:**\n\n"
    for service_id, service_info in SERVICES.items():
        message += f"{service_info['name']}\n"
        message += f"   {service_info['description']}\n\n"
    
    message += "Select a service and tell us how much you want to pay! ⬇️"
    return message

def get_service_details_message(service_id: str) -> str:
    """Get detailed service message"""
    if service_id not in SERVICES:
        return "Service not found."
    
    service = SERVICES[service_id]
    return f"""
{service['name']}

📝 **Description:**
{service['description']}

🎯 **Benefits:**
• Professional & Experienced Team
• Eco-Friendly Products
• 100% Satisfaction Guaranteed
• Flexible Scheduling
• Transparent Negotiation

Ready to book? Choose the number of hours needed ⬇️
    """

def get_quote_message(service_id: str, hours: int) -> str:
    """Get quote message"""
    if service_id not in SERVICES:
        return "Service not found."
    
    service = SERVICES[service_id]
    
    message = f"""
💰 **Booking Proposal:**

Service: {service['name']}
Hours: {hours} hour{'s' if hours > 1 else ''}

Please tell us how much you are willing to pay for this service.

✅ Our admin will review your offer and negotiate with you directly.
    """
    return message

def get_subscription_plans_message() -> str:
    """Get subscription plans message"""
    message = "💼 **Flexible Subscription Plans:**\n\n"
    
    for plan_id, plan in SUBSCRIPTION_PLANS.items():
        message += f"**{plan['name']}**\n"
        message += f"📅 {plan['frequency']}\n"
        message += f"💰 AED {plan['price_min']}-{plan['price_max']}/month\n"
        message += f"📝 {plan['description']}\n\n"
    
    message += "✅ Cancel anytime\n"
    message += "✅ Save up to 20%\n"
    message += "✅ No contracts\n\n"
    message += "Choose a plan that suits you! ⬇️"
    
    return message

def get_contact_message() -> str:
    """Get contact information message"""
    return f"""
📞 **Contact Aman Al Rayan:**

☎️ **Phone Numbers:**
• {CONTACT_INFO['phone']}
• {CONTACT_INFO['phone2']}
• {CONTACT_INFO['phone3']}

💬 **WhatsApp:**
• {CONTACT_INFO['whatsapp']}

📧 **Email:**
• {CONTACT_INFO['email']}

🌐 **Website:**
• https://aman-al-rayan.base44.app

🗺️ **Service Area:**
All UAE Emirates (Dubai, Abu Dhabi, Sharjah, etc.)

📱 We're available 24/7!
    """

def get_cart_summary(cart_items: list) -> str:
    """Get cart summary message"""
    if not cart_items:
        return "🛒 Your cart is empty."
    
    message = "🛒 **Your Cart:**\n\n"
    total_price = 0
    
    for i, item in enumerate(cart_items, 1):
        service = SERVICES.get(item['service_type'], {})
        price = item.get('estimated_price', 0)
        total_price += price
        
        message += f"{i}. {service.get('name', item['service_type'])}\n"
        message += f"   Hours: {item['hours']}\n"
        message += f"   Price: AED {price}\n\n"
    
    message += f"**Total: AED {total_price}**\n\n"
    message += "Would you like to proceed with checkout?"
    
    return message

def get_order_confirmation_message(order_id: int, service_id: str, hours: int, price: float = None) -> str:
    """Get order confirmation message"""
    service = SERVICES.get(service_id, {})
    
    return f"""
✅ **Order Confirmation:**

Order ID: #{order_id}
Service: {service.get('name', service_id)}
Hours: {hours}
{(f'Proposed Price: AED {price}\n' if price is not None else '')}
Status: ⏳ Pending Confirmation

📋 **Next Steps:**
1. Our admin will review your request
2. We will confirm the deal and schedule your service
3. Add any special requests or notes

📱 We'll reach out via WhatsApp or Phone

Thank you for choosing Aman Al Rayan! 🙏
    """

def get_help_message() -> str:
    """Get help message"""
    return """
❓ **How to Use This Bot:**

1️⃣ **Browse Services**
   • Tap "🧹 Services" to see all available services
   • Select a service to view details
   • Choose the number of hours needed

2️⃣ **Get a Quote**
   • After selecting hours, you'll get an instant quote
   • The price is calculated based on hourly rate

3️⃣ **Book a Service**
   • Confirm the quote to place your order
   • Add scheduling preferences or notes
   • Our team will contact you to finalize

4️⃣ **Subscriptions**
   • Browse flexible monthly plans
   • Save up to 20% with subscriptions
   • Cancel anytime

5️⃣ **Contact Us**
   • Direct phone numbers
   • WhatsApp messaging
   • Email support

💡 **Tips:**
• Add multiple services to your cart
• Provide detailed notes for better service
• Schedule in advance for better availability
• Check our website for more info

Questions? Contact us anytime! 📞
    """
