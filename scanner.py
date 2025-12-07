import time
import pyautogui
import cv2
import numpy as np
import pygetwindow as gw
import re
from PIL import Image, ImageDraw

class VisualInterfaceScanner:
    def __init__(self):
        self.last_trigger_time = 0
        self.cooldown = 15  # 15 секунд между уведомлениями
        self.last_window_hash = None
        print("[INFO] Визуальный сканер интерфейса инициализирован")
        
        # Паттерны текста для покупок
        self.text_patterns = {
            # Основные действия
            "cart": ["корзина", "cart", "basket", "корзин", "cart items"],
            "checkout": ["оформление", "checkout", "оформить", "place order"],
            "payment": ["оплата", "payment", "оплатить", "pay", "payment method"],
            "buy": ["купить", "buy", "buy now", "purchase", "add to cart"],
            "order": ["заказ", "order", "my order", "order summary"],
            
            # Финансовые термины
            "price": ["цена", "price", "стоимость", "cost"],
            "total": ["итого", "total", "итог", "total amount"],
            "discount": ["скидка", "discount", "акция", "sale"],
            "delivery": ["доставка", "delivery", "shipping"],
            
            # Платежные методы
            "card": ["карта", "card", "банковская карта", "bank card"],
            "online": ["онлайн", "online", "интернет", "internet"],
            "transfer": ["перевод", "transfer", "перечислить"],
            "wallet": ["кошелек", "wallet", "электронный кошелек"],
            
            # Формы ввода
            "card_number": ["номер карты", "card number", "card no"],
            "expiry": ["срок действия", "expiry date", "valid thru"],
            "cvv": ["cvv", "cvc", "код безопасности", "security code"],
            "phone": ["телефон", "phone", "мобильный телефон"],
            "email": ["email", "почта", "электронная почта"],
            "address": ["адрес", "address", "адрес доставки"]
        }
        
        # Цвета элементов интерфейса (BGR)
        self.interface_colors = {
            # Кнопки покупки
            "buy_button": {
                "name": "Кнопка 'Купить'",
                "colors": [
                    {"lower": [0, 100, 200], "upper": [30, 200, 255]},    # Оранжевый
                    {"lower": [0, 150, 150], "upper": [10, 255, 255]},    # Красный
                ]
            },
            # Кнопки корзины
            "cart_button": {
                "name": "Кнопка корзины",
                "colors": [
                    {"lower": [150, 100, 50], "upper": [200, 200, 150]},  # Синий
                    {"lower": [100, 50, 100], "upper": [150, 150, 200]},  # Фиолетовый
                ]
            },
            # Кнопки оформления
            "checkout_button": {
                "name": "Кнопка 'Оформить'",
                "colors": [
                    {"lower": [0, 150, 0], "upper": [100, 255, 100]},     # Зеленый
                    {"lower": [0, 100, 100], "upper": [50, 200, 200]},    # Желто-зеленый
                ]
            },
            # Поля ввода
            "input_field": {
                "name": "Поле ввода",
                "colors": [
                    {"lower": [200, 200, 200], "upper": [255, 255, 255]}, # Белый
                    {"lower": [240, 240, 240], "upper": [255, 255, 255]}, # Светло-серый
                ]
            },
            # Иконки платежей
            "payment_icon": {
                "name": "Иконка оплаты",
                "colors": [
                    {"lower": [0, 0, 200], "upper": [100, 100, 255]},     # Синий (Visa/Mastercard)
                    {"lower": [0, 100, 200], "upper": [50, 200, 255]},    # Оранжевый (Мир)
                    {"lower": [0, 150, 150], "upper": [100, 255, 255]},   # Зеленый (Сбер)
                ]
            }
        }
        
        # Шаблоны визуальных элементов (простые паттерны)
        self.visual_patterns = {
            "card_icon": self.create_card_icon_pattern(),
            "cart_icon": self.create_cart_icon_pattern(),
            "lock_icon": self.create_lock_icon_pattern(),  # Иконка безопасности
            "user_icon": self.create_user_icon_pattern(),  # Иконка пользователя
        }
    
    def create_card_icon_pattern(self):
        """Создает шаблон иконки банковской карты"""
        size = 30
        img = Image.new('RGB', (size, size), color='white')
        draw = ImageDraw.Draw(img)
        
        # Простая иконка карты
        draw.rectangle([5, 10, 25, 20], outline='blue', fill='lightblue')
        draw.rectangle([10, 5, 20, 25], outline='blue', fill='white')
        
        return np.array(img)
    
    def create_cart_icon_pattern(self):
        """Создает шаблон иконки корзины"""
        size = 30
        img = Image.new('RGB', (size, size), color='white')
        draw = ImageDraw.Draw(img)
        
        # Простая иконка корзины
        draw.arc([5, 5, 25, 25], 0, 180, fill='black', width=2)
        draw.line([10, 10, 15, 5], fill='black', width=2)
        draw.line([20, 10, 15, 5], fill='black', width=2)
        
        return np.array(img)
    
    def create_lock_icon_pattern(self):
        """Создает шаблон иконки замка (безопасность)"""
        size = 30
        img = Image.new('RGB', (size, size), color='white')
        draw = ImageDraw.Draw(img)
        
        # Иконка замка
        draw.rectangle([10, 15, 20, 25], outline='green', fill='lightgreen')
        draw.arc([12, 10, 18, 16], 0, 180, fill='green', width=2)
        
        return np.array(img)
    
    def create_user_icon_pattern(self):
        """Создает шаблон иконки пользователя"""
        size = 30
        img = Image.new('RGB', (size, size), color='white')
        draw = ImageDraw.Draw(img)
        
        # Иконка пользователя
        draw.ellipse([10, 5, 20, 15], outline='black', fill='gray')
        draw.rectangle([8, 15, 22, 25], outline='black', fill='gray')
        
        return np.array(img)
    
    def get_browser_window(self):
        """Получает окно браузера"""
        try:
            windows = gw.getAllWindows()
            
            # Сначала ищем активное окно
            active_window = None
            for window in windows:
                if window.isActive and window.title:
                    active_window = window
                    break
            
            # Если нет активного, берем первое окно браузера
            if not active_window:
                browser_keywords = ["chrome", "firefox", "edge", "opera", "safari", "браузер", "browser"]
                for window in windows:
                    if window.title:
                        title_lower = window.title.lower()
                        if any(keyword in title_lower for keyword in browser_keywords):
                            active_window = window
                            break
            
            return active_window
            
        except Exception as e:
            print(f"[ERROR] Ошибка получения окна: {e}")
            return None
    
    def capture_screen_area(self, window):
        """Делает скриншот области окна"""
        try:
            if not window:
                return None
            
            left, top, width, height = window.left, window.top, window.width, window.height
            
            # Проверяем размеры
            if width <= 10 or height <= 10:
                return None
            
            # Ограничиваем размер для производительности
            max_width, max_height = 800, 600
            if width > max_width or height > max_height:
                scale = min(max_width / width, max_height / height)
                width = int(width * scale)
                height = int(height * scale)
                left = left + (window.width - width) // 2
                top = top + (window.height - height) // 2
            
            # Делаем скриншот
            screenshot = pyautogui.screenshot(region=(left, top, width, height))
            return np.array(screenshot)
            
        except Exception as e:
            print(f"[ERROR] Ошибка скриншота: {e}")
            return None
    
    def detect_text_elements(self, image):
        """Обнаружение текстовых элементов на изображении"""
        try:
            # Конвертируем в оттенки серого
            gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            # Применяем различные методы для выделения текста
            # 1. Адаптивная бинаризация
            binary = cv2.adaptiveThreshold(gray, 255, 
                                          cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                          cv2.THRESH_BINARY, 11, 2)
            
            # 2. Находим контуры
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_regions = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                # Фильтруем по размеру (текст обычно имеет определенные пропорции)
                if 20 < w < 500 and 10 < h < 100:
                    # Проверяем соотношение сторон
                    aspect_ratio = w / h
                    if 1.5 < aspect_ratio < 10:  # Текст обычно вытянут по горизонтали
                        text_regions.append((x, y, w, h))
            
            return text_regions
            
        except Exception as e:
            print(f"[ERROR] Ошибка детектирования текста: {e}")
            return []
    
    def detect_interface_elements(self, image):
        """Обнаружение элементов интерфейса по цвету"""
        try:
            # Конвертируем в BGR для OpenCV
            img_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            
            detected_elements = {}
            
            for element_type, element_info in self.interface_colors.items():
                element_mask = None
                
                for color_range in element_info["colors"]:
                    lower = np.array(color_range["lower"])
                    upper = np.array(color_range["upper"])
                    
                    mask = cv2.inRange(img_bgr, lower, upper)
                    
                    if element_mask is None:
                        element_mask = mask
                    else:
                        element_mask = cv2.bitwise_or(element_mask, mask)
                
                if element_mask is not None:
                    # Находим контуры
                    contours, _ = cv2.findContours(element_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    elements = []
                    for contour in contours:
                        area = cv2.contourArea(contour)
                        
                        # Фильтруем по размеру
                        if 100 < area < 10000:  # Размеры кнопок/полей
                            x, y, w, h = cv2.boundingRect(contour)
                            
                            # Проверяем форму (кнопки обычно прямоугольные)
                            aspect_ratio = w / h
                            if 0.3 < aspect_ratio < 3:  # Пропорции кнопок
                                elements.append({
                                    "type": element_type,
                                    "name": element_info["name"],
                                    "x": x, "y": y, "w": w, "h": h,
                                    "area": area
                                })
                    
                    if elements:
                        detected_elements[element_type] = elements
            
            return detected_elements
            
        except Exception as e:
            print(f"[ERROR] Ошибка детектирования интерфейса: {e}")
            return {}
    
    def detect_visual_patterns(self, image):
        """Обнаружение визуальных паттернов (иконок)"""
        try:
            img_gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            
            detected_patterns = []
            
            for pattern_name, pattern_img in self.visual_patterns.items():
                pattern_gray = cv2.cvtColor(pattern_img, cv2.COLOR_RGB2GRAY)
                
                # Используем template matching
                result = cv2.matchTemplate(img_gray, pattern_gray, cv2.TM_CCOEFF_NORMED)
                threshold = 0.7
                locations = np.where(result >= threshold)
                
                for pt in zip(*locations[::-1]):
                    detected_patterns.append({
                        "name": pattern_name,
                        "x": pt[0], "y": pt[1]
                    })
            
            return detected_patterns
            
        except Exception as e:
            print(f"[ERROR] Ошибка детектирования паттернов: {e}")
            return []
    
    def analyze_purchase_interface(self, window):
        """Анализирует интерфейс на признаки покупки"""
        try:
            if not window:
                return False, {}, [], []
            
            # Делаем скриншот
            screenshot = self.capture_screen_area(window)
            if screenshot is None:
                return False, {}, [], []
            
            # 1. Детектируем элементы интерфейса
            interface_elements = self.detect_interface_elements(screenshot)
            
            # 2. Детектируем визуальные паттерны
            visual_patterns = self.detect_visual_patterns(screenshot)
            
            # 3. Детектируем текстовые области
            text_regions = self.detect_text_elements(screenshot)
            
            # 4. Анализируем комбинации элементов
            purchase_score = 0
            found_elements = []
            
            # Проверяем наличие кнопок покупки
            if "buy_button" in interface_elements:
                purchase_score += 3
                found_elements.append("buy_button")
                print(f"[VISUAL] Найдены кнопки покупки: {len(interface_elements['buy_button'])}")
            
            # Проверяем наличие кнопок корзины
            if "cart_button" in interface_elements:
                purchase_score += 2
                found_elements.append("cart_button")
                print(f"[VISUAL] Найдены кнопки корзины: {len(interface_elements['cart_button'])}")
            
            # Проверяем наличие кнопок оформления
            if "checkout_button" in interface_elements:
                purchase_score += 3
                found_elements.append("checkout_button")
                print(f"[VISUAL] Найдены кнопки оформления: {len(interface_elements['checkout_button'])}")
            
            # Проверяем наличие полей ввода (форма оплаты)
            if "input_field" in interface_elements:
                purchase_score += 2
                found_elements.append("input_field")
                print(f"[VISUAL] Найдены поля ввода: {len(interface_elements['input_field'])}")
            
            # Проверяем наличие иконок оплаты
            if "payment_icon" in interface_elements:
                purchase_score += 2
                found_elements.append("payment_icon")
                print(f"[VISUAL] Найдены иконки оплаты: {len(interface_elements['payment_icon'])}")
            
            # Проверяем визуальные паттерны
            for pattern in visual_patterns:
                if pattern["name"] in ["card_icon", "lock_icon"]:
                    purchase_score += 1
                    found_elements.append(pattern["name"])
                    print(f"[VISUAL] Найдена иконка: {pattern['name']}")
            
            # Учитываем количество текстовых областей (формы обычно содержат много текста)
            if len(text_regions) > 5:
                purchase_score += 1
                found_elements.append("text_fields")
                print(f"[VISUAL] Много текстовых областей: {len(text_regions)}")
            
            # Определяем тип страницы
            page_type = "unknown"
            if purchase_score >= 5:
                page_type = "checkout_page"
            elif purchase_score >= 3:
                page_type = "cart_page"
            
            # Формируем контекст
            context_info = {
                "page_type": page_type,
                "score": purchase_score,
                "elements": found_elements,
                "element_count": len(interface_elements),
                "pattern_count": len(visual_patterns),
                "text_region_count": len(text_regions)
            }
            
            return purchase_score >= 3, context_info, interface_elements, visual_patterns
            
        except Exception as e:
            print(f"[ERROR] Ошибка анализа интерфейса: {e}")
            return False, {}, [], []
    
    def analyze_window_title(self, title):
        """Анализ заголовка окна"""
        if not title:
            return 0, []
        
        title_lower = title.lower()
        text_score = 0
        found_keywords = []
        
        for category, keywords in self.text_patterns.items():
            for keyword in keywords:
                if keyword in title_lower:
                    text_score += 1
                    found_keywords.append(keyword)
                    break  # Чтобы не считать несколько ключевых слов из одной категории
        
        return text_score, found_keywords
    
    def start(self, trigger_queue, running_flag):
        """Основной цикл сканирования"""
        print("[INFO] Визуальный сканер запущен")
        print("[INFO] Анализ интерфейса: кнопки, формы, иконки")
        
        while True:
            if not running_flag():
                time.sleep(1)
                continue
            
            try:
                current_time = time.time()
                
                # Получаем окно браузера
                window = self.get_browser_window()
                
                if window and window.title:
                    window_hash = hash(window.title) % 1000000
                    
                    # 1. Анализ заголовка
                    text_score, text_keywords = self.analyze_window_title(window.title)
                    
                    # 2. Визуальный анализ интерфейса
                    is_purchase, context_info, interface_elements, visual_patterns = \
                        self.analyze_purchase_interface(window)
                    
                    # Комбинированная оценка
                    total_score = text_score + context_info.get("score", 0)
                    
                    # Если общий счет достаточно высок
                    if (is_purchase or total_score >= 4) and window_hash != self.last_window_hash:
                        
                        # Проверяем кулдаун
                        if (current_time - self.last_trigger_time) > self.cooldown:
                            
                            print(f"\n[!] ВИЗУАЛЬНОЕ ОБНАРУЖЕНИЕ!")
                            print(f"[!] Заголовок: {window.title[:80]}...")
                            print(f"[!] Текстовые ключевые слова: {text_keywords}")
                            print(f"[!] Визуальный счет: {context_info.get('score', 0)}")
                            print(f"[!] Тип страницы: {context_info.get('page_type', 'unknown')}")
                            
                            # Формируем детальное описание
                            host = "Обнаружена страница покупки"
                            if text_keywords:
                                host += f" - {text_keywords[0]}"
                            
                            context = "🔍 **Визуальный анализ обнаружены:**\n\n"
                            
                            # Добавляем информацию о тексте
                            if text_keywords:
                                context += f"📝 Текстовые признаки:\n"
                                context += f"   • Ключевые слова: {', '.join(text_keywords[:5])}\n\n"
                            
                            # Добавляем информацию о визуальных элементах
                            context += f"🎨 Визуальные элементы:\n"
                            context += f"   • Тип страницы: {context_info.get('page_type', 'unknown')}\n"
                            context += f"   • Общий счет: {total_score}/10\n"
                            
                            if context_info.get("elements"):
                                context += f"   • Найдены элементы: {', '.join(context_info['elements'][:5])}\n"
                            
                            # Добавляем информацию о форме
                            if "input_field" in context_info.get("elements", []):
                                context += f"\n💳 **Обнаружена форма оплаты!**\n"
                                context += f"   • Поля для ввода данных\n"
                                context += f"   • Возможно требуется ввод карты\n"
                            
                            if "payment_icon" in context_info.get("elements", []):
                                context += f"\n💰 **Обнаружены платежные элементы**\n"
                                context += f"   • Иконки платежных систем\n"
                                context += f"   • Выбор способа оплаты\n"
                            
                            # Добавляем заголовок окна
                            context += f"\n📄 Заголовок окна:\n{window.title[:150]}..."
                            
                            # Отправляем уведомление
                            trigger_queue.put((host, context))
                            
                            self.last_trigger_time = current_time
                            self.last_window_hash = window_hash
                
                # Интервал сканирования
                time.sleep(2.5)
                
            except Exception as e:
                print(f"[ERROR] Ошибка в основном цикле: {e}")
                time.sleep(5)

# Функция для совместимости
def start_scanner(trigger_queue, running_flag):
    scanner = VisualInterfaceScanner()
    scanner.start(trigger_queue, running_flag)