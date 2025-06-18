import requests
import json
from datetime import datetime
import logging

class AmoCRMIntegration:
    def __init__(self):
        # Данные интеграции amoCRM
        self.client_id = "c48e1e09-855a-47c2-8d7c-2ca33e168b1c"
        self.client_secret = "wgeSGmOD4GVijBNBKOdtI58B7Zuxtw2lrnMbY0M2Asb47rnvrhmLYORIaQeVP4rQ"
        self.subdomain = "dsekbhvac"  # Ваш поддомен
        self.base_url = f"https://{self.subdomain}.amocrm.ru"
        self.access_token = None
        self.refresh_token = None
        
    def get_access_token(self, auth_code):
        """Получение access token по коду авторизации"""
        url = f"{self.base_url}/oauth2/access_token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "authorization_code",
            "code": auth_code,
            "redirect_uri": "https://example.com"
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens["refresh_token"]
            return True
        return False
    
    def refresh_access_token(self):
        """Обновление access token"""
        url = f"{self.base_url}/oauth2/access_token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "grant_type": "refresh_token",
            "refresh_token": self.refresh_token,
            "redirect_uri": "https://example.com"
        }
        
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            tokens = response.json()
            self.access_token = tokens["access_token"]
            self.refresh_token = tokens["refresh_token"]
            return True
        return False
    
    def create_contact(self, name, phone, telegram_id):
        """Создание контакта в amoCRM"""
        url = f"{self.base_url}/api/v4/contacts"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Подготовка данных контакта
        contact_data = [{
            "name": name,
            "custom_fields_values": [
                {
                    "field_id": 264911,  # ID поля телефона
                    "values": [{"value": phone, "enum_code": "WORK"}]
                },
                {
                    "field_id": 264913,  # ID поля Telegram
                    "values": [{"value": f"@{telegram_id}"}]
                }
            ]
        }]
        
        response = requests.post(url, headers=headers, json=contact_data)
        
        if response.status_code == 200:
            return response.json()["_embedded"]["contacts"][0]["id"]
        return None
    
    def create_deal(self, contact_id, service_type, description, amount=0):
        """Создание сделки в amoCRM"""
        url = f"{self.base_url}/api/v4/leads"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Определяем название сделки
        deal_name = f"HVAC заявка - {service_type}"
        
        deal_data = [{
            "name": deal_name,
            "price": amount,
            "pipeline_id": 123456,  # ID воронки продаж
            "status_id": 789012,    # ID этапа "Новая заявка"
            "_embedded": {
                "contacts": [{"id": contact_id}]
            },
            "custom_fields_values": [
                {
                    "field_id": 123456,  # ID поля "Тип услуги"
                    "values": [{"value": service_type}]
                },
                {
                    "field_id": 123457,  # ID поля "Описание"
                    "values": [{"value": description}]
                }
            ]
        }]
        
        response = requests.post(url, headers=headers, json=deal_data)
        
        if response.status_code == 200:
            return response.json()["_embedded"]["leads"][0]["id"]
        return None
    
    def create_task(self, deal_id, contact_id, task_text):
        """Создание задачи в amoCRM"""
        url = f"{self.base_url}/api/v4/tasks"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Создаем задачу на завтра
        complete_till = int(datetime.now().timestamp()) + 86400
        
        task_data = [{
            "text": task_text,
            "complete_till": complete_till,
            "entity_id": deal_id,
            "entity_type": "leads",
            "task_type_id": 1  # Обычная задача
        }]
        
        response = requests.post(url, headers=headers, json=task_data)
        return response.status_code == 200
    
    def process_telegram_request(self, user_data):
        """Основная функция обработки заявки из Telegram"""
        try:
            # Извлекаем данные
            name = user_data.get("name", "Неизвестно")
            phone = user_data.get("phone", "")
            telegram_id = user_data.get("telegram_id", "")
            service_type = user_data.get("service_type", "Общая заявка")
            description = user_data.get("description", "")
            
            # 1. Создаем контакт
            contact_id = self.create_contact(name, phone, telegram_id)
            if not contact_id:
                logging.error("Не удалось создать контакт")
                return False
            
            # 2. Создаем сделку
            deal_id = self.create_deal(contact_id, service_type, description)
            if not deal_id:
                logging.error("Не удалось создать сделку")
                return False
            
            # 3. Создаем задачу
            task_text = f"Связаться с клиентом {name} по заявке: {service_type}"
            self.create_task(deal_id, contact_id, task_text)
            
            logging.info(f"Успешно создана сделка {deal_id} для контакта {contact_id}")
            return True
            
        except Exception as e:
            logging.error(f"Ошибка при обработке заявки: {e}")
            return False

# Глобальный экземпляр интеграции
amocrm = AmoCRMIntegration()
