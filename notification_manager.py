import json
from datetime import datetime, timedelta

class NotificationManager:
    def __init__(self, auth_system):
        self.auth = auth_system
    
    def check_pending_notifications(self, username):
        """Проверяет, нужно ли отправлять уведомления"""
        user_data = self.auth.get_user_data(username)
        purchases = user_data.get("purchases", [])
        notification_settings = user_data.get("notification_settings", {})
        
        if not notification_settings.get("enabled", True):
            return []
        
        frequency_days = notification_settings.get("frequency_days", 7)
        excluded_items = notification_settings.get("excluded_items", [])
        
        pending_notifications = []
        
        for purchase in purchases:
            if purchase.get("status") != "cooling" or purchase.get("purchased", False):
                continue
            
            if purchase["id"] in excluded_items:
                continue
            
            # Проверяем, было ли уже уведомление
            last_notification = purchase.get("last_notification")
            if last_notification:
                last_date = datetime.strptime(last_notification, "%Y-%m-%d %H:%M:%S")
                days_since_last = (datetime.now() - last_date).days
                if days_since_last < frequency_days:
                    continue
            
            # Проверяем, истек ли период охлаждения
            cooling_until = purchase.get("cooling_until")
            if cooling_until:
                until_date = datetime.strptime(cooling_until, "%Y-%m-%d %H:%M:%S")
                if until_date <= datetime.now():
                    pending_notifications.append({
                        "purchase": purchase,
                        "type": "cooling_ended",
                        "message": f"✅ Период охлаждения для '{purchase['name']}' завершен!\nВы можете совершить покупку."
                    })
                else:
                    # Регулярное напоминание
                    days_left = (until_date - datetime.now()).days
                    pending_notifications.append({
                        "purchase": purchase,
                        "type": "reminder",
                        "message": f"⏳ Напоминание о покупке: '{purchase['name']}'\nОхлаждение до: {until_date.strftime('%d.%m.%Y')}\nОсталось дней: {days_left}"
                    })
        
        return pending_notifications
    
    def mark_as_notified(self, username, purchase_id):
        """Отмечает покупку как уведомленную"""
        users = self.auth.load_users()
        if username in users and "purchases" in users[username]:
            for purchase in users[username]["purchases"]:
                if purchase.get("id") == purchase_id:
                    purchase["last_notification"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    purchase["notified"] = True
                    self.auth.save_users()
                    return True
        return False
    
    def mark_as_purchased(self, username, purchase_id):
        """Отмечает покупку как совершенную"""
        users = self.auth.load_users()
        if username in users and "purchases" in users[username]:
            for purchase in users[username]["purchases"]:
                if purchase.get("id") == purchase_id:
                    purchase["purchased"] = True
                    purchase["purchased_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    purchase["status"] = "purchased"
                    self.auth.save_users()
                    return True
        return False