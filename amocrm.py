"""
Модуль для работы с API amoCRM
Создание сделок, контактов, задач
"""

import asyncio
import aiohttp
import logging
from typing import Dict, Optional, Tuple
from datetime import datetime
from config import Config

logger = logging.getLogger(__name__)

class AmoCRMClient:
    """Клиент для работы с amoCRM API"""
    
    def __init__(self):
        self.config = Config()
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.API_TIMEOUT),
            headers={
                'Authorization': f'Bearer {self.config.AMOCRM_TOKEN}',
                'Content-Type': 'application/json'
            }
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()

    async def create_contact(self, user_data: Dict) -> Optional[int]:
        """Создание контакта в amoCRM"""
        try:
            contact_data = {
                "name": user_data.get('name', f"Клиент {user_data.get('user_id', 'Unknown')}"),
                "custom_fields_values": []
            }
            
            # Добавляем телефон если есть
            if phone := user_data.get('phone'):
                contact_data["custom_fields_values"].append({
                    "field_code": "PHONE",
                    "values": [{"value": phone, "enum_code": "WORK"}]
                })
            
            # Добавляем Telegram
            if telegram := user_data.get('telegram'):
                contact_data["custom_fields_values"].append({
                    "field_code": "IM",
                    "values": [{"value": telegram, "enum_code": "TELEGRAM"}]
                })
            
            url = f"{self.config.AMOCRM_API_URL}/contacts"
            
            async with self.session.post(url, json=[contact_data]) as response:
                if response.status == 200:
                    result = await response.json()
                    contact_id = result['_embedded']['contacts'][0]['id']
                    logger.info(f"✅ Контакт создан: ID {contact_id}")
                    return contact_id
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка создания контакта: {response.status} - {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Исключение при создании контакта: {e}")
            return None

    async def create_deal(self, user_data: Dict, contact_id: Optional[int] = None) -> Tuple[Optional[int], str]:
        """Создание сделки в amoCRM"""
        try:
            # Формируем название сделки
            service_type = self._detect_service_type(user_data.get('message', ''))
            deal_name = f"HVAC заявка - {service_type}"
            
            deal_data = {
                "name": deal_name,
                "price": 0,
                "custom_fields_values": [
                    {
                        "field_code": "DESCRIPTION",
                        "values": [{"value": user_data.get('message', 'Заявка из Telegram')}]
                    }
                ]
            }
            
            # Привязываем контакт если есть
            if contact_id:
                deal_data["_embedded"] = {
                    "contacts": [{"id": contact_id}]
                }
            
            url = f"{self.config.AMOCRM_API_URL}/leads"
            
            async with self.session.post(url, json=[deal_data]) as response:
                if response.status == 200:
                    result = await response.json()
                    deal_id = result['_embedded']['leads'][0]['id']
                    logger.info(f"✅ Сделка создана: ID {deal_id}")
                    
                    # Создаем задачу для менеджера
                    await self._create_task(deal_id, user_data)
                    
                    return deal_id, f"#{deal_id}"
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Ошибка создания сделки: {response.status} - {error_text}")
                    return None, "Временно недоступен"
                    
        except Exception as e:
            logger.error(f"❌ Исключение при создании сделки: {e}")
            return None, "Техническая ошибка"

    async def _create_task(self, deal_id: int, user_data: Dict) -> None:
        """Создание задачи для менеджера"""
        try:
            task_data = {
                "text": f"Новая HVAC заявка\n\nКлиент: {user_data.get('name', 'Не указано')}\nТелефон: {user_data.get('phone', 'Не указано')}\nПроблема: {user_data.get('message', 'Не указано')}\n\nTelegram: {user_data.get('telegram', 'Не указано')}",
                "complete_till": int((datetime.now().timestamp() + 1800)),  # +30 минут
                "entity_id": deal_id,
                "entity_type": "leads"
            }
            
            url = f"{self.config.AMOCRM_API_URL}/tasks"
            
            async with self.session.post(url, json=[task_data]) as response:
                if response.status == 200:
                    logger.info(f"✅ Задача создана для сделки {deal_id}")
                else:
                    logger.error(f"❌ Ошибка создания задачи: {response.status}")
                    
        except Exception as e:
            logger.error(f"❌ Ошибка создания задачи: {e}")

    def _detect_service_type(self, message: str) -> str:
        """Определение типа услуги по сообщению"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['вентиляция', 'воздух', 'приток', 'вытяжка']):
            return "Вентиляция"
        elif any(word in message_lower for word in ['кондиционер', 'сплит', 'охлаждение', 'freon']):
            return "Кондиционеры"
        elif any(word in message_lower for word in ['холодильник', 'морозильник', 'чиллер']):
            return "Холодильное"
        else:
            return "Общая"

    async def get_deal_status(self, deal_id: int) -> Optional[str]:
        """Получение статуса сделки"""
        try:
            url = f"{self.config.AMOCRM_API_URL}/leads/{deal_id}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    result = await response.json()
                    status_id = result['status_id']
                    # Здесь можно добавить маппинг статусов
                    return f"Статус: {status_id}"
                else:
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Ошибка получения статуса: {e}")
            return None

# Вспомогательная функция для использования в других модулях
async def process_user_request(user_data: Dict) -> Tuple[bool, str, Optional[str]]:
    """
    Обработка заявки пользователя
    Returns: (success, message, deal_number)
    """
    try:
        async with AmoCRMClient() as client:
            # Создаем контакт
            contact_id = await client.create_contact(user_data)
            
            # Создаем сделку
            deal_id, deal_number = await client.create_deal(user_data, contact_id)
            
            if deal_id:
                success_msg = Config.SUCCESS_MESSAGE.format(deal_id=deal_number)
                return True, success_msg, deal_number
            else:
                return False, Config.ERROR_MESSAGE, None
                
    except Exception as e:
        logger.error(f"❌ Критическая ошибка обработки заявки: {e}")
        return False, Config.ERROR_MESSAGE, None
