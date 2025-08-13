from datetime import datetime
import re

def format_phone(phone):
    """Format phone number to standard Kazakhstan format"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Add country code if not present
    if len(digits) == 10 and digits.startswith('7'):
        digits = '7' + digits
    elif len(digits) == 10:
        digits = '7' + digits
    
    # Format as +7 (XXX) XXX-XX-XX
    if len(digits) == 11 and digits.startswith('7'):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    
    return phone

def format_datetime(dt):
    """Format datetime for display"""
    if not dt:
        return ""
    return dt.strftime('%d.%m.%Y %H:%M')

def format_date(dt):
    """Format date for display"""
    if not dt:
        return ""
    return dt.strftime('%d.%m.%Y')

def calculate_days_ago(dt):
    """Calculate how many days ago the datetime was"""
    if not dt:
        return ""
    
    days = (datetime.utcnow() - dt).days
    
    if days == 0:
        return "Сегодня"
    elif days == 1:
        return "Вчера"
    else:
        return f"{days} дней назад"

# Template filters registration function
def register_template_filters(app):
    """Register custom template filters with the Flask app"""
    
    @app.template_filter('format_phone')
    def format_phone_filter(phone):
        return format_phone(phone)

    @app.template_filter('format_datetime')
    def format_datetime_filter(dt):
        return format_datetime(dt)

    @app.template_filter('format_date')
    def format_date_filter(dt):
        return format_date(dt)

    @app.template_filter('days_ago')
    def days_ago_filter(dt):
        return calculate_days_ago(dt)
