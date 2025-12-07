import json
import os
from datetime import datetime
import uuid

USERS_FILE = "users.json"

class AuthSystem:
    def __init__(self):
        self.current_user = None
        self.users = self.load_users()
    
    def load_users(self):
        """Загружает пользователей из файла"""
        try:
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            print(f"[ERROR] Ошибка загрузки пользователей: {e}")
        return {}
    
    def save_users(self):
        """Сохраняет пользователей в файл"""
        try:
            with open(USERS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.users, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка сохранения пользователей: {e}")
            return False
    
    def create_new_user(self, username):
        """Создает нового пользователя по никнейму"""
        if username in self.users:
            return False, "Пользователь с таким никнеймом уже существует"
        
        if not username or len(username.strip()) < 2:
            return False, "Никнейм должен быть не менее 2 символов"
        
        if len(username) > 20:
            return False, "Никнейм не должен превышать 20 символов"
        
        # Создаем базовую структуру пользователя без пароля
        self.users[username] = {
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "last_login": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "is_first_time": True,
            "personal_profile": {
                "monthly_income": 0,
                "savings_per_month": 0,
                "current_savings": 0,
                "filling_completed": False
            },
            "forbidden_categories": [],
            "cooling_periods": [
                {"min_price": 0, "max_price": 5000, "days": 1},
                {"min_price": 5001, "max_price": 20000, "days": 3},
                {"min_price": 20001, "max_price": 50000, "days": 7},
                {"min_price": 50001, "max_price": 100000, "days": 14},
                {"min_price": 100001, "max_price": 200000, "days": 30},
                {"min_price": 200001, "max_price": 500000, "days": 60},
                {"min_price": 500001, "max_price": 1000000, "days": 90}
            ],
            "notification_settings": {
                "enabled": True,
                "frequency_days": 7,
                "excluded_items": [],
                "channel": "in_app"
            },
            "consider_savings": True,
            "purchases": []
        }
        
        self.save_users()
        return True, "Новый пользователь создан"
    
    def login(self, username):
        """Вход пользователя по никнейму"""
        if not username or len(username.strip()) < 2:
            return False, "Введите никнейм"
        
        if username in self.users:
            self.users[username]["last_login"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.current_user = username
            self.save_users()
            return True, f"Добро пожаловать, {username}!"
        else:
            success, message = self.create_new_user(username)
            if success:
                self.current_user = username
                return True, f"Новый пользователь {username} создан!"
            else:
                return False, message
    
    def logout(self):
        """Выход пользователя"""
        self.current_user = None
        return True
    
    def is_first_time_user(self, username):
        """Проверяет, является ли пользователь новым (нужно заполнить анкету)"""
        if username in self.users:
            return self.users[username].get("is_first_time", True)
        return True
    
    def get_user_data(self, username):
        """Получает данные пользователя"""
        return self.users.get(username, {}).copy()
    
    def update_user_data(self, username, data):
        """Обновляет данные пользователя"""
        if username in self.users:
            for key, value in data.items():
                if key in self.users[username]:
                    if isinstance(self.users[username][key], dict) and isinstance(value, dict):
                        self.users[username][key].update(value)
                    else:
                        self.users[username][key] = value
                else:
                    self.users[username][key] = value
            
            self.save_users()
            return True
        return False
    
    def complete_first_time_setup(self, username, profile_data):
        """Завершает первоначальную настройку пользователя"""
        if username in self.users:
            if "personal_profile" not in self.users[username]:
                self.users[username]["personal_profile"] = {}
            
            self.users[username]["personal_profile"].update(profile_data)
            self.users[username]["personal_profile"]["filling_completed"] = True
            self.users[username]["is_first_time"] = False
            
            self.save_users()
            return True
        return False
    
    def add_purchase(self, username, purchase_data):
        """Добавляет покупку пользователю"""
        if username in self.users:
            if "purchases" not in self.users[username]:
                self.users[username]["purchases"] = []
            
            if "id" not in purchase_data:
                purchase_data["id"] = f"item_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}"
            
            # Все новые покупки - на охлаждении
            if "status" not in purchase_data:
                purchase_data["status"] = "cooling"
            
            # Обязательные поля
            defaults = {
                "added_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "notified": False,
                "last_notification": None,
                "current_savings": 0,
                "savings_target": purchase_data.get("price", 0),
                "purchased_at": None
            }
            
            for key, value in defaults.items():
                if key not in purchase_data:
                    purchase_data[key] = value
            
            # Автоматически проверяем, не накопили ли уже достаточно
            current_savings = purchase_data.get("current_savings", 0)
            savings_target = purchase_data.get("savings_target", purchase_data.get("price", 0))
            
            if current_savings >= savings_target:
                purchase_data["status"] = "purchased"
                purchase_data["purchased_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"[AUTH] Покупка '{purchase_data.get('name')}' сразу куплена (накопления {current_savings} >= {savings_target})")
            
            print(f"[AUTH] Добавлена покупка: {purchase_data.get('name')}, статус: {purchase_data.get('status')}")
            
            self.users[username]["purchases"].append(purchase_data)
            self.save_users()
            return True
        return False
    
    def update_purchase(self, username, purchase_id, update_data):
        """Обновляет покупку пользователя с проверкой накоплений"""
        if username in self.users and "purchases" in self.users[username]:
            for purchase in self.users[username]["purchases"]:
                if purchase.get("id") == purchase_id:
                    # Сохраняем текущие данные
                    old_status = purchase.get("status", "cooling")
                    
                    # Обновляем данные
                    purchase.update(update_data)
                    
                    # Проверяем: если накопления достигли цели - меняем статус
                    if old_status == "cooling":
                        current_savings = purchase.get("current_savings", 0)
                        savings_target = purchase.get("savings_target", purchase.get("price", 0))
                        
                        if current_savings >= savings_target:
                            purchase["status"] = "purchased"
                            purchase["purchased_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            print(f"[AUTH] Покупка '{purchase.get('name')}' теперь куплена! Накопления: {current_savings}/{savings_target}")
                    
                    self.save_users()
                    return True
        return False
    
    def delete_purchase(self, username, purchase_id):
        """Удаляет покупку пользователя"""
        if username in self.users and "purchases" in self.users[username]:
            initial_length = len(self.users[username]["purchases"])
            self.users[username]["purchases"] = [
                p for p in self.users[username]["purchases"] if p.get("id") != purchase_id
            ]
            if len(self.users[username]["purchases"]) < initial_length:
                self.save_users()
                return True
        return False
    
    def get_purchase(self, username, purchase_id):
        """Получает покупку по ID"""
        if username in self.users and "purchases" in self.users[username]:
            for purchase in self.users[username]["purchases"]:
                if purchase.get("id") == purchase_id:
                    return purchase.copy()
        return None
    
    def mark_purchase_as_purchased(self, username, purchase_id):
        """Помечает покупку как купленную (ручное действие)"""
        if username in self.users and "purchases" in self.users[username]:
            for purchase in self.users[username]["purchases"]:
                if purchase.get("id") == purchase_id:
                    purchase["status"] = "purchased"
                    purchase["purchased_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    self.save_users()
                    return True
        return False