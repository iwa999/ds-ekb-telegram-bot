"""
Конфигурация проекта DS EKB Bot
Все настройки и токены
"""

import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class Config:
    """Класс конфигурации бота"""
    
    # Telegram Bot
    TELEGRAM_TOKEN: str = "7437623986:AAFj-sItRC4s889Sop2mglRE7SE2c-drTCY"
    
    # amoCRM
    AMOCRM_SUBDOMAIN: str = "ekbamodseru"
    AMOCRM_TOKEN: str = "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImp0aSI6ImI4YWFlMGU1ODA2Nzc1MDAzMjFmMjlhNDYyODI1ZTQ3NjY3MDNkOThjOGE2NDQ1YTNhNTg1M2Y5NDg3YWJjMzU4MGIyNDhmMTAzZjdkZmFmIn0.eyJhdWQiOiJjNDhlMWUwOS04NTVhLTQ3YzItOGQ3Yy0yY2EzM2UxNjhiMWMiLCJqdGkiOiJiOGFhZTBlNTgwNjc3NTAwMzIxZjI5YTQ2MjgyNWU0NzY2NzAzZDk4YzhhNjQ0NWEzYTU4NTNmOTQ4N2FiYzM1ODBiMjQ4ZjEwM2Y3ZGZhZiIsImlhdCI6MTc1MDI2MzQyNSwibmJmIjoxNzUwMjYzNDI1LCJleHAiOjE4NDIzMDcyMDAsInN1YiI6IjEyNjQwMzA2IiwiZ3JhbnRfdHlwZSI6IiIsImFjY291bnRfaWQiOjMyNDk0NTU4LCJiYXNlX2RvbWFpbiI6ImFtb2NybS5ydSIsInZlcnNpb24iOjIsInNjb3BlcyI6WyJjcm0iLCJmaWxlcyIsImZpbGVzX2RlbGV0ZSIsIm5vdGlmaWNhdGlvbnMiLCJwdXNoX25vdGlmaWNhdGlvbnMiXSwiaGFzaF91dWlkIjoiMDBiZDI4ZTMtYTllZS00ZmFiLWI5N2MtYjk0OTdiMDY2MzY4IiwiYXBpX2RvbWFpbiI6ImFwaS1iLmFtb2NybS5ydSJ9.HvgSDyxs_Lw0opRU7XW95zv1L65Mz-F0XAXdUl_Xwddx6pqP2OXUPXAK-Gr-k85-8nZUV0rtp9fkXHpVh6GpJrKgrnhNCWkv5YHBx29TJj8G-mQEomfrHFv-uzMQt6DY4cktWPAytRqXdloYbv4c_hkMElbqt5M8-fY3GAJY3xLrqzpDtclUh-Hcfyun6-st23-hHdJDWAWCrZxLYK7LcHICZ9XG8EXrx-rNVW_OSRponiYacNAVDW30n-F5hgOdnhrfxAKa-ies35ZakaAHLWtezFl-DP4d0mIQWEVJfeuBAA2LsQng-ct1jbzCnhEGISR4RVviTLufiQrBR9Qp2Q"
    
    # API URLs
    @property
    def AMOCRM_API_URL(self) -> str:
        return f"https://{self.AMOCRM_SUBDOMAIN}.amocrm.ru/api/v4"
    
    # Настройки бота
    BOT_USERNAME: str = "@dsekb_assistant_bot"
    COMPANY_NAME: str = "ДС ЕКБ"
    COMPANY_PHONE: str = "+7 922 130-83-65"
    
    # Сообщения
    WELCOME_MESSAGE: str = (
        "🔧 Добро пожаловать в ДС ЕКБ!\n\n"
        "Мы предоставляем профессиональные услуги:\n"
        "• Обслуживание вентиляции\n"
        "• Ремонт кондиционеров\n"
        "• Холодильное оборудование\n\n"
        "💬 Опишите вашу проблему или задачу, и мы поможем!"
    )
    
    SUCCESS_MESSAGE: str = (
        "✅ Заявка принята!\n\n"
        "📋 Номер заявки: #{deal_id}\n"
        "📞 Ожидайте звонка в течение 30 минут\n"
        "🕐 Рабочие часы: 8:00-20:00\n\n"
        "Спасибо за обращение к ДС ЕКБ!"
    )
    
    ERROR_MESSAGE: str = (
        "⚠️ Временные технические неполадки\n\n"
        "📞 Пожалуйста, позвоните: +7 922 130-83-65\n"
        "💬 Или попробуйте написать позже\n\n"
        "Извините за неудобства!"
    )
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Таймауты
    API_TIMEOUT: int = 30
    RETRY_COUNT: int = 3
    RETRY_DELAY: int = 1
