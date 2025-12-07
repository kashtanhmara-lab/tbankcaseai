import openai
import os
import json
import re
from datetime import datetime, timedelta
import requests
from typing import Optional, Dict, List
import time

class OpenAIPriceEstimator:
    def __init__(self, api_key: str):
        """Инициализация с ключом OpenAI"""
        if api_key == "dummy_key" or not api_key:
            self.api_key = None
            self.openai_available = False
            print("[PRICE] OpenAI не доступен, используется fallback режим")
        else:
            openai.api_key = api_key
            self.api_key = api_key
            self.openai_available = True
            print("[PRICE] OpenAI Price Estimator инициализирован")
        
        self.cache_file = "price_cache.json"
        self.price_cache = self.load_cache()
    
    def load_cache(self) -> Dict:
        """Загружает кэш цен из файла"""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                    
                    cleaned_cache = {}
                    current_time = datetime.now().isoformat()
                    
                    for key, data in cache.items():
                        if "timestamp" in data:
                            cache_time = datetime.fromisoformat(data["timestamp"])
                            if datetime.now() - cache_time < timedelta(days=7):
                                cleaned_cache[key] = data
                    
                    return cleaned_cache
        except Exception as e:
            print(f"[CACHE] Ошибка загрузки кэша: {e}")
        return {}
    
    def save_cache(self):
        """Сохраняет кэш в файл"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.price_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[CACHE] Ошибка сохранения кэша: {e}")
    
    def get_cache_key(self, item_name: str, category: str, condition: str) -> str:
        """Создает ключ для кэша"""
        key = f"{category.lower()}_{item_name.lower()}_{condition.lower()}"
        key = re.sub(r'[^a-zа-я0-9_]', '', key)
        return key
    
    def get_cached_price(self, item_name: str, category: str, condition: str) -> Optional[int]:
        """Получает цену из кэша"""
        cache_key = self.get_cache_key(item_name, category, condition)
        if cache_key in self.price_cache:
            cache_data = self.price_cache[cache_key]
            print(f"[CACHE] Найдена в кэше: {item_name} -> {cache_data['price']} ₽")
            return cache_data["price"]
        return None
    
    def save_to_cache(self, item_name: str, category: str, condition: str, price: int, source: str):
        """Сохраняет цену в кэш"""
        cache_key = self.get_cache_key(item_name, category, condition)
        self.price_cache[cache_key] = {
            "price": price,
            "category": category,
            "item_name": item_name,
            "condition": condition,
            "source": source,
            "timestamp": datetime.now().isoformat()
        }
        self.save_cache()
    
    def estimate_with_openai(self, item_name: str, category: str, condition: str) -> Optional[int]:
        """Оценивает цену с помощью OpenAI"""
        if not self.openai_available:
            return None
            
        try:
            prompt = f"""Ты - эксперт по ценам на российских маркетплейсах (Wildberries, OZON, Яндекс.Маркет).
            
            Товар: {item_name}
            Категория: {category}
            Состояние: {condition}
            
            Проанализируй и оцени примерную стоимость этого товара на российском рынке в рублях.
            
            Учти:
            1. Реальные цены на маркетплейсах
            2. Состояние товара ({condition})
            3. Популярность бренда и модели
            4. Текущие рыночные тренды
            
            Ответь ТОЛЬКО числом в рублях, без текста, без символа ₽.
            
            Примеры:
            Вопрос: "Наушники Razer Kraken, Электроника, Новая"
            Ответ: 7990
            
            Вопрос: "iPhone 15 Pro, Электроника, Новая"
            Ответ: 119990
            
            Вопрос: "Диван IKEA, Дом и ремонт, Новая"
            Ответ: 34990
            
            Вопрос: "Кроссовки Nike Air Max, Одежда и обувь, Новая"
            Ответ: 12990
            
            Твой ответ:"""
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Ты - эксперт по ценам на российских маркетплейсах. Отвечай только числом."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=50
            )
            
            answer = response.choices[0].message.content.strip()
            
            numbers = re.findall(r'\d+', answer.replace(' ', ''))
            if numbers:
                price = int(numbers[0])
                print(f"[OPENAI] Оценка OpenAI: {item_name} -> {price} ₽")
                return price
            
            return None
            
        except Exception as e:
            print(f"[OPENAI] Ошибка при запросе к OpenAI: {e}")
            return None
    
    def estimate_price(self, item_name: str, category: str, condition: str) -> int:
        """Основная функция оценки цены"""
        print(f"\n[PRICE] Оценка: {item_name} ({category}, {condition})")
        
        cached_price = self.get_cached_price(item_name, category, condition)
        if cached_price is not None:
            return cached_price
        
        price = None
        source = "cache"
        
        if self.openai_available:
            openai_price = self.estimate_with_openai(item_name, category, condition)
            if openai_price:
                price = openai_price
                source = "openai"
        
        if price is None:
            price = self.fallback_estimate(item_name, category, condition)
            source = "fallback"
        
        if condition == "Б/у":
            price = self.apply_condition_discount(price, category)
        
        price = self.round_to_marketplace_price(price)
        
        self.save_to_cache(item_name, category, condition, price, source)
        
        print(f"[PRICE] Итоговая цена: {price:,} ₽ (источник: {source})".replace(",", " "))
        return price
    
    def fallback_estimate(self, item_name: str, category: str, condition: str) -> int:
        """Fallback оценка, если API не сработали"""
        category_prices = {
            "Электроника": 25000,
            "Одежда и обувь": 5000,
            "Бытовая техника": 20000,
            "Автомобиль": 50000,
            "Путешествия": 30000,
            "Образование": 15000,
            "Здоровье и спорт": 10000,
            "Дом и ремонт": 15000,
            "Хобби и развлечения": 12000,
        }
        
        base_price = category_prices.get(category, 10000)
        
        item_lower = item_name.lower()
        
        premium_brands = ["apple", "sony", "dyson", "bosch", "miele", "gucci", "louis vuitton"]
        for brand in premium_brands:
            if brand in item_lower:
                base_price *= 2
                break
        
        budget_brands = ["xiaomi", "huawei", "poco", "realme", "bork", "polaris"]
        for brand in budget_brands:
            if brand in item_lower:
                base_price *= 0.7
                break
        
        return int(base_price)
    
    def apply_condition_discount(self, price: int, category: str) -> int:
        """Применяет скидку на состояние Б/у"""
        discounts = {
            "Электроника": 0.4,
            "Одежда и обувь": 0.3,
            "Бытовая техника": 0.35,
            "Автомобиль": 0.5,
            "Дом и ремонт": 0.25,
            "default": 0.3
        }
        
        discount = discounts.get(category, discounts["default"])
        discounted_price = int(price * (1 - discount))
        
        min_prices = {
            "Электроника": 1000,
            "Одежда и обувь": 500,
            "Бытовая техника": 3000,
            "default": 500
        }
        
        min_price = min_prices.get(category, min_prices["default"])
        return max(discounted_price, min_price)
    
    def round_to_marketplace_price(self, price: int) -> int:
        """Округляет цену как на маркетплейсах"""
        if price < 1000:
            return ((price + 25) // 50) * 50
        elif price < 10000:
            last_two = price % 100
            if last_two < 50:
                return price - last_two + 90
            else:
                return price - last_two + 190
        else:
            last_three = price % 1000
            if last_three < 500:
                return price - last_three + 990
            else:
                return price - last_three + 1990