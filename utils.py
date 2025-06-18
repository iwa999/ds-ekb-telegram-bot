"""
Вспомогательные функции и утилиты
"""

import logging
import re
from typing import Dict, Optional
from telegram import Update
from config import Config

def setup_logging() -> None:
    """Настройка системы логирования"""
    config = Config()
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT,
        handlers=[
            logging.StreamHandler(),
        ]
    )
    
    # Отключаем избыточное логирование библиотек
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)

def extract_user_data(update: Update) -> Dict:
    """Извлечение данных пользователя из сообщения"""
    user = update.effective_user
    message = update.message
    
    # Базовые данные
    user_data = {
        'user_id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'message': message.text or message.caption or "Без текста",
        'telegram': f"@{user.username}" if user.username else f"ID: {user.id}",
        'name': "",
        'phone': "",
        'email': ""
    }
    
    # Формируем полное имя
    name_parts = []
    if user.first_name:
        name_parts.append(user.first_name)
    if user.last_name:
        name_parts.append(user.last_name)
    user_data['name'] = " ".join(name_parts) or f"Пользователь {user.id}"
    
    # Извлекаем телефон из текста сообщения
    if phone := extract_phone(message.text or ""):
        user_data['phone'] = phone
    
    # Извлекаем email из текста сообщения
    if email := extract_email(message.text or ""):
        user_data['email'] = email
    
    return user_data

def extract_phone(text: str) -> Optional[str]:
    """Извлечение номера телефона из текста"""
    if not text:
        return None
    
    # Различные форматы телефонов
    phone_patterns = [
        r'\+7[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{2})[\s\-\(\)]?(\d{2})',
        r'8[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{2})[\s\-\(\)]?(\d{2})',
        r'7[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{2})[\s\-\(\)]?(\d{2})',
        r'(\d{3})[\s\-\(\)]?(\d{3})[\s\-\(\)]?(\d{2})[\s\-\(\)]?(\d{2})'
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, text)
        if match:
            # Нормализуем номер
            digits = ''.join(match.groups())
            if len(digits) == 10:
                return f"+7{digits}"
            elif len(digits) == 11 and digits.startswith('7'):
                return f"+{digits}"
    
    return None

def extract_email(text: str) -> Optional[str]:
    """Извлечение email из текста"""
    if not text:
        return None
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    match = re.search(email_pattern, text)
    
    return match.group() if match else None

def format_message(template: str, **kwargs) -> str:
    """Форматирование сообщения с подстановкой переменных"""
    try:
        return template.format(**kwargs)
    except KeyError as e:
        logging.error(f"❌ Ошибка форматирования сообщения: отсутствует ключ {e}")
        return template

def clean_text(text: str) -> str:
    """Очистка текста от лишних символов"""
    if not text:
        return ""
    
    # Удаляем лишние пробелы и переносы
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Удаляем потенциально опасные символы
    text = re.sub(r'[<>"\'\x00-\x1f\x7f-\x9f]', '', text)
    
    return text

def validate_phone(phone: str) -> bool:
    """Валидация номера телефона"""
    if not phone:
        return False
    
    # Убираем все символы кроме цифр и +
    clean_phone = re.sub(r'[^\d+]', '', phone)
    
    # Проверяем длину и формат
    if len(clean_phone) == 12 and clean_phone.startswith('+7'):
        return True
    elif len(clean_phone) == 11 and clean_phone.startswith('7'):
        return True
    elif len(clean_phone) == 10:
        return True
    
    return False

def get_service_emoji(service_type: str) -> str:
    """Получение эмодзи для типа услуги"""
    service_emojis = {
        'вентиляция': '🌪️',
        'кондиционер': '❄️',
        'холодильное': '🧊',
        'общая': '🔧'
    }
    
    service_lower = service_type.lower()
    
    for key, emoji in service_emojis.items():
        if key in service_lower:
            return emoji
    
    return '🔧'

def truncate_text(text: str, max_length: int = 100) -> str:
    """Обрезка текста до указанной длины"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def is_business_hours() -> bool:
    """Проверка рабочего времени"""
    from datetime import datetime
    
    now = datetime.now()
    
    # Рабочие часы: 8:00 - 20:00
    if 8 <= now.hour < 20:
        return True
    
    return False

def format_phone_display(phone: str) -> str:
    """Форматирование телефона для отображения"""
    if not phone:
        return ""
    
    # Убираем все кроме цифр
    digits = re.sub(r'\D', '', phone)
    
    if len(digits) == 11 and digits.startswith('7'):
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"
    elif len(digits) == 10:
        return f"+7 ({digits[0:3]}) {digits[3:6]}-{digits[6:8]}-{digits[8:10]}"
    
    return phone
