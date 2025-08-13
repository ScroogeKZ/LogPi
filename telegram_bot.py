import requests
import logging
import os
from models import Order

# Get Telegram bot configuration from environment variables
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')

def send_telegram_notification(order):
    """Send notification about new order to Telegram"""
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logging.warning("Telegram bot token or chat ID not configured")
        return False
    
    try:
        # Prepare message text
        message_text = f"""
🆕 *Новая заявка XPOM-KZ*

📋 *Номер:* `{order.tracking_number}`
👤 *Клиент:* {order.customer_name}
📞 *Телефон:* {order.customer_phone}
📧 *Email:* {order.customer_email or 'Не указан'}

🚚 *Тип заказа:* {order.get_type_display()}

📍 *Забор:* {order.pickup_address}
📍 *Доставка:* {order.delivery_address}

📦 *Груз:* {order.cargo_description}
⚖️ *Вес:* {order.cargo_weight or 'Не указан'} кг
📏 *Габариты:* {order.cargo_dimensions or 'Не указаны'}

🕐 *Создана:* {order.created_at.strftime('%d.%m.%Y %H:%M')}
"""

        # Send message
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message_text,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            logging.info(f"Telegram notification sent for order {order.tracking_number}")
            return True
        else:
            logging.error(f"Failed to send Telegram notification: {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error sending Telegram notification: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error sending Telegram notification: {e}")
        return False

def send_status_update_notification(order, old_status, new_status):
    """Send notification about order status update"""
    
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    
    try:
        status_map = {
            'new': 'Новая заявка',
            'confirmed': 'Подтверждена',
            'in_progress': 'В процессе доставки',
            'delivered': 'Доставлена',
            'cancelled': 'Отменена'
        }
        
        message_text = f"""
🔄 *Обновление статуса заказа*

📋 *Номер:* `{order.tracking_number}`
👤 *Клиент:* {order.customer_name}

📊 *Статус изменен:*
❌ Было: {status_map.get(old_status, old_status)}
✅ Стало: {status_map.get(new_status, new_status)}

🕐 *Обновлено:* {order.updated_at.strftime('%d.%m.%Y %H:%M')}
"""

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        
        data = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': message_text,
            'parse_mode': 'Markdown'
        }
        
        response = requests.post(url, data=data, timeout=10)
        
        if response.status_code == 200:
            logging.info(f"Status update notification sent for order {order.tracking_number}")
            return True
        else:
            logging.error(f"Failed to send status update notification: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logging.error(f"Error sending status update notification: {e}")
        return False
