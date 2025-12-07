import json
from datetime import datetime, timedelta

class CoolingManager:
    def __init__(self, auth_system):
        self.auth = auth_system
    
    def calculate_cooling_period(self, price, category, item_name=""):
        """Рассчитывает период охлаждения"""
        if not self.auth.current_user:
            return self.get_default_result(price, category, item_name)
            
        user_data = self.auth.get_user_data(self.auth.current_user)
        
        # 1. Проверка запрещенной категории
        forbidden_categories = user_data.get("forbidden_categories", [])
        if category in forbidden_categories:
            return {
                "recommended": False,
                "reason": "Запрещенная категория",
                "message": f"❌ **Категория '{category}' находится в вашем списке запрещенных покупок**\n\nРекомендуем отказаться от этой покупки. Вы добавили эту категорию в список запрещенных, что говорит о желании контролировать подобные траты.",
                "cooling_days": 0,
                "savings_based_days": 0,
                "total_days": 0
            }
        
        # 2. Расчет дней охлаждения на основе цены
        cooling_periods = user_data.get("cooling_periods", [])
        price_days = 0
        
        for period in cooling_periods:
            min_price = period.get("min_price", 0)
            max_price = period.get("max_price", 0)
            days = period.get("days", 0)
            
            if min_price <= price <= max_price:
                price_days = days
                break
        
        # 3. Расчет дней на основе накоплений (если включено)
        savings_days = 0
        consider_savings = user_data.get("consider_savings", True)
        
        if consider_savings:
            savings_days = self.calculate_savings_based_days(price, user_data)
        
        # 4. Итоговый период охлаждения
        total_days = max(price_days, savings_days)
        
        if total_days <= 0:
            return {
                "recommended": True,
                "reason": "Можно покупать сразу",
                "message": f"✅ **Анализ завершен: {item_name}**\n\n💰 **Цена:** {price:,} ₽\n📁 **Категория:** {category}\n\n📊 **Рекомендации:**\n• По цене: можно покупать сразу\n\n💡 **Советы:**\n1. Убедитесь, что товар вам действительно нужен\n2. Проверьте наличие акций и скидок\n3. Сравните цены в других магазинах".replace(",", " "),
                "cooling_days": price_days,
                "savings_based_days": savings_days,
                "total_days": 0
            }
        
        # Формирование сообщения
        message = self.generate_recommendation_message(
            price, category, item_name, price_days, savings_days, total_days
        )
        
        return {
            "recommended": True,
            "reason": "Требуется охлаждение",
            "message": message,
            "cooling_days": price_days,
            "savings_based_days": savings_days,
            "total_days": total_days
        }
    
    def get_default_result(self, price, category, item_name):
        """Возвращает результат по умолчанию, если нет пользователя"""
        return {
            "recommended": True,
            "reason": "Стандартный анализ",
            "message": f"✅ **Анализ: {item_name}**\n\n💰 **Цена:** {price:,} ₽\n📁 **Категория:** {category}\n\n⏱️ **Рекомендуемый период охлаждения:** 7 дней\n\n💡 **Советы:**\n1. Подождите неделю перед покупкой\n2. Проверьте, действительно ли вам нужен этот товар\n3. Ищите альтернативы и скидки".replace(",", " "),
            "cooling_days": 7,
            "savings_based_days": 0,
            "total_days": 7
        }
    
    def calculate_savings_based_days(self, price, user_data):
        """Рассчитывает дни на основе накоплений"""
        profile = user_data.get("personal_profile", {})
        
        current_savings = profile.get("current_savings", 0)
        savings_per_month = profile.get("savings_per_month", 0)
        
        if savings_per_month <= 0:
            return 0
        
        shortage = max(0, price - current_savings)
        
        if shortage <= 0:
            return 0
        
        daily_savings = savings_per_month / 30
        days_needed = int(shortage / daily_savings) + 1
        
        return days_needed
    
    def generate_recommendation_message(self, price, category, item_name, price_days, savings_days, total_days):
        """Генерирует рекомендательное сообщение"""
        message = f"🎯 **Анализ завершен: {item_name}**\n\n"
        message += f"💰 **Цена:** {price:,} ₽\n".replace(",", " ")
        message += f"📁 **Категория:** {category}\n\n"
        
        message += f"📊 **Рекомендации:**\n"
        
        if price_days > 0:
            message += f"• По цене: подумайте {price_days} дней\n"
        
        if savings_days > 0:
            message += f"• По накоплениям: потребуется {savings_days} дней\n"
        
        message += f"\n⏱️ **Итоговый период охлаждения:** {total_days} дней\n"
        
        if total_days > 0:
            purchase_date = datetime.now() + timedelta(days=total_days)
            message += f"📅 **Можете купить:** {purchase_date.strftime('%d.%m.%Y')}\n"
        
        user_data = self.auth.get_user_data(self.auth.current_user)
        profile = user_data.get("personal_profile", {})
        savings_per_month = profile.get("savings_per_month", 0)
        
        if savings_per_month > 0:
            daily_save = savings_per_month / 30
            days_to_save = int(price / daily_save) + 1
            message += f"\n💵 **Накопления:**\n"
            message += f"• При откладывании {int(daily_save):,} ₽/день: {days_to_save} дней\n".replace(",", " ")
        
        message += f"\n💡 **Советы:**\n"
        message += f"1. Используйте это время для поиска альтернатив\n"
        message += f"2. Проверьте, не появились ли акции\n"
        message += f"3. Убедитесь, что товар вам действительно нужен\n"
        message += f"4. Рассмотрите покупку аналогичного товара б/у\n"
        message += f"5. Сравните цены в разных магазинах\n"
        
        return message
    
    def create_purchase_item(self, item_name, price, category, cooling_result):
        """Создает объект покупки для сохранения"""
        total_days = cooling_result["total_days"]
        
        # Всегда создаем со статусом "cooling" (на охлаждении)
        purchase_item = {
            "id": f"item_{int(datetime.now().timestamp())}_{category[:3].lower()}",
            "name": item_name,
            "price": price,
            "category": category,
            "cooling_days": total_days,
            "cooling_until": (datetime.now() + timedelta(days=total_days)).strftime("%Y-%m-%d %H:%M:%S"),
            "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": "cooling",  # Всегда "cooling" при создании
            "notified": False,
            "last_notification": None,
            "current_savings": 0,
            "savings_target": price,
            "purchased_at": None
        }
        
        return purchase_item