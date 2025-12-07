import tkinter as tk
from tkinter import ttk, messagebox
import queue
import threading
from datetime import datetime
from auth import AuthSystem
from cooling_manager import CoolingManager
from notification_manager import NotificationManager
from scanner import start_scanner

try:
    from openai_config import OPENAI_API_KEY
except ImportError:
    OPENAI_API_KEY = None
import sys
import os
import traceback
from pathlib import Path

# ==================== СИСТЕМА ПУТЕЙ ====================
def is_exe_mode():
    """Проверяем, запущены ли мы в EXE"""
    return getattr(sys, 'frozen', False)

def get_base_path():
    """Получаем базовый путь (для EXE или разработки)"""
    if is_exe_mode():
        # В EXE файле
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
    # При разработке
    return os.getcwd()

def resource_path(filename):
    """
    Умный поиск файлов. Работает и в EXE, и при разработке.
    
    Использование:
    - Было: open("products.json")
    - Стало: open(resource_path("products.json"))
    """
    # 1. Если файл в текущей папке (для пользовательских файлов)
    current_path = Path(filename)
    if current_path.exists():
        return str(current_path)
    
    # 2. Если файл в src/ (для статических ресурсов)
    src_path = Path("src") / filename
    if src_path.exists():
        return str(src_path)
    
    # 3. В режиме EXE ищем во временной папке
    if is_exe_mode() and hasattr(sys, '_MEIPASS'):
        exe_path = Path(sys._MEIPASS) / filename
        if exe_path.exists():
            return str(exe_path)
    
    # 4. Файл не найден
    print(f"⚠️ Файл не найден: {filename}")
    return filename

def init_application():
    """Инициализация приложения - создание нужных файлов и папок"""
    print("=" * 60)
    print("🚀 ИНИЦИАЛИЗАЦИЯ T-ASSISTANT")
    print("=" * 60)
    
    # Информация о режиме
    if is_exe_mode():
        print("✅ Режим: Собранный EXE файл")
        if hasattr(sys, '_MEIPASS'):
            print(f"📁 Временная папка: {sys._MEIPASS}")
    else:
        print("✅ Режим: Разработка (Python)")
    
    print(f"📂 Рабочая папка: {os.getcwd()}")
    print(f"🐍 Python: {sys.version.split()[0]}")
    
    # Создаем необходимые папки
    folders = ['logs', 'data', 'cache']
    for folder in folders:
        Path(folder).mkdir(exist_ok=True)
        print(f"📁 Папка '{folder}': создана/существует")
    
    # Проверяем критические файлы
    print("\n🔍 Проверка ресурсов:")
    
    # Статические файлы (должны быть)
    static_files = ['aboba.png', 'tassistant.png']
    for file in static_files:
        path = resource_path(file)
        if Path(path).exists():
            print(f"  ✅ {file}: найден")
        else:
            print(f"  ❌ {file}: НЕ НАЙДЕН! Приложение может работать некорректно")
    
    # Динамические файлы (создаем при необходимости)
    dynamic_files = {
        'products.json': {"products": [], "version": "1.0", "created": True},
        'config.json': {"settings": {}, "user": {}, "version": "1.0"},
    }
    
    print("\n📝 Динамические файлы:")
    for filename, default_content in dynamic_files.items():
        if not Path(filename).exists():
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(default_content, f, indent=2, ensure_ascii=False)
            print(f"  📄 {filename}: создан (шаблон)")
        else:
            print(f"  📄 {filename}: уже существует")
    
    print("=" * 60)
    print("✅ Инициализация завершена успешно!")
    print("=" * 60 + "\n")
    
    return True

class RoundedButton(tk.Canvas):
    def __init__(self, master=None, text="", radius=20, bg="#FFCC00",  # Хардкод цветов
                 fg="#000000", font=("Arial", 14, "bold"), 
                 command=None, **kwargs):
        # Используем темный фон по умолчанию
        master_bg = "#1E1E1E"  # Темный фон
        if master:
            try:
                master_bg = master.cget("bg")
            except:
                pass
        
        super().__init__(master, highlightthickness=0, bg=master_bg)
        self.radius = radius
        self.bg = bg
        self.fg = fg
        self.font = font
        self.command = command
        self.is_pressed = False
        self.bind("<Button-1>", self.on_press)
        self.bind("<ButtonRelease-1>", self.on_release)
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.text_id = None
        self.draw()
    
    def draw(self):
        self.delete("all")
        width = self.winfo_reqwidth() if self.winfo_reqwidth() > 1 else 200
        height = self.winfo_reqheight() if self.winfo_reqheight() > 1 else 50
        self.create_rounded_rect(0, 0, width, height, self.radius, fill=self.bg, outline="")
        if self.text_id:
            self.delete(self.text_id)
        self.text_id = self.create_text(width/2, height/2, text=self.text, 
                                       fill=self.fg, font=self.font)
    
    def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
        points = [
            x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r, x2, y2,
            x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1, x1+r, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def on_press(self, event):
        self.is_pressed = True
        self.bg = "#E6B800"  # Темнее желтый
        self.draw()
    
    def on_release(self, event):
        self.is_pressed = False
        self.bg = "#FFCC00"  # Основной желтый
        self.draw()
        if self.command:
            self.command()
    
    def on_enter(self, event):
        if not self.is_pressed:
            self.bg = "#FFD633"  # Светлее желтый
            self.draw()
    
    def on_leave(self, event):
        if not self.is_pressed:
            self.bg = "#FFCC00"  # Основной желтый
        self.draw()
    
    @property
    def text(self):
        return self._text if hasattr(self, '_text') else ""
    
    @text.setter
    def text(self, value):
        self._text = value
        if self.text_id:
            self.itemconfig(self.text_id, text=value)
        else:
            self.draw()
    
    def config(self, **kwargs):
        if 'text' in kwargs:
            self.text = kwargs['text']
        if 'command' in kwargs:
            self.command = kwargs['command']
        if 'bg' in kwargs:
            self.bg = kwargs['bg']
        self.draw()

class MainApplication:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("T-Assistant")
        self.root.geometry("560x900")
        
        # СНАЧАЛА определяем DARK_THEME
        self.DARK_THEME = {
            "bg": "#1E1E1E",           # Основной фон
            "surface": "#2C2C2C",      # Поверхности (карточки, формы)
            "text": "#FFFFFF",         # Основной текст
            "secondary": "#888888",    # Вторичный текст
            "text_disabled": "#666666",  # Текст для неактивных элементов
            "accent": "#FFCC00",       # Акцентный цвет (T-Bank желтый)
            "primary_light": "#FFD633",  # Светло-желтый для сообщений пользователя
            "primary_dark": "#E6B800",   # Темно-желтый
            "success": "#28A745",      # Успех
            "warning": "#FFC107",      # Предупреждение
            "error": "#DC3545",        # Ошибка
            "info": "#17A2B8",         # Информация
            "divider": "#444444",      # Разделители
            "input_bg": "#3A3A3A",     # Фон полей ввода
            "card_bg": "#2C2C2C",      # Фон карточек
        }
        
        # ТЕПЕРЬ настраиваем фон
        self.root.configure(bg=self.DARK_THEME["bg"])
        self.root.resizable(False, True)
        
        self.auth_system = AuthSystem()
        self.cooling_manager = CoolingManager(self.auth_system)
        self.notification_manager = NotificationManager(self.auth_system)
        self.trigger_queue = queue.Queue()
        self.scanner_running = False
        self.scanner_thread = None
        self.current_user = None
        self.content_container = None
        self.current_screen = None
        self.chat_history = []
        # Монки-патчим Canvas для поддержки закругленных прямоугольников
        def create_rounded_rect(self, x1, y1, x2, y2, r, **kwargs):
            points = [
                x1+r, y1, x2-r, y1, 
                x2, y1, x2, y1+r, 
                x2, y2-r, x2, y2,
                x2-r, y2, x1+r, y2, 
                x1, y2, x1, y2-r, 
                x1, y1+r, x1, y1, 
                x1+r, y1
            ]
            return self.create_polygon(points, smooth=True, **kwargs)
        
        tk.Canvas.create_rounded_rect = create_rounded_rect
        
        self.init_navigation()
        self.show_login_screen()
        self.ai_assistant = None
        self.init_openai_assistant()
        self.root.after(1000, self.check_scanner_queue)
   

    def show_navigation(self, show=True):
        """Показывает или скрывает нижнюю навигацию"""
        theme = self.DARK_THEME
        
        if show:
            # Убедимся, что меню еще не отображается
            try:
                if self.nav_frame.winfo_ismapped():
                    return  # Уже отображено, ничего не делаем
            except:
                pass
            
            # Упаковываем меню ВНИЗУ окна
            self.nav_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=0)
            self.nav_frame.lift()  # Поднимаем поверх других элементов
        else:
            # Скрываем меню
            try:
                if self.nav_frame.winfo_exists():
                    self.nav_frame.pack_forget()
            except:
                pass

    def create_rounded_button(self, parent, text, command, **kwargs):
        """Создает простую закругленную кнопку"""
        bg = kwargs.get('bg', self.DARK_THEME["accent"])
        fg = kwargs.get('fg', "#000000")
        font = kwargs.get('font', ("Arial", 14, "bold"))
        width = kwargs.get('width', 200)
        height = kwargs.get('height', 50)
        radius = kwargs.get('radius', 20)
        
        # Создаем Canvas для кнопки
        canvas = tk.Canvas(parent, highlightthickness=0, 
                          bg=parent.cget("bg") if parent else self.DARK_THEME["bg"],
                          width=width, height=height)
        
        # Рисуем закругленный прямоугольник
        canvas.create_rounded_rect(2, 2, width-2, height-2, radius, 
                                   fill=bg, outline="")
        
        # Добавляем текст
        canvas.create_text(width/2, height/2, text=text, fill=fg, font=font)
        
        # Делаем кликабельным
        def on_click(event):
            if command:
                command()
        
        def on_enter(event):
            canvas.config(cursor="hand2")
            # Можно добавить изменение цвета при наведении
        
        def on_leave(event):
            canvas.config(cursor="")
        
        canvas.bind("<Button-1>", on_click)
        canvas.bind("<Enter>", on_enter)
        canvas.bind("<Leave>", on_leave)
        
        return canvas
    
    def check_scanner_queue(self):
        try:
            while not self.trigger_queue.empty():
                host, context = self.trigger_queue.get_nowait()
                self.show_scanner_notification(host, context)
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Ошибка обработки очереди сканера: {e}")
        
        if hasattr(self, 'root') and self.root:
            self.root.after(1000, self.check_scanner_queue)
    
    def show_scanner_notification(self, host, context):
        """Показывает уведомление о новой покупке (облегчённая версия без контекста)."""
        notification_window = tk.Toplevel(self.root)
        notification_window.title("🛒 ОБНАРУЖЕНА ПОКУПКА")
        
        # Делаем окно такого же размера как основное приложение
        main_width = 700
        main_height = 900
        notification_window.geometry(f"{main_width}x{main_height}")
        notification_window.configure(bg=self.DARK_THEME["bg"])
        notification_window.resizable(True, True)  # Разрешаем изменение размера

        # Модальное окно поверх всех окон
        notification_window.attributes("-topmost", True)
        notification_window.transient(self.root)
        notification_window.grab_set()
        notification_window.focus_force()

        # Центрирование
        try:
            root_x = self.root.winfo_x()
            root_y = self.root.winfo_y()
            root_width = self.root.winfo_width()
            root_height = self.root.winfo_height()
            x = root_x + (root_width - main_width) // 2
            y = root_y + (root_height - main_height) // 2
            notification_window.geometry(f"{main_width}x{main_height}+{x}+{y}")
        except:
            pass

        # Основной контейнер с прокруткой
        main_canvas = tk.Canvas(notification_window, bg=self.DARK_THEME["bg"], 
                            highlightthickness=0)
        scrollbar = ttk.Scrollbar(notification_window, orient="vertical", 
                                command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=self.DARK_THEME["bg"])
        
        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Заголовок
        header = tk.Frame(scrollable_frame, bg=self.DARK_THEME["accent"], height=100)
        header.pack(fill=tk.X, pady=(0, 20))
        header.pack_propagate(False)

        tk.Label(
            header,
            text="🛒 ОБНАРУЖЕНА ПОКУПКА",
            font=("Arial", 20, "bold"),
            fg="#000000",
            bg=self.DARK_THEME["accent"]
        ).pack(expand=True, pady=20)

        # Тело
        body = tk.Frame(scrollable_frame, bg=self.DARK_THEME["surface"])
        body.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Сайт
        tk.Label(
            body,
            text="🌐 Сайт:",
            font=("Arial", 14, "bold"),
            fg=self.DARK_THEME["text"],
            bg=self.DARK_THEME["surface"]
        ).pack(anchor=tk.W, pady=(10, 5))

        site_text = host or "Неизвестно"
        site_label = tk.Label(
            body,
            text=site_text,
            font=("Arial", 13),
            fg=self.DARK_THEME["secondary"],
            bg=self.DARK_THEME["surface"],
            wraplength=main_width-60,
            justify=tk.LEFT
        )
        site_label.pack(anchor=tk.W, pady=(0, 20))

        # Вопрос
        tk.Label(
            body,
            text="Хотите добавить покупку в охлаждение или пройти опрос сейчас?",
            font=("Arial", 14),
            fg=self.DARK_THEME["text"],
            bg=self.DARK_THEME["surface"],
            wraplength=main_width-60,
            justify=tk.LEFT
        ).pack(anchor=tk.W, pady=(0, 30))

        # --- Опрос (скрытый до нажатия кнопки)
        survey_frame = tk.Frame(scrollable_frame, bg=self.DARK_THEME["surface"])
        result_frame = tk.Frame(scrollable_frame, bg=self.DARK_THEME["surface"])

        # Вопросы
        survey_questions = [
            {
                "text": "1. Эта покупка решает конкретную проблему или удовлетворяет реальную потребность?",
                "options": ["✅ Да, это необходимость", "🤔 Скорее да", "🚫 Нет, это просто хочу"]
            },
            {
                "text": "2. У вас уже есть что-то похожее или выполняющее ту же функцию?",
                "options": ["🚫 Нет, это первая такая вещь", "🤔 Есть, но устарело/не работает", "✅ Да, есть аналогичная"]
            },
            {
                "text": "3. Вы можете позволить себе эту покупку без ущерба для основных расходов?",
                "options": ["✅ Да, легко", "🤔 Придется немного ужать бюджет", "🚫 Нет, это будет в ущерб"]
            },
            {
                "text": "4. Подумали ли вы об этой покупке дольше 24 часов?",
                "options": ["✅ Да, думаю уже несколько дней", "🤔 Несколько часов", "🚫 Только что увидел(а)"]
            },
            {
                "text": "5. Что случится, если вы откажетесь от этой покупки?",
                "options": ["🚫 Будет серьезная проблема", "🤔 Будет неудобно, но жить можно", "✅ Ничего особенного"]
            }
        ]

        survey_vars = [tk.StringVar(value="") for _ in survey_questions]
        
        # Создаём опрос в скрытом блоке
        s_canvas = tk.Canvas(survey_frame, bg=self.DARK_THEME["surface"], highlightthickness=0)
        s_scroll = ttk.Scrollbar(survey_frame, orient="vertical", command=s_canvas.yview)
        s_inner = tk.Frame(s_canvas, bg=self.DARK_THEME["surface"])

        s_inner.bind("<Configure>", lambda e: s_canvas.configure(scrollregion=s_canvas.bbox("all")))
        s_canvas.create_window((0, 0), window=s_inner, anchor="nw", width=main_width-60)
        s_canvas.configure(yscrollcommand=s_scroll.set)
        
        s_canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        s_scroll.pack(side="right", fill="y")

        for i, q in enumerate(survey_questions):
            q_frame = tk.Frame(s_inner, bg=self.DARK_THEME["surface"], pady=10)
            q_frame.pack(fill=tk.X, pady=(0, 15))
            
            tk.Label(q_frame, text=q["text"], font=("Arial", 13, "bold"),
                    fg=self.DARK_THEME["text"], bg=self.DARK_THEME["surface"],
                    wraplength=main_width-100, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 10))
        
            for opt in q["options"]:
                tk.Radiobutton(
                    q_frame, text=opt, variable=survey_vars[i], value=opt,
                    font=("Arial", 12),
                    bg=self.DARK_THEME["surface"], anchor="w", justify=tk.LEFT,
                    wraplength=main_width-120
                ).pack(fill=tk.X, padx=20, pady=5)

        # Состояние
        notification_window.survey_completed = False
        notification_window.survey_answers = []

        def show_survey():
            body.pack_forget()
            result_frame.pack_forget()
            survey_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        def finish_survey():
            answers = [v.get() for v in survey_vars]
            if any(not a for a in answers):
                messagebox.showwarning("Не всё заполнено", "Ответьте на все вопросы.")
                return

            notification_window.survey_completed = True
            notification_window.survey_answers = answers
            
            # Показываем результат сразу после завершения опроса
            show_result()

        def show_result():
            if not notification_window.survey_completed:
                messagebox.showwarning("Нет результата", "Сначала завершите опрос.")
                return

            # Простая логика оценки
            answers = notification_window.survey_answers
            score = 0
            for a in answers:
                if a.startswith("✅"):
                    score += 2
                elif a.startswith("🤔"):
                    score += 1

            percentage = (score / (len(answers) * 2)) * 100

            survey_frame.pack_forget()
            result_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            for w in result_frame.winfo_children():
                w.destroy()

            # Заголовок результата
            result_header = tk.Frame(result_frame, bg=self.DARK_THEME["accent"], height=80)
            result_header.pack(fill=tk.X, pady=(0, 20))
            result_header.pack_propagate(False)
            
            tk.Label(result_header, text="📊 РЕЗУЛЬТАТ ОПРОСА",
                     font=("Arial", 18, "bold"),
                     fg="#000000", bg=self.DARK_THEME["accent"]).pack(expand=True, pady=20)

            # Оценка
            tk.Label(result_frame, text=f"🎯 Оценка необходимости: {percentage:.0f}%",
                     font=("Arial", 16, "bold"),
                     fg=self.DARK_THEME["text"], bg=self.DARK_THEME["surface"]).pack(pady=(0, 20))

            if percentage >= 70:
                text = "✅ МОЖНО ПОКУПАТЬ\n\nЭта покупка выглядит обоснованной и необходимой."
                color = self.DARK_THEME["success"]
            elif percentage >= 40:
                text = "🤔 ПОДУМАТЬ ЕЩЁ\n\nЕсть как доводы за, так и против покупки.\nРекомендуется подождать еще несколько дней."
                color = self.DARK_THEME["warning"]
            else:
                text = "🚫 ЛУЧШЕ ОТКАЗАТЬСЯ\n\nПокупка выглядит импульсивной и необязательной.\nРекомендуется отказаться или отложить на 30 дней."
                color = self.DARK_THEME["error"]

            tk.Label(result_frame, text=text,
                     font=("Arial", 14),
                     fg=color, bg=self.DARK_THEME["surface"],
                     wraplength=main_width-100, justify=tk.LEFT).pack(pady=(0, 30))

            # Кнопки действий в результате
            action_frame = tk.Frame(result_frame, bg=self.DARK_THEME["surface"])
            action_frame.pack(fill=tk.X, pady=20)

            def apply_action():
                notification_window.destroy()
                self.show_add_purchase()

            def ignore_and_close():
                notification_window.destroy()

            if percentage >= 40:  # Если можно покупать или подумать
                tk.Button(action_frame, text="➕ ДОБАВИТЬ В ОХЛАЖДЕНИЕ",
                        font=("Arial", 14, "bold"),
                        bg=self.DARK_THEME["accent"], fg="#000000",
                        command=apply_action,
                        padx=20, pady=15).pack(fill=tk.X, pady=(0, 10))
            else:
                tk.Button(action_frame, text="❌ ОТКАЗАТЬСЯ ОТ ПОКУПКИ",
                        font=("Arial", 14, "bold"),
                        bg=self.DARK_THEME["error"], fg="#000000",
                        command=ignore_and_close,
                        padx=20, pady=15).pack(fill=tk.X, pady=(0, 10))

            tk.Button(action_frame, text="← НАЗАД К ГЛАВНОМУ МЕНЮ",
                    font=("Arial", 12),
                    bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"],
                    command=ignore_and_close,
                    padx=20, pady=10).pack(fill=tk.X)

        def add_directly():
            notification_window.destroy()
            self.show_add_purchase()

        def ignore():
            notification_window.destroy()

        # Footer с кнопками (изначально видимый)
        footer = tk.Frame(scrollable_frame, bg=self.DARK_THEME["bg"])
        footer.pack(fill=tk.X, pady=(20, 40))

        tk.Button(
            footer, text="➕ ДОБАВИТЬ ПОКУПКУ В ОХЛАЖДЕНИЕ", font=("Arial", 14, "bold"),
            bg=self.DARK_THEME["success"], fg="#000000",
            command=add_directly,
            padx=20, pady=15
        ).pack(fill=tk.X, pady=(0, 10))

        tk.Button(
            footer, text="🧠 НАЧАТЬ ОПРОС (5 вопросов)", font=("Arial", 14, "bold"),
            bg=self.DARK_THEME["accent"], fg="#000000",
            command=show_survey,
            padx=20, pady=15
        ).pack(fill=tk.X, pady=(0, 10))

        # Кнопка завершения опроса будет показываться только когда опрос активен
        def update_finish_button():
            if survey_frame.winfo_ismapped():  # Если опрос виден
                if not hasattr(notification_window, 'finish_btn'):
                    notification_window.finish_btn = tk.Button(
                        footer, text="✅ ЗАВЕРШИТЬ ОПРОС И ПОЛУЧИТЬ РЕЗУЛЬТАТ", 
                        font=("Arial", 14, "bold"),
                        bg=self.DARK_THEME["info"], fg="#000000",
                        command=finish_survey,
                        padx=20, pady=15
                    )
                    notification_window.finish_btn.pack(fill=tk.X, pady=(0, 10))
            elif hasattr(notification_window, 'finish_btn'):
                notification_window.finish_btn.pack_forget()
            
            # Обновляем каждые 100 мс
            if notification_window.winfo_exists():
                notification_window.after(1000, update_finish_button)

        tk.Button(
            footer, text="✕ ИГНОРИРОВАТЬ", font=("Arial", 13),
            bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"],
            command=ignore,
            padx=20, pady=12
        ).pack(fill=tk.X, pady=(10, 0))

        # Запускаем обновление кнопки завершения
        notification_window.after(100, update_finish_button)

        # Поддерживаем окно всегда сверху (не агрессивно)
        def keep_on_top():
            try:
                if notification_window.winfo_exists():
                    notification_window.attributes("-topmost", True)
                    notification_window.after(200, keep_on_top)
            except:
                pass

        notification_window.after(200, keep_on_top)

        # Обработка закрытия
        notification_window.protocol("WM_DELETE_WINDOW", ignore)
    
    def show_scanner_dialog(self):
        """Показывает диалог с вопросами о покупке"""
        dialog_window = tk.Toplevel(self.root)
        dialog_window.title("Проверка необходимости покупки")
        
        # Делаем окно такого же размера как основное приложение
        main_width = 600
        main_height = 900
        dialog_window.geometry(f"{main_width}x{main_height}")
        dialog_window.configure(bg=self.DARK_THEME["bg"])
        dialog_window.resizable(True, True)
        
        # Позиционирование по центру
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        x = root_x + (root_width - main_width) // 2
        y = root_y + (root_height - main_height) // 2
        
        dialog_window.geometry(f"{main_width}x{main_height}+{max(0, x)}+{max(0, y)}")
        
        # Делаем окно модальным и поверх всех
        dialog_window.transient(self.root)
        dialog_window.grab_set()
        dialog_window.attributes('-topmost', True)
        dialog_window.focus_force()
        
        self.root.lift()
        dialog_window.lift()
        
        # Основной контейнер с прокруткой
        main_canvas = tk.Canvas(dialog_window, bg=self.DARK_THEME["bg"], 
                            highlightthickness=0)
        scrollbar = ttk.Scrollbar(dialog_window, orient="vertical", 
                                command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas, bg=self.DARK_THEME["bg"])
        
        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True, padx=(10, 0), pady=10)
        scrollbar.pack(side="right", fill="y")
        
        # Заголовок
        header_frame = tk.Frame(scrollable_frame, bg=self.DARK_THEME["accent"], height=120)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🧠 Проверка необходимости покупки", 
                font=("Arial", 22, "bold"), fg="#000000", 
                bg=self.DARK_THEME["accent"]).pack(expand=True, pady=30)
        
        # Контейнер для вопросов
        questions_container = tk.Frame(scrollable_frame, bg=self.DARK_THEME["bg"])
        questions_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Описание
        description = tk.Label(questions_container, 
                text="Ответьте на 5 вопросов, чтобы оценить необходимость покупки:",
                font=("Arial", 16, "bold"), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"], wraplength=main_width-80, justify=tk.LEFT)
        description.pack(anchor=tk.W, pady=(0, 30))
        
        questions = [
            {
                "text": "1. Эта покупка решает конкретную проблему или удовлетворяет реальную потребность?",
                "options": ["✅ Да, это необходимость", "🤔 Скорее да", "🚫 Нет, это просто хочу"]
            },
            {
                "text": "2. У вас уже есть что-то похожее или выполняющее ту же функцию?",
                "options": ["🚫 Нет, это первая такая вещь", "🤔 Есть, но устарело/не работает", "✅ Да, есть аналогичная"]
            },
            {
                "text": "3. Вы можете позволить себе эту покупку без ущерба для основных расходов?",
                "options": ["✅ Да, легко", "🤔 Придется немного ужать бюджет", "🚫 Нет, это будет в ущерб"]
            },
            {
                "text": "4. Вы подумали об этой покупке больше 24 часов?",
                "options": ["✅ Да, думаю уже несколько дней", "🤔 Несколько часов", "🚫 Только что увидел(а)"]
            },
            {
                "text": "5. Что произойдет, если вы откажетесь от этой покупки?",
                "options": ["🚫 Будет серьезная проблема", "🤔 Будет неудобно, но жить можно", "✅ Ничего особенного"]
            }
        ]
    
        # Переменные для хранения ответов
        dialog_vars = []
    
        for i, question in enumerate(questions):
            # Фрейм для вопроса
            question_frame = tk.Frame(questions_container, bg=self.DARK_THEME["surface"], 
                                relief=tk.FLAT, highlightbackground=self.DARK_THEME["divider"],
                                highlightthickness=1)
            question_frame.pack(fill=tk.X, pady=(0, 25))
        
            # Текст вопроса
            tk.Label(question_frame, text=question["text"], 
                font=("Arial", 14, "bold"), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["surface"], wraplength=main_width-100, justify=tk.LEFT).pack(anchor=tk.W, padx=20, pady=(20, 15))
        
            var = tk.StringVar(value="")
            dialog_vars.append(var)
        
            # Варианты ответов
            for option in question["options"]:
                option_frame = tk.Frame(question_frame, bg=self.DARK_THEME["surface"])
                option_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
                
                rb = tk.Radiobutton(option_frame, text=option, 
                            variable=var, value=option,
                            font=("Arial", 13), fg=self.DARK_THEME["text"],
                            bg=self.DARK_THEME["surface"],
                            selectcolor=self.DARK_THEME["accent"],
                            wraplength=main_width-120, justify=tk.LEFT,
                            activebackground=self.DARK_THEME["surface"])
                rb.pack(anchor=tk.W)
    
        # Фрейм для кнопок
        button_frame = tk.Frame(scrollable_frame, bg=self.DARK_THEME["bg"], 
                                pady=30, padx=20)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
        def analyze_answers():
            """Анализирует ответы и показывает результат"""
            answers = [var.get() for var in dialog_vars]
            
            # Проверка заполненности
            unanswered = [i+1 for i, answer in enumerate(answers) if answer == ""]
            if unanswered:
                messagebox.showwarning("Не все ответы", 
                                     f"Пожалуйста, ответьте на вопросы: {', '.join(map(str, unanswered))}")
                return
            
            # Подсчет баллов
            score = 0
            for answer in answers:
                if answer.startswith("✅"):
                    score += 2
                elif answer.startswith("🤔"):
                    score += 1
                elif answer.startswith("🚫"):
                    score += 0
            
            max_score = len(questions) * 2
            percentage = (score / max_score) * 100
            
            # Определение результата
            if percentage >= 70:
                result = "✅ РЕКОМЕНДАЦИЯ: Можно покупать\n\nЭта покупка выглядит обоснованной и необходимой."
                color = self.DARK_THEME["success"]
                action_text = "📝 Добавить в охлаждение"
            elif percentage >= 40:
                result = "🤔 РЕКОМЕНДАЦИЯ: Взвесить решение\n\nЕсть как доводы за, так и против покупки.\nРекомендуется подождать еще несколько дней."
                color = self.DARK_THEME["warning"]
                action_text = "📝 Добавить в охлаждение"
            else:
                result = "🚫 РЕКОМЕНДАЦИЯ: Отказаться\n\nПокупка выглядит импульсивной и необязательной.\nРекомендуется отказаться или отложить на 30 дней."
                color = self.DARK_THEME["error"]
                action_text = "❌ Отказаться от покупки"
            
            dialog_window.destroy()
            self.show_scanner_result(result, color, action_text, percentage)
    
        # Кнопка анализа
        analyze_btn = tk.Button(button_frame, text="🔍 ПРОАНАЛИЗИРОВАТЬ ОТВЕТЫ", 
                                font=("Arial", 16, "bold"),
                                bg=self.DARK_THEME["accent"], fg="#000000",
                                relief=tk.FLAT, bd=0,
                                command=analyze_answers,
                                padx=0, pady=18)
        analyze_btn.pack(fill=tk.X, pady=(0, 15))
            
        # Кнопка отмены
        cancel_btn = tk.Button(button_frame, text="← Назад", 
                                font=("Arial", 14),
                                bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"],
                                relief=tk.FLAT, bd=0,
                                command=dialog_window.destroy,
                                padx=0, pady=14)
        cancel_btn.pack(fill=tk.X)
            
        dialog_window.protocol("WM_DELETE_WINDOW", dialog_window.destroy)
    
        # Заставляем окно оставаться поверх всех
        def keep_on_top():
            if dialog_window.winfo_exists():
                dialog_window.attributes('-topmost', True)
                dialog_window.after(100, keep_on_top)
        
        keep_on_top()
    
    def show_scanner_result(self, result, color, action_text, percentage):
        """Показывает результат анализа"""
        result_window = tk.Toplevel(self.root)
        result_window.title("Результат проверки")
        result_window.geometry("400x800")
        result_window.configure(bg=self.DARK_THEME["bg"])
        result_window.resizable(False, False)
        
        # Позиционирование по центру
        root_x = self.root.winfo_x()
        root_y = self.root.winfo_y()
        root_width = self.root.winfo_width()
        root_height = self.root.winfo_height()
        
        window_width = 500
        window_height = 500
        
        x = root_x + (root_width - window_width) // 2
        y = root_y + (root_height - window_height) // 2
        
        result_window.geometry(f"{window_width}x{window_height}+{max(0, x)}+{max(0, y)}")
        
        # Делаем окно модальным и поверх всех
        result_window.transient(self.root)
        result_window.grab_set()
        result_window.attributes('-topmost', True)
        result_window.focus_force()
        
        self.root.lift()
        result_window.lift()
        
        # Основной контейнер
        main_container = tk.Frame(result_window, bg=self.DARK_THEME["bg"])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        header_frame = tk.Frame(main_container, bg=color, height=90)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📊 Результат анализа", 
                font=("Arial", 20, "bold"), fg="#000000", 
                bg=color).pack(expand=True)
        
        # Содержимое
        content_frame = tk.Frame(main_container, bg=self.DARK_THEME["bg"], 
                                padx=25, pady=25)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Оценка
        tk.Label(content_frame, text=f"🎯 Оценка необходимости: {percentage:.0f}%", 
                font=("Arial", 16, "bold"), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 20))
        
        # Результат
        result_lines = result.split('\n')
        for line in result_lines:
            if line.strip():
                tk.Label(content_frame, text=line, 
                        font=("Arial", 12), fg=color, 
                        bg=self.DARK_THEME["bg"], wraplength=450, justify=tk.LEFT).pack(anchor=tk.W, pady=3)
        
        # Пояснение
        tk.Label(content_frame, text="📋 Основано на ваших ответах на 5 ключевых вопросов.", 
                font=("Arial", 11), fg=self.DARK_THEME["secondary"], 
                bg=self.DARK_THEME["bg"], wraplength=450, justify=tk.LEFT).pack(anchor=tk.W, pady=(20, 0))
        
        def add_to_cooling():
            result_window.destroy()
            self.show_add_purchase()
        
        def close_with_message():
            result_window.destroy()
            messagebox.showinfo("Принято", "Вы отказались от покупки. Это поможет сохранить ваши финансы!")
        
        # Фрейм для кнопок
        button_frame = tk.Frame(main_container, bg=self.DARK_THEME["bg"], 
                              pady=20, padx=25)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Основная кнопка действия
        if "охлаждение" in action_text.lower():
            action_btn = tk.Button(button_frame, text=action_text, 
                                  font=("Arial", 13, "bold"),
                                  bg=self.DARK_THEME["accent"], fg="#000000",
                                  relief=tk.FLAT, bd=0,
                                  command=add_to_cooling,
                                  padx=0, pady=12)
            action_btn.pack(fill=tk.X, pady=(0, 10))
        else:
            action_btn = tk.Button(button_frame, text=action_text, 
                                  font=("Arial", 13, "bold"),
                                  bg=self.DARK_THEME["error"], fg="#000000",
                                  relief=tk.FLAT, bd=0,
                                  command=close_with_message,
                                  padx=0, pady=12)
            action_btn.pack(fill=tk.X, pady=(0, 10))
        
        # Кнопка "Назад"
        close_btn = tk.Button(button_frame, text="← Назад в главное меню", 
                             font=("Arial", 12),
                             bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"],
                             relief=tk.FLAT, bd=0,
                             command=result_window.destroy,
                             padx=0, pady=10)
        close_btn.pack(fill=tk.X)
        
        result_window.protocol("WM_DELETE_WINDOW", result_window.destroy)
        
        # Заставляем окно оставаться поверх всех
        def keep_on_top():
            if result_window.winfo_exists():
                result_window.attributes('-topmost', True)
                result_window.after(100, keep_on_top)
        
        result_window.after(100, keep_on_top)
    
    def init_navigation(self):
        theme = self.DARK_THEME
        
        # Создаем фрейм для навигации
        self.nav_frame = tk.Frame(self.root, bg=theme["surface"],
                                 height=70, highlightthickness=0)
        
        self.nav_buttons = {}
        
        nav_items = [
            ("🏠", "Главная", self.show_main_content),
            ("🛒", "Покупки", self.show_purchases_screen),
            ("🤖", "AI Помощник", self.show_ai_chat),
            ("🔍", "Сканер", self.show_scanner_screen),
            ("👤", "Профиль", self.show_profile_screen)
        ]
        
        for i, (icon, text, command) in enumerate(nav_items):
            btn_frame = tk.Frame(self.nav_frame, bg=theme["surface"], 
                               cursor="hand2")
            btn_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=0)
            
            # Контейнер для центрирования
            content_frame = tk.Frame(btn_frame, bg=theme["surface"])
            content_frame.pack(expand=True, fill=tk.BOTH)
            
            icon_label = tk.Label(content_frame, text=icon, font=("Arial", 16), 
                                 bg=theme["surface"], fg=theme["text"])
            icon_label.pack(pady=(8, 0))
            
            text_label = tk.Label(content_frame, text=text, font=("Arial", 9), 
                                 bg=theme["surface"], fg=theme["text"])
            text_label.pack(pady=(0, 8))
            
            def make_hover_effect(frame, content_frame, icon_lbl, text_lbl, cmd=command):
                def on_enter(e):
                    frame.configure(bg=theme["divider"])
                    content_frame.configure(bg=theme["divider"])
                    icon_lbl.configure(bg=theme["divider"], fg=theme["accent"])
                    text_lbl.configure(bg=theme["divider"], fg=theme["accent"])
                def on_leave(e):
                    frame.configure(bg=theme["surface"])
                    content_frame.configure(bg=theme["surface"])
                    icon_lbl.configure(bg=theme["surface"], fg=theme["text"])
                    text_lbl.configure(bg=theme["surface"], fg=theme["text"])
                def on_click(e):
                    cmd()
                frame.bind("<Enter>", on_enter)
                frame.bind("<Leave>", on_leave)
                frame.bind("<Button-1>", on_click)
                content_frame.bind("<Button-1>", on_click)
                icon_lbl.bind("<Button-1>", on_click)
                text_lbl.bind("<Button-1>", on_click)
            
            make_hover_effect(btn_frame, content_frame, icon_label, text_label)
            
            self.nav_buttons[text] = {
                "frame": btn_frame,
                "content_frame": content_frame,
                "icon": icon_label,
                "text": text_label
            }
        
    def set_active_nav(self, nav_name):
        theme = self.DARK_THEME
        
        for name, btn_data in self.nav_buttons.items():
            if name == nav_name:
                # Активная кнопка
                btn_data["frame"].configure(bg=theme["accent"])
                btn_data["content_frame"].configure(bg=theme["accent"])
                btn_data["icon"].configure(bg=theme["accent"], 
                                          fg="#000000")
                btn_data["text"].configure(bg=theme["accent"], 
                                          fg="#000000")
            else:
                # Неактивная кнопка
                btn_data["frame"].configure(bg=theme["surface"])
                btn_data["content_frame"].configure(bg=theme["surface"])
                btn_data["icon"].configure(bg=theme["surface"], 
                                          fg=theme["text"])
                btn_data["text"].configure(bg=theme["surface"], 
                                          fg=theme["text"])

    def clear_content(self):
        if self.content_container:
            self.content_container.destroy()
        
        # Очищаем ссылку на метку статуса сканера
        if hasattr(self, 'current_scanner_status_label'):
            self.current_scanner_status_label = None
        
        # Используем темную тему
        self.content_container = tk.Frame(self.root, bg=self.DARK_THEME["bg"])
        self.content_container.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
    
    def init_openai_assistant(self):
        try:
            api_key = self.get_openai_api_key()
            if api_key and api_key != "your-api-key-here":
                from openai_assistant import OpenAIAssistant
                self.ai_assistant = OpenAIAssistant(api_key, self.auth_system)
                print("✅ OpenAI помощник инициализирован")
                return True
            else:
                print("⚠️ API ключ OpenAI не найден")
                return False
        except Exception as e:
            print(f"❌ Ошибка инициализации OpenAI: {e}")
            return False
    
    def get_openai_api_key(self):
        try:
            from config import OPENAI_API_KEY
            if OPENAI_API_KEY and OPENAI_API_KEY.strip():
                return OPENAI_API_KEY.strip()
        except ImportError:
            pass
        import os
        api_key = os.environ.get("OPENAI_API_KEY")
        if api_key:
            return api_key
        try:
            with open(".env", "r") as f:
                for line in f:
                    if line.startswith("OPENAI_API_KEY="):
                        return line.split("=", 1)[1].strip()
        except:
            pass
        return None


    def apply_rounded_style(self):
        """Применяет закругленные стили ко всем виджетам"""
        
        # Стиль для ttk виджетов
        style = ttk.Style()
        
        # Настраиваем стили для закругленных кнопок
        style.configure("Rounded.TButton",
                       borderwidth=0,
                       focusthickness=0,
                       focuscolor="none",
                       relief="flat",
                       padding=10)
        
        # Стиль для закругленных полей ввода
        style.configure("Rounded.TEntry",
                       borderwidth=0,
                       focusthickness=0,
                       relief="flat",
                       padding=10)
        
        # Создаем изображения для закругленных кнопок
        try:
            # Создаем изображение для нормального состояния
            normal_img = tk.PhotoImage(width=1, height=1)
            # Создаем изображение для нажатого состояния
            pressed_img = tk.PhotoImage(width=1, height=1)
            # Создаем изображение для состояния наведения
            hover_img = tk.PhotoImage(width=1, height=1)
            
            style.element_create("RoundedButton.border", "image", normal_img,
                               ("pressed", pressed_img),
                               ("active", hover_img))
            style.layout("Rounded.TButton",
                        [("RoundedButton.border", {"sticky": "nswe"})])
        except:
            pass




    def show_login_screen(self):
        # Очистка предыдущего контента
        if self.content_container:
            self.content_container.destroy()
        self.show_navigation(False)
        self.current_screen = "auth"
        
        # Цвета для тёмной темы
        DARK_BG = "#1E1E1E"
        DARK_SURFACE = "#2C2C2C"
        DARK_TEXT = "#FFFFFF"
        DARK_SECONDARY = "#888888"
        DARK_ACCENT = "#FFCC00"
        
        self.content_container = tk.Frame(self.root, bg=DARK_BG)
        self.content_container.pack(fill="both", expand=True)

        # --- Верхний блок с картинкой БЕЗ обводки ---
        top_block = tk.Frame(self.content_container, bg=DARK_BG, height=150)
        top_block.pack(fill="x", pady=(20, 10))  # Увеличил верхний отступ
        top_block.pack_propagate(False)
        
        try:
            from PIL import Image, ImageTk
            
            # Загружаем и масштабируем логотип
            logo_img = Image.open("src/tassistant.png")
            
            # Делаем логотип больше
            logo_width = 300
            logo_height = 120
            
            # Сохраняем пропорции при масштабировании
            original_width, original_height = logo_img.size
            aspect_ratio = original_width / original_height
            new_height = logo_height
            new_width = int(new_height * aspect_ratio)
            
            if new_width > logo_width:
                new_width = logo_width
                new_height = int(new_width / aspect_ratio)
            
            logo_img = logo_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            
            # Просто Label без фона
            logo_label = tk.Label(top_block, image=self.logo_photo, bg=DARK_BG)
            logo_label.pack(expand=True)
            
        except Exception as e:
            print("Ошибка загрузки логотипа:", e)
            logo_label = tk.Label(top_block, text="T-Assistant", 
                                font=("Arial", 28, "bold"),
                                bg=DARK_BG, fg=DARK_ACCENT)
            logo_label.pack(expand=True)

        # --- Центральный блок с формой (УВЕЛИЧЕН по высоте) ---
        center_block = tk.Frame(self.content_container, bg=DARK_BG)
        center_block.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Закругленный контейнер для формы (ВЫСОКИЙ)
        form_container = tk.Canvas(center_block, bg=DARK_BG, highlightthickness=0, height=550)  # Увеличил с 500 до 550
        form_container.pack(fill="both", expand=True)
        
        # Рисуем закругленный фон формы
        form_width = 560
        form_height = 550  # Увеличил высоту формы
        form_container.create_rounded_rect(0, 0, form_width, form_height, 30, 
                                          fill=DARK_SURFACE, outline="")
        
        # Внутренний контент формы
        inner_frame = tk.Frame(form_container, bg=DARK_SURFACE)
        form_container.create_window(form_width//2, form_height//2, 
                                    window=inner_frame, anchor="center",
                                    width=form_width-00, height=form_height-0)

        # Заголовок
        tk.Label(inner_frame, text="Добрый день",
                 font=("Arial", 22, "bold"),
                 bg=DARK_SURFACE, fg=DARK_TEXT).pack(pady=(30, 10))  # Увеличил отступ сверху

        # Подзаголовок
        tk.Label(inner_frame, text="Для начала работы с приложением введите ваш никнейм",
                 font=("Arial", 14),
                 bg=DARK_SURFACE, fg=DARK_SECONDARY,
                 wraplength=400, justify="center").pack(pady=(0, 30))  # Уменьшил отступ

        # 3. Поле ввода логина с закругленными углами
        entry_frame = tk.Frame(inner_frame, bg=DARK_SURFACE, height=60)
        entry_frame.pack(fill="x", pady=(0, 30), padx=50)
        entry_frame.pack_propagate(False)

        # Canvas для закругленного фона
        entry_canvas = tk.Canvas(entry_frame, bg=DARK_SURFACE, highlightthickness=0)
        entry_canvas.pack(fill="both", expand=True)

        # Рисуем закругленный фон
        entry_canvas.create_rounded_rect(0, 5, 460, 55, 15, 
                                        fill="#3A3A3A", outline="")

        # Поле ввода поверх Canvas
        login_var = tk.StringVar()
        entry = tk.Entry(entry_canvas, textvariable=login_var,
                         font=("Arial", 16),
                         bg="#3A3A3A", fg=DARK_SECONDARY,  # Серый цвет для плейсхолдера
                         insertbackground=DARK_TEXT,
                         relief="flat", bd=0, highlightthickness=0,
                         justify="center")

        # Размещаем Entry по центру Canvas с небольшими отступами
        entry_window = entry_canvas.create_window(10, 30, window=entry, 
                                                 anchor="w", width=440, height=40)

        # Функция для обновления размера Entry при изменении размера Canvas
        def update_entry_size(event):
            width = entry_canvas.winfo_width()
            if width > 20:
                entry_canvas.coords(entry_window, 10, 30)
                entry_canvas.itemconfig(entry_window, width=width-20)

        entry_canvas.bind("<Configure>", update_entry_size)

        # Плейсхолдер
        entry.insert(0, "Введите имя")
        entry.placeholder_active = True

        def clear_placeholder(event):
            if entry.placeholder_active:
                entry.delete(0, tk.END)
                entry.config(fg=DARK_TEXT)  # Белый цвет для вводимого текста
                entry.placeholder_active = False

        def add_placeholder(event):
            if not entry.get() and not entry.placeholder_active:
                entry.insert(0, "Введите имя")
                entry.config(fg=DARK_SECONDARY)  # Серый цвет для плейсхолдера
                entry.placeholder_active = True

        entry.bind("<FocusIn>", clear_placeholder)
        entry.bind("<FocusOut>", add_placeholder)
        
        # Сразу после поля ввода - кнопка (перемещаем кнопку выше)
        btn_container = tk.Frame(inner_frame, bg=DARK_SURFACE, height=70)
        btn_container.pack(fill="x", pady=(0, 40), padx=50)  # Отступ снизу 40 для картинки
        btn_container.pack_propagate(False)

        # Закругленная кнопка (центрированная)
        btn_canvas = tk.Canvas(btn_container, bg=DARK_SURFACE, 
                              highlightthickness=0, width=240, height=60)
        btn_canvas.pack(expand=True)

        # Рисуем кнопку
        btn_canvas.create_rounded_rect(2, 2, 238, 58, 20, 
                                      fill=DARK_ACCENT, outline="")

        # Текст на кнопке
        btn_canvas.create_text(120, 30, text="Далее", 
                              font=("Arial", 16, "bold"),
                              fill="#000000")

        # Делаем кнопку кликабельной
        def on_btn_click(event):
            username = ""
            if hasattr(entry, 'placeholder_active') and entry.placeholder_active:
                username = ""
            else:
                username = entry.get().strip()
            
            if not username or username == "Введите имя":
                # Анимация ошибки
                entry_canvas.itemconfig(1, fill="#5A1E1E")
                btn_canvas.after(300, lambda: entry_canvas.itemconfig(1, fill="#3A3A3A"))
            else:
                self.handle_login(username)

        def on_btn_enter(event):
            btn_canvas.config(cursor="hand2")
            btn_canvas.itemconfig(1, fill="#FFD633")

        def on_btn_leave(event):
            btn_canvas.config(cursor="")
            btn_canvas.itemconfig(1, fill=DARK_ACCENT)

        btn_canvas.bind("<Button-1>", on_btn_click)
        btn_canvas.bind("<Enter>", on_btn_enter)
        btn_canvas.bind("<Leave>", on_btn_leave)

        # --- Фрейм для картинки ---
        bottom_container = tk.Frame(inner_frame, bg=DARK_SURFACE)
        bottom_container.pack(fill="both", expand=True, pady=(0, 00))

        # Правая часть - картинка aboba
        # Правая часть - картинка aboba
        right_frame = tk.Frame(bottom_container, bg=DARK_SURFACE)
        right_frame.pack(side="right", anchor="e", padx=(0, 00))  # anchor="e" для выравнивания вправо

                
        try:
            # Загружаем и масштабируем картинку aboba
            aboba_img = Image.open("src/aboba.png")
            
            # Увеличиваем размер картинки
            aboba_width = 500  # Еще больше
            aboba_height = 260  # Еще больше
            
            # Сохраняем пропорции
            original_width, original_height = aboba_img.size
            aspect_ratio = original_width / original_height
            new_height = aboba_height
            new_width = int(new_height * aspect_ratio)
            
            if new_width > aboba_width:
                new_width = aboba_width
                new_height = int(new_width / aspect_ratio)
            
            aboba_img = aboba_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            self.aboba_photo = ImageTk.PhotoImage(aboba_img)
            
            # Создаем Canvas для картинки
            img_canvas = tk.Canvas(right_frame, bg=DARK_SURFACE, highlightthickness=0,
                                  width=new_width + 30, height=new_height + 30)
            img_canvas.pack(expand=True)
            
            # Рисуем закругленный фон для картинки
            img_canvas.create_rounded_rect(0, 0, new_width + 40, new_height + 40, 20, 
                                          fill=DARK_SURFACE, outline="")
            
            # Помещаем картинку на Canvas
            img_label = tk.Label(img_canvas, image=self.aboba_photo, bg=DARK_SURFACE)
            img_canvas.create_window((new_width + 10)//2, (new_height + 10)//2-30, 
                                    window=img_label, anchor="center")
            
        except Exception as e:
            print("Ошибка загрузки нижней картинки:", e)
            # Запасной вариант - сообщение
            placeholder = tk.Label(right_frame, text="🐱", font=("Arial", 48),
                                 bg=DARK_SURFACE, fg=DARK_SECONDARY)
            placeholder.pack(expand=True)

        # Нижний отступ
        bottom_padding = tk.Frame(self.content_container, bg=DARK_BG, height=40)
        bottom_padding.pack(fill="x")





    def handle_login(self, username: str):
        username = username.strip()
        
        # Проверяем, не является ли строка плейсхолдером
        if not username or username == "Введите имя" or username == "":
            messagebox.showwarning("Ошибка", "Введите ваш никнейм!")
            return

        self.current_user = username

        try:
            # если есть метод login в AuthSystem
            if hasattr(self.auth_system, "login"):
                self.auth_system.login(username)
            else:
                # если нет — просто сохраняем пользователя
                print(f"Пользователь {username} вошёл")
        except Exception as e:
            messagebox.showerror("Ошибка входа", f"Не удалось войти: {e}")
            return

        # Переход на основной экран
        self.show_main_content()





    def show_auth_screen(self):
        """Упрощенный экран входа - только никнейм"""
        self.clear_content()
        self.show_navigation(False)
        self.current_screen = "auth"
        
        # Шапка
        header_frame = tk.Frame(self.content_container, bg=self.DARK_THEME["accent"], height=200)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🛡️", 
                font=("Arial", 48), fg="#000000", bg=self.DARK_THEME["accent"]).pack(pady=(40, 10))
        tk.Label(header_frame, text="T-Assistant", 
                font=("Arial", 28, "bold"), fg="#000000", bg=self.DARK_THEME["accent"]).pack()
        tk.Label(header_frame, text="Умный помощник покупок", 
                font=("Arial", 14), fg="#000000", bg=self.DARK_THEME["accent"]).pack(pady=(0, 30))
        
        # Основной контент
        content_frame = tk.Frame(self.content_container, bg=self.DARK_THEME["bg"], 
                                padx=24, pady=24)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(content_frame, text="Вход по никнейму", 
                font=("Arial", 18, "bold"), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 20))
        
        # Поле ввода
        input_frame = tk.Frame(content_frame, bg=self.DARK_THEME["bg"])
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(input_frame, text="Ваш никнейм", 
                font=("Arial", 11), fg=self.DARK_THEME["secondary"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 5))
        
        self.username_entry = tk.Entry(input_frame, font=("Arial", 14), 
                                      bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"], 
                                      relief=tk.FLAT, bd=0, highlightthickness=1,
                                      highlightbackground=self.DARK_THEME["divider"],
                                      highlightcolor=self.DARK_THEME["accent"])
        self.username_entry.pack(fill=tk.X, pady=(0, 25), ipady=10)
        self.username_entry.bind("<Return>", lambda e: self.handle_login(self.username_entry.get()))

        
        # Кнопка входа
        login_btn = tk.Button(content_frame, text="Войти / Создать", 
                              font=("Arial", 14, "bold"),
                              bg=self.DARK_THEME["accent"], fg="#000000",
                              relief=tk.FLAT, bd=0,
                              command=lambda: self.handle_login(self.username_entry.get()),
                              padx=0, pady=12)

        login_btn.pack(fill=tk.X, pady=(0, 20))
        
        # Информация
        info_frame = tk.Frame(content_frame, bg=self.DARK_THEME["surface"], relief=tk.FLAT)
        info_frame.pack(fill=tk.X, pady=(20, 0))
        
        info_text = """📝 Как это работает:
• Введите ваш никнейм
• Если вы новый пользователь, он будет создан автоматически
• При первом входе заполните анкету"""
        
        tk.Label(info_frame, text=info_text, 
                font=("Arial", 10), fg=self.DARK_THEME["secondary"], 
                bg=self.DARK_THEME["surface"], justify=tk.LEFT).pack(padx=16, pady=12)
    
    def perform_login(self):
        """Выполняет вход по никнейму"""
        username = self.username_entry.get().strip()
        
        if not username:
            messagebox.showerror("Ошибка", "Введите никнейм")
            return
        
        success, message = self.auth_system.login(username)
        
        if success:
            self.current_user = username
            messagebox.showinfo("Успех", message)
            
            # Проверяем, нужно ли заполнить анкету
            if self.auth_system.is_first_time_user(username):
                self.show_profile_setup_screen()
            else:
                self.show_main_content()
        else:
            messagebox.showerror("Ошибка", message)
    
    def show_profile_setup_screen(self):
        """Экран заполнения анкеты для новых пользователей"""
        self.clear_content()
        self.show_navigation(False)
        self.current_screen = "profile_setup"
        
        # Шапка
        header_frame = tk.Frame(self.content_container, bg=self.DARK_THEME["accent"], height=150)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="📝", font=("Arial", 36), 
                fg="#000000", bg=self.DARK_THEME["accent"]).pack(pady=(20, 10))
        tk.Label(header_frame, text="Заполните анкету", 
                font=("Arial", 22, "bold"), fg="#000000", bg=self.DARK_THEME["accent"]).pack()
        tk.Label(header_frame, text="Это поможет персонализировать ваш опыт", 
                font=("Arial", 11), fg="#000000", 
                bg=self.DARK_THEME["accent"]).pack(pady=(0, 20))
        
        # Основной контент с прокруткой
        canvas = tk.Canvas(self.content_container, bg=self.DARK_THEME["bg"], 
                          highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.content_container, orient="vertical", 
                                 command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.DARK_THEME["bg"])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Контейнер для полей
        form_frame = tk.Frame(scrollable_frame, bg=self.DARK_THEME["bg"], 
                             padx=24, pady=24)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        # Поля анкеты
        fields = [
            ("💰", "Месячный доход (₽)", "income"),
            ("💵", "Сколько откладываете в месяц (₽)", "savings"),
            ("🏦", "Текущие накопления (₽)", "current_savings")
        ]
        
        self.profile_entries = {}
        
        for icon, label, key in fields:
            field_frame = tk.Frame(form_frame, bg=self.DARK_THEME["bg"])
            field_frame.pack(fill=tk.X, pady=(0, 20))
            
            # Иконка и текст
            label_frame = tk.Frame(field_frame, bg=self.DARK_THEME["bg"])
            label_frame.pack(fill=tk.X, pady=(0, 8))
            
            tk.Label(label_frame, text=icon, font=("Arial", 16), 
                    fg=self.DARK_THEME["accent"], bg=self.DARK_THEME["bg"]).pack(side=tk.LEFT, padx=(0, 10))
            tk.Label(label_frame, text=label, 
                    font=("Arial", 12), fg=self.DARK_THEME["text"], 
                    bg=self.DARK_THEME["bg"]).pack(side=tk.LEFT)
            
            # Поле ввода
            entry = tk.Entry(field_frame, font=("Arial", 14), 
                           bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"], 
                           relief=tk.FLAT, bd=0, highlightthickness=1,
                           highlightbackground=self.DARK_THEME["divider"],
                           highlightcolor=self.DARK_THEME["accent"])
            entry.pack(fill=tk.X, ipady=10)
            entry.insert(0, "0")
            
            self.profile_entries[key] = entry
        
        # Информационный блок
        info_card = tk.Frame(form_frame, bg=self.DARK_THEME["surface"], relief=tk.FLAT)
        info_card.pack(fill=tk.X, pady=(0, 30))
        
        info_text = """💡 Эта информация поможет:
• Рассчитать разумные сроки охлаждения покупок
• Давать персонализированные рекомендации
• Предлагать оптимальные планы накоплений"""
        
        tk.Label(info_card, text=info_text, 
                font=("Arial", 10), fg=self.DARK_THEME["secondary"], 
                bg=self.DARK_THEME["surface"], justify=tk.LEFT).pack(padx=16, pady=12)
        
        # Кнопка сохранения
        save_btn = tk.Button(form_frame, text="💾 Сохранить и продолжить", 
                            font=("Arial", 14, "bold"),
                            bg=self.DARK_THEME["accent"], fg="#000000",
                            relief=tk.FLAT, bd=0,
                            command=self.save_profile_setup,
                            padx=0, pady=12)
        save_btn.pack(fill=tk.X)
    
    def save_profile_setup(self):
        """Сохраняет анкету пользователя"""
        try:
            # Получаем значения из полей
            income = float(self.profile_entries["income"].get())
            savings = float(self.profile_entries["savings"].get())
            current_savings = float(self.profile_entries["current_savings"].get())
            
            # Проверяем корректность
            if income < 0 or savings < 0 or current_savings < 0:
                messagebox.showerror("Ошибка", "Значения не могут быть отрицательными")
                return
            
            # Подготавливаем данные профиля
            profile_data = {
                "monthly_income": income,
                "savings_per_month": savings,
                "current_savings": current_savings
            }
            
            # Сохраняем в системе
            if self.auth_system.complete_first_time_setup(self.current_user, profile_data):
                messagebox.showinfo("Успех", "Анкета сохранена! Добро пожаловать в T-Assistant!")
                self.show_main_content()
            else:
                messagebox.showerror("Ошибка", "Не удалось сохранить анкету")
                
        except ValueError:
            messagebox.showerror("Ошибка", "Пожалуйста, введите корректные числа")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения: {str(e)}") 
    
    def show_main_content(self):
        if not self.current_user:
            return
        
        theme = self.DARK_THEME
        
        self.clear_content()
        self.show_navigation(True)
        self.set_active_nav("Главная")
        self.current_screen = "main"
        
        # Основной контейнер с отступами по бокам
        main_container = tk.Frame(self.content_container, bg=theme["bg"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)  # Отступы по бокам
        
        # Canvas для прокрутки
        canvas = tk.Canvas(main_container, bg=theme["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=canvas.yview)
        
        # Прокручиваемый фрейм С ОТСТУПОМ СПРАВА
        scrollable_frame = tk.Frame(canvas, bg=theme["bg"])
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        # Создаем окно с отступом справа для скроллбара
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Функция для обновления ширины с учетом отступа
        def update_scrollable_width(event):
            # Оставляем 30px для скроллбара
            available_width = event.width - 30
            if available_width > 0:
                canvas.itemconfig(window_id, width=available_width)
        
        canvas.bind("<Configure>", update_scrollable_width)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        user_data = self.auth_system.get_user_data(self.current_user)
        
        # 1. Логотип и приветствие в одной строке
        header_frame = tk.Frame(scrollable_frame, bg=theme["bg"], height=100)
        header_frame.pack(fill=tk.X, pady=(0, 20))
        header_frame.pack_propagate(False)
        
        # Левая часть - логотип
        left_header = tk.Frame(header_frame, bg=theme["bg"])
        left_header.pack(side="left", fill="y", pady=20)
        
        try:
            from PIL import Image, ImageTk
            logo_img = Image.open("src/tassistant.png")
            # Уменьшаем размер логотипа еще больше
            logo_img.thumbnail((120, 50), Image.Resampling.LANCZOS)  # Было 150x60
            self.logo_photo = ImageTk.PhotoImage(logo_img)
            
            logo_label = tk.Label(left_header, image=self.logo_photo, bg=theme["bg"])
            logo_label.pack(side="left", padx=(0, 20))
        except Exception as e:
            print("Ошибка загрузки логотипа:", e)
            tk.Label(left_header, text="T-Assistant", 
                    font=("Arial", 18, "bold"),
                    bg=theme["bg"], fg=theme["accent"]).pack(side="left", padx=(0, 20))
        
        # Правая часть - приветствие (опускаем ниже)
        right_header = tk.Frame(header_frame, bg=theme["bg"])
        right_header.pack(side="right", fill="y", pady=30)  # Увеличил pady
        
        tk.Label(right_header, text=f"Привет, {self.current_user}!",
                 font=("Arial", 18, "bold"),
                 bg=theme["bg"], fg=theme["text"]).pack()
        
        # 2. Быстрые действия
        actions_frame = tk.Frame(scrollable_frame, bg=theme["bg"])
        actions_frame.pack(fill=tk.X, pady=(0, 30))
        
        tk.Label(actions_frame, text="Быстрые действия", 
                font=("Arial", 16, "bold"), fg=theme["text"], 
                bg=theme["bg"]).pack(anchor=tk.W, pady=(0, 15))
        
        actions = [
            ("➕", "Добавить покупку", lambda: self.show_add_purchase()),
            ("⚡", "Быстрый анализ", lambda: self.show_quick_analysis()),
            ("🔔", "Уведомления", lambda: self.check_notifications()),
            ("📊", "Статистика", lambda: self.show_statistics_screen())
        ]
        
        # Grid 2x2 для быстрых действий
        for i in range(2):
            row_frame = tk.Frame(actions_frame, bg=theme["bg"])
            row_frame.pack(fill=tk.X, pady=(0, 12))
            
            for j in range(2):
                index = i * 2 + j
                if index < len(actions):
                    icon, text, command = actions[index]
                    
                    # Карточка действия (занимает половину ширины с отступом)
                    action_card = tk.Frame(row_frame, bg=theme["surface"], 
                                         relief="flat", cursor="hand2")
                    action_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, 
                                   padx=(0, 12) if j == 0 else (0, 0))
                    
                    # Содержимое карточки
                    content_frame = tk.Frame(action_card, bg=theme["surface"], 
                                           padx=20, pady=25)  # Увеличил pady
                    content_frame.pack(fill=tk.BOTH, expand=True)
                    
                    # Иконка
                    tk.Label(content_frame, text=icon, font=("Arial", 28),  # Увеличил шрифт
                            bg=theme["surface"], fg=theme["accent"]).pack(pady=(0, 12))
                    
                    # Текст
                    tk.Label(content_frame, text=text, font=("Arial", 12), 
                            bg=theme["surface"], fg=theme["text"],
                            wraplength=120, justify="center").pack()
                    
                    # Делаем всю карточку кликабельной
                    def make_clickable(frame, content_frame, cmd=command):
                        def on_click(e):
                            cmd()
                        def on_enter(e):
                            frame.configure(bg=theme["divider"])
                            content_frame.configure(bg=theme["divider"])
                            for child in content_frame.winfo_children():
                                if isinstance(child, tk.Label):
                                    child.configure(bg=theme["divider"])
                        def on_leave(e):
                            frame.configure(bg=theme["surface"])
                            content_frame.configure(bg=theme["surface"])
                            for child in content_frame.winfo_children():
                                if isinstance(child, tk.Label):
                                    child.configure(bg=theme["surface"])
                        
                        frame.bind("<Button-1>", on_click)
                        frame.bind("<Enter>", on_enter)
                        frame.bind("<Leave>", on_leave)
                        
                        # Делаем кликабельными все дочерние элементы
                        for widget in [frame, content_frame] + content_frame.winfo_children():
                            widget.bind("<Button-1>", on_click)
                            widget.config(cursor="hand2")
                    
                    make_clickable(action_card, content_frame)
        
            # 3. Статистика (УВЕЛИЧЕННЫЙ РАЗДЕЛ)
        stats_frame = tk.Frame(scrollable_frame, bg=theme["bg"])
        stats_frame.pack(fill=tk.X, pady=(0, 30), padx=0)  # Убрал padx здесь
        
        tk.Label(stats_frame, text="Ваша статистика", 
                font=("Arial", 16, "bold"), fg=theme["text"], 
                bg=theme["bg"]).pack(anchor=tk.W, pady=(0, 20))  # Увеличил отступ снизу
        
        purchases = user_data.get("purchases", [])
        
        if purchases:
            active_purchases = [p for p in purchases if p.get("status") == "cooling"]
            cooling_value = sum(p.get("price", 0) for p in active_purchases)
            completed_purchases = [p for p in purchases if p.get("status") == "purchased"]
            completed_value = sum(p.get("price", 0) for p in completed_purchases)
            
            stats_items = [
                ("⏳ На охлаждении", f"{len(active_purchases)} шт", f"{cooling_value:,} ₽".replace(",", " ")),
                ("✅ Завершено", f"{len(completed_purchases)} шт", f"{completed_value:,} ₽".replace(",", " ")),
                ("💰 Всего покупок", f"{len(purchases)} шт", f"{cooling_value + completed_value:,} ₽".replace(",", " "))
            ]
            
            for title, count, value in stats_items:
                # Карточка статистики (увеличил высоту и добавил отступы по бокам)
                stat_card = tk.Frame(stats_frame, bg=theme["surface"], 
                                   relief="flat", height=110)  # Увеличил с 90 до 110
                stat_card.pack(fill=tk.X, pady=(0, 12), padx=0)  # padx=0, отступы будут внутри
                stat_card.pack_propagate(False)
                
                # Внутренний контейнер с отступами
                inner_card = tk.Frame(stat_card, bg=theme["surface"])
                inner_card.pack(fill=tk.BOTH, expand=True, padx=20, pady=0)  # Отступы по бокам
                
                content_frame = tk.Frame(inner_card, bg=theme["surface"],
                                       pady=25)  # Увеличил вертикальные отступы
                content_frame.pack(fill=tk.BOTH, expand=True)
                
                # Заголовок слева
                tk.Label(content_frame, text=title, font=("Arial", 13, "bold"),  # Увеличил шрифт
                        fg=theme["text"], bg=theme["surface"],
                        anchor="w", justify="left").pack(side=tk.LEFT, fill=tk.Y, expand=True)
                
                # Значения справа (с увеличенными шрифтами)
                values_frame = tk.Frame(content_frame, bg=theme["surface"])
                values_frame.pack(side=tk.RIGHT, fill=tk.Y)
                
                # Количество (увеличил шрифт и отступы)
                count_label = tk.Label(values_frame, text=count, font=("Arial", 13),  # Увеличил
                        fg=theme["secondary"], bg=theme["surface"])
                count_label.pack(anchor="e", pady=(0, 5))  # Отступ снизу
                
                # Цена (увеличил шрифт сильно)
                value_label = tk.Label(values_frame, text=value, font=("Arial", 18, "bold"),  # Увеличил сильно
                        fg=theme["accent"], bg=theme["surface"])
                value_label.pack(anchor="e", pady=(0, 0))  # Убрал верхний отступ
        
        else:
            # Пустая статистика (увеличил в 1.5 раза)
            empty_card = tk.Frame(stats_frame, bg=theme["surface"], 
                                relief="flat", height=150)  # Увеличил с 100 до 150
            empty_card.pack(fill=tk.X, pady=(0, 12), padx=0)
            empty_card.pack_propagate(False)
            
            # Внутренний контейнер с отступами
            inner_empty = tk.Frame(empty_card, bg=theme["surface"])
            inner_empty.pack(fill=tk.BOTH, expand=True, padx=20, pady=0)
            
            content_frame = tk.Frame(inner_empty, bg=theme["surface"],
                                   pady=40)  # Увеличил отступы
            content_frame.pack(fill=tk.BOTH, expand=True)
            
            # Иконка (увеличил)
            tk.Label(content_frame, text="📭", font=("Arial", 36),  # Увеличил иконку
                    fg=theme["secondary"], bg=theme["surface"]).pack(pady=(0, 15))
            
            # Текст (увеличил шрифты)
            tk.Label(content_frame, text="Нет данных о покупках", 
                    font=("Arial", 16, "bold"), fg=theme["text"],  # Увеличил
                    bg=theme["surface"]).pack()
            
            tk.Label(content_frame, text="Добавьте первую покупку для отслеживания", 
                    font=("Arial", 12), fg=theme["secondary"],  # Увеличил
                    bg=theme["surface"]).pack(pady=(8, 0))
        
        # 4. Финансовый профиль (на всю ширину)
        profile_frame = tk.Frame(scrollable_frame, bg=theme["bg"])
        profile_frame.pack(fill=tk.X, pady=(0, 40))
        
        tk.Label(profile_frame, text="Финансовый профиль", 
                font=("Arial", 16, "bold"), fg=theme["text"], 
                bg=theme["bg"]).pack(anchor=tk.W, pady=(0, 15))
        
        profile = user_data.get("personal_profile", {})
        income = profile.get("monthly_income", 0)
        savings = profile.get("savings_per_month", 0)
        current_savings = profile.get("current_savings", 0)
        
        # Карточка профиля на всю ширину
        profile_card = tk.Frame(profile_frame, bg=theme["surface"], 
                              relief="flat")
        profile_card.pack(fill=tk.X, pady=(0, 20))
        
        profile_items = [
            ("💰", "Месячный доход", f"{income:,} ₽".replace(",", " ")),
            ("💵", "Откладываю в месяц", f"{savings:,} ₽".replace(",", " ")),
            ("🏦", "Текущие накопления", f"{current_savings:,} ₽".replace(",", " "))
        ]
        
        for icon, label, value in profile_items:
            item_frame = tk.Frame(profile_card, bg=theme["surface"],
                                padx=20, pady=18)  # Увеличил pady
            item_frame.pack(fill=tk.X)
            
            # Иконка и текст слева
            left_frame = tk.Frame(item_frame, bg=theme["surface"])
            left_frame.pack(side=tk.LEFT, fill=tk.Y)
            
            tk.Label(left_frame, text=icon, font=("Arial", 16), 
                    fg=theme["accent"], bg=theme["surface"]).pack(side=tk.LEFT, padx=(0, 12))
            
            tk.Label(left_frame, text=label, font=("Arial", 12), 
                    fg=theme["text"], bg=theme["surface"]).pack(side=tk.LEFT)
            
            # Значение справа
            tk.Label(item_frame, text=value, font=("Arial", 14, "bold"), 
                    fg=theme["accent"], bg=theme["surface"]).pack(side=tk.RIGHT)
            
            # Разделитель (кроме последнего элемента)
            if profile_items.index((icon, label, value)) < len(profile_items) - 1:
                separator = tk.Frame(profile_card, bg=theme["divider"], 
                                   height=1)
                separator.pack(fill=tk.X, padx=20)
        
        # Кнопка редактирования профиля (выше и по центру)
        edit_btn_frame = tk.Frame(profile_frame, bg=theme["bg"])
        edit_btn_frame.pack(fill=tk.X, pady=(10, 0))  # Добавил pady сверху
        
        def edit_profile():
            self.show_personal_profile_setup()
        
        # Закругленная кнопка (выше)
        edit_canvas = tk.Canvas(edit_btn_frame, bg=theme["bg"], 
                              highlightthickness=0, height=55)  # Увеличил высоту
        edit_canvas.pack(fill=tk.X)
        
        # Получаем ширину для центрирования
        edit_btn_frame.update_idletasks()
        btn_width = edit_btn_frame.winfo_width()
        
        edit_canvas.create_rounded_rect(0, 5, btn_width, 50, 25,  # Увеличил radius
                                      fill=theme["surface"], outline="")
        
        # Текст по центру (реально по центру)
        edit_canvas.create_text(btn_width/2, 28,  # Центрируем по ширине и высоте
                              text="✏️ Редактировать профиль", 
                              font=("Arial", 13),  # Немного увеличил шрифт
                              fill=theme["text"])
        
        def on_edit_click(event):
            edit_profile()
        
        def on_edit_enter(event):
            edit_canvas.config(cursor="hand2")
            edit_canvas.itemconfig(1, fill=theme["divider"])
        
        def on_edit_leave(event):
            edit_canvas.config(cursor="")
            edit_canvas.itemconfig(1, fill=theme["surface"])
        
        edit_canvas.bind("<Button-1>", on_edit_click)
        edit_canvas.bind("<Enter>", on_edit_enter)
        edit_canvas.bind("<Leave>", on_edit_leave)
        
        # Принудительно обновляем геометрию для правильного центрирования
        scrollable_frame.update_idletasks()


    def show_purchases_screen(self):
        if not self.current_user:
            return
        
        theme = self.DARK_THEME
        
        self.clear_content()
        self.show_navigation(True)
        self.set_active_nav("Покупки")
        self.current_screen = "purchases"
        
        # Основной контейнер
        main_frame = tk.Frame(self.content_container, bg=theme["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0)
        
        # Canvas и скроллбар
        canvas = tk.Canvas(main_frame, bg=theme["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        
        # Прокручиваемый фрейм
        scrollable_frame = tk.Frame(canvas, bg=theme["bg"])
        
        # Создаем окно в Canvas
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Функция для обновления ширины
        def configure_scrollable(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(window_id, width=event.width)
        
        # Привязываем события
        scrollable_frame.bind("<Configure>", configure_scrollable)
        canvas.bind("<Configure>", configure_scrollable)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Хедер с заголовком и кнопкой добавления
        header_frame = tk.Frame(scrollable_frame, bg=theme["bg"])
        header_frame.pack(fill=tk.X, pady=(20, 0), padx=20)
        
        tk.Label(header_frame, text="🛒 Покупки", 
                font=("Arial", 20, "bold"), fg=theme["text"], 
                bg=theme["bg"]).pack(side=tk.LEFT)
        
        # Стилизованная кнопка добавления
        add_btn_frame = tk.Frame(header_frame, bg=theme["accent"], 
                                relief="flat", cursor="hand2",
                                height=40, width=40)
        add_btn_frame.pack(side=tk.RIGHT)
        add_btn_frame.pack_propagate(False)
        
        add_btn_label = tk.Label(add_btn_frame, text="＋", font=("Arial", 24),
                                fg="#000000", bg=theme["accent"])
        add_btn_label.pack(expand=True)
        
        add_btn_frame.bind("<Button-1>", lambda e: self.show_add_purchase())
        add_btn_label.bind("<Button-1>", lambda e: self.show_add_purchase())
        
        user_data = self.auth_system.get_user_data(self.current_user)
        purchases = user_data.get("purchases", [])
        
        if not purchases:
            # Экран "Нет покупок" - ВСЁ ПО ЦЕНТРУ
            empty_frame = tk.Frame(scrollable_frame, bg=theme["bg"])
            empty_frame.pack(fill=tk.BOTH, expand=True)
            
            # Центрирующий фрейм
            center_container = tk.Frame(empty_frame, bg=theme["bg"])
            center_container.place(relx=0.5, rely=0.5, anchor="center")
            
            # Большая иконка
            icon_label = tk.Label(center_container, text="🛍️", font=("Arial", 72), 
                                fg=theme["secondary"], bg=theme["bg"])
            icon_label.pack(pady=(0, 20))
            
            # Текст заголовка
            title_label = tk.Label(center_container, text="Нет покупок", 
                                font=("Arial", 22, "bold"), fg=theme["text"], 
                                bg=theme["bg"])
            title_label.pack(pady=(0, 10))
            
            # Описание
            desc_label = tk.Label(center_container, 
                                text="Добавьте первую покупку для отслеживания", 
                                font=("Arial", 14), fg=theme["secondary"], 
                                bg=theme["bg"])
            desc_label.pack(pady=(0, 30))
            
            # Кнопка добавления - по центру
            add_first_btn = tk.Button(center_container, text="➕ Добавить покупку", 
                                     font=("Arial", 14, "bold"),
                                     bg=theme["accent"], fg="#000000",
                                     relief="flat", bd=0,
                                     command=self.show_add_purchase,
                                     padx=30, pady=15)
            add_first_btn.pack()
            
            # Добавляем hover эффект
            def on_enter_add_btn(e):
                add_first_btn.config(bg=theme["primary_light"], cursor="hand2")
            
            def on_leave_add_btn(e):
                add_first_btn.config(bg=theme["accent"], cursor="")
            
            add_first_btn.bind("<Enter>", on_enter_add_btn)
            add_first_btn.bind("<Leave>", on_leave_add_btn)
            
        else:
            # Фрейм фильтров
            filter_frame = tk.Frame(scrollable_frame, bg=theme["bg"])
            filter_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
            
            filters = ["Все", "Охлаждение", "Купленные"]
            self.purchase_filter_var = tk.StringVar(value="Все")
            
            # Фрейм для кнопок фильтров
            filters_container = tk.Frame(filter_frame, bg=theme["surface"], 
                                        relief="flat", height=40)
            filters_container.pack(fill=tk.X)
            filters_container.pack_propagate(False)
            
            # Создаем кнопки фильтров с закругленными углами
            for i, filter_text in enumerate(filters):
                filter_btn = tk.Button(filters_container, text=filter_text,
                                     font=("Arial", 11),
                                     bg=theme["surface"], fg=theme["text"],
                                     relief="flat", bd=0,
                                     command=lambda f=filter_text: self.set_filter_and_update(f))
                filter_btn.pack(side=tk.LEFT, padx=2, fill=tk.BOTH, expand=True)
                
                # Стилизация активной кнопки
                def update_filter_style():
                    for child in filters_container.winfo_children():
                        if isinstance(child, tk.Button):
                            if child.cget("text") == self.purchase_filter_var.get():
                                child.config(bg=theme["accent"], fg="#000000")
                            else:
                                child.config(bg=theme["surface"], fg=theme["text"])
                
                # Привязываем обновление стиля
                self.purchase_filter_var.trace("w", lambda *args: update_filter_style())
            
            # Контейнер для карточек покупок
            self.purchases_container = tk.Frame(scrollable_frame, bg=theme["bg"])
            self.purchases_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
            
            # Отображаем покупки
            purchases_sorted = sorted(purchases, 
                                     key=lambda x: x.get("added_at", ""), 
                                     reverse=True)
            self.display_purchases(purchases_sorted)
        
        # Инициализируем стиль фильтров
        if purchases:
            if hasattr(self, 'purchase_filter_var'):
                self.purchase_filter_var.set("Все")
            self.filter_purchases()




    def display_purchases(self, purchases):
        for widget in self.purchases_container.winfo_children():
            widget.destroy()
        current_filter = self.purchase_filter_var.get()
        if current_filter == "Охлаждение":
            filtered = [p for p in purchases if p.get("status") == "cooling"]
        elif current_filter == "Купленные":
            filtered = [p for p in purchases if p.get("status") == "purchased"]
        else:
            filtered = purchases
        if not filtered:
            empty_label = tk.Label(self.purchases_container, 
                                  text="Нет покупок по выбранному фильтру",
                                  font=("Arial", 12), fg=self.DARK_THEME["secondary"],
                                  bg=self.DARK_THEME["bg"])
            empty_label.pack(pady=40)
            return
        for purchase in filtered:
            self.create_purchase_card(self.purchases_container, purchase)
    
    def create_purchase_card(self, parent, purchase):
        # ВАЖНО: читаем статус ИЗ ПОЛЯ "status"
        status = purchase.get("status", "cooling")
        purchase_id = purchase.get("id")
        
        print(f"[CARD] Создаем карточку покупки:")
        print(f"  ID: {purchase_id}")
        print(f"  Название: {purchase.get('name')}")
        print(f"  Статус: {status}")
        print(f"  Накопления: {purchase.get('current_savings', 0)}/{purchase.get('price', 0)}")
        
        # Определяем цвет и иконку по статусу
        if status == "purchased":
            bg_color = self.DARK_THEME["success"]
            status_icon = "✅"
            status_text = "Куплено"
        elif status == "cooling":
            bg_color = self.DARK_THEME["warning"]
            status_icon = "⏳"
            status_text = "На охлаждении"
        else:
            bg_color = self.DARK_THEME["info"]
            status_icon = "📝"
            status_text = status
        
        card = tk.Frame(parent, bg=self.DARK_THEME["surface"], relief=tk.FLAT,
                    highlightbackground=self.DARK_THEME["divider"],
                    highlightthickness=1)
        card.pack(fill=tk.X, pady=(0, 8))
        
        # Верхняя часть карточки
        top_frame = tk.Frame(card, bg=self.DARK_THEME["surface"])
        top_frame.pack(fill=tk.X, padx=16, pady=12)
        
        # Название покупки
        name = purchase.get("name", purchase.get("item_name", "Без названия"))
        tk.Label(top_frame, text=name, font=("Arial", 14, "bold"),
                fg=self.DARK_THEME["text"], bg=self.DARK_THEME["surface"],
                wraplength=280, justify=tk.LEFT).pack(side=tk.LEFT, anchor=tk.W, fill=tk.X, expand=True)
        
        # Кнопка удаления
        delete_btn = tk.Label(top_frame, text="🗑️", font=("Arial", 12),
                            fg=self.DARK_THEME["error"], bg=self.DARK_THEME["surface"],
                            cursor="hand2")
        delete_btn.pack(side=tk.RIGHT, padx=(5, 0))
        delete_btn.bind("<Button-1>", lambda e, pid=purchase_id: self.delete_purchase(pid))
        
        # Статус с иконкой (ТОЛЬКО для "cooling" показываем кнопку "Куплено")
        status_label = tk.Label(top_frame, text=f"{status_icon} {status_text}", 
                            font=("Arial", 12), fg=bg_color, bg=self.DARK_THEME["surface"])
        status_label.pack(side=tk.RIGHT, padx=(0, 10))
        
        # Нижняя часть карточки
        bottom_frame = tk.Frame(card, bg=self.DARK_THEME["surface"])
        bottom_frame.pack(fill=tk.X, padx=16, pady=(0, 12))
        
        # Цена
        price = purchase.get("price", purchase.get("estimated_price", 0))
        tk.Label(bottom_frame, text=f"{price:,} ₽".replace(",", " "),
                font=("Arial", 12, "bold"), fg=self.DARK_THEME["text"],
                bg=self.DARK_THEME["surface"]).pack(side=tk.LEFT)
        
        # Категория
        category = purchase.get("category", "Без категории")
        tk.Label(bottom_frame, text=category, font=("Arial", 11),
                fg=self.DARK_THEME["secondary"], bg=self.DARK_THEME["surface"]).pack(side=tk.RIGHT)
        
        # Если покупка на охлаждении - показываем прогресс и кнопку "Куплено"
        if status == "cooling":
            # Прогресс накоплений
            progress_frame = tk.Frame(card, bg=self.DARK_THEME["surface"])
            progress_frame.pack(fill=tk.X, padx=16, pady=(0, 12))
            
            current_savings = purchase.get("current_savings", 0)
            savings_target = purchase.get("savings_target", price)
            
            if savings_target > 0:
                progress_percent = min(100, int((current_savings / savings_target) * 100))
                
                # Полоса прогресса
                progress_bg = tk.Frame(progress_frame, bg=self.DARK_THEME["divider"], height=8)
                progress_bg.pack(fill=tk.X, pady=(5, 0))
                progress_bg.pack_propagate(False)
                
                progress_fg = tk.Frame(progress_bg, bg=self.DARK_THEME["success"], 
                                    width=progress_percent * 3)
                progress_fg.pack(side=tk.LEFT, fill=tk.Y)
                
                # Текст прогресса
                progress_text = tk.Label(progress_frame, 
                                    text=f"Накоплено: {current_savings:,} ₽ из {savings_target:,} ₽ ({progress_percent}%)".replace(",", " "),
                                    font=("Arial", 10), fg=self.DARK_THEME["secondary"],
                                    bg=self.DARK_THEME["surface"])
                progress_text.pack(anchor=tk.W, pady=(5, 0))
                
                # Кнопка добавления накоплений
                add_savings_btn = tk.Button(progress_frame, text="➕ Добавить накопления",
                                        font=("Arial", 9),
                                        bg=self.DARK_THEME["info"], fg="#000000",
                                        relief=tk.FLAT, bd=0,
                                        command=lambda pid=purchase_id: self.add_savings_dialog(pid),
                                        padx=8, pady=4)
                add_savings_btn.pack(anchor=tk.W, pady=(5, 0))
            
            # Время охлаждения и кнопка "Куплено"
            action_frame = tk.Frame(card, bg=self.DARK_THEME["surface"])
            action_frame.pack(fill=tk.X, padx=16, pady=(0, 12))
            
            cooling_until = purchase.get("cooling_until", "")
            try:
                if cooling_until:
                    cooling_until_dt = datetime.strptime(cooling_until, "%Y-%m-%d %H:%M:%S")
                    now = datetime.now()
                    if cooling_until_dt > now:
                        days_left = (cooling_until_dt - now).days
                        if days_left > 0:
                            time_text = f"⏰ Осталось: {days_left} дней"
                        else:
                            hours_left = (cooling_until_dt - now).seconds // 3600
                            time_text = f"⏰ Осталось: {hours_left} часов"
                    else:
                        time_text = "✅ Можно покупать"
                else:
                    time_text = "Не указано"
            except:
                time_text = cooling_until if cooling_until else "Не указано"
            
            tk.Label(action_frame, text=time_text, font=("Arial", 11),
                    fg=self.DARK_THEME["secondary"], bg=self.DARK_THEME["surface"]).pack(side=tk.LEFT)
            
            # Кнопка "Куплено" только для покупок на охлаждении
            btn_frame = tk.Frame(action_frame, bg=self.DARK_THEME["surface"])
            btn_frame.pack(side=tk.RIGHT)
            
            purchased_btn = tk.Button(btn_frame, text="✅",
                                    font=("Arial", 9),
                                    bg=self.DARK_THEME["success"], fg="#000000",
                                    relief=tk.FLAT, bd=0,
                                    command=lambda pid=purchase_id: self.mark_as_purchased(pid),
                                    padx=8, pady=4)
            purchased_btn.pack(side=tk.LEFT, padx=2)
    
    def add_savings_dialog(self, purchase_id):
        """Диалог для добавления накоплений на покупку"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Добавить накопления")
        dialog.configure(bg=self.DARK_THEME["bg"])
        dialog.resizable(False, False)
        
        # Делаем окно модальным
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Получаем информацию о покупке
        purchase = self.auth_system.get_purchase(self.current_user, purchase_id)
        if not purchase:
            messagebox.showerror("Ошибка", "Покупка не найдена")
            return
        
        price = purchase.get("price", 0)
        current_savings = purchase.get("current_savings", 0)
        item_name = purchase.get("name", "Неизвестный товар")
        
        # Настройка размера и позиции
        dialog_width = 400
        dialog_height = 400
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog_width) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog_height) // 2
        dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
        
        # Основной контейнер
        main_frame = tk.Frame(dialog, bg=self.DARK_THEME["bg"], padx=20, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Заголовок
        header_frame = tk.Frame(main_frame, bg=self.DARK_THEME["bg"])
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(header_frame, text="💵 Добавить накопления", 
                font=("Arial", 16, "bold"), fg=self.DARK_THEME["text"],
                bg=self.DARK_THEME["bg"]).pack()
        
        # Информация о покупке
        info_frame = tk.Frame(main_frame, bg=self.DARK_THEME["surface"], 
                            relief=tk.FLAT, padx=15, pady=10)
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(info_frame, text=f"📦 {item_name}", 
                font=("Arial", 13, "bold"), fg=self.DARK_THEME["text"],
                bg=self.DARK_THEME["surface"], wraplength=350).pack(anchor=tk.W, pady=(0, 5))
        
        tk.Label(info_frame, text=f"💰 Цена: {price:,} ₽".replace(",", " "), 
                font=("Arial", 12), fg=self.DARK_THEME["accent"],
                bg=self.DARK_THEME["surface"]).pack(anchor=tk.W, pady=(0, 3))
        
        tk.Label(info_frame, text=f"💾 Уже накоплено: {current_savings:,} ₽".replace(",", " "), 
                font=("Arial", 12), fg=self.DARK_THEME["secondary"],
                bg=self.DARK_THEME["surface"]).pack(anchor=tk.W, pady=(0, 3))
        
        # Поле для ввода суммы
        input_frame = tk.Frame(main_frame, bg=self.DARK_THEME["bg"])
        input_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(input_frame, text="Сумма для добавления:", 
                font=("Arial", 12), fg=self.DARK_THEME["text"],
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 8))
        
        # Контейнер для поля ввода и знака рубля
        entry_container = tk.Frame(input_frame, bg=self.DARK_THEME["bg"])
        entry_container.pack(fill=tk.X)
        
        # Поле ввода
        amount_var = tk.StringVar()
        amount_entry = tk.Entry(entry_container, textvariable=amount_var,
                            font=("Arial", 14), 
                            bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"], 
                            relief=tk.FLAT, bd=0, highlightthickness=1,
                            highlightbackground=self.DARK_THEME["divider"],
                            highlightcolor=self.DARK_THEME["accent"])
        amount_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=8, padx=(0, 10))
        
        # Знак рубля
        tk.Label(entry_container, text="₽", font=("Arial", 14), 
                fg=self.DARK_THEME["text"], bg=self.DARK_THEME["bg"]).pack(side=tk.LEFT)
        
        # Фрейм для кнопок
        button_frame = tk.Frame(main_frame, bg=self.DARK_THEME["bg"])
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Функция сохранения (ВНУТРЕННЯЯ ФУНКЦИЯ - правильный уровень!)
        def save_savings():
            try:
                amount_str = amount_var.get().strip()
                if not amount_str:
                    messagebox.showerror("Ошибка", "Введите сумму")
                    amount_entry.focus_set()
                    return
                
                amount = float(amount_str)
                if amount <= 0:
                    messagebox.showerror("Ошибка", "Сумма должна быть больше 0")
                    amount_entry.focus_set()
                    return
                
                # Рассчитываем новую сумму
                new_savings = current_savings + amount
                
                print(f"[DEBUG] Добавляем накопления:")
                print(f"  Товар: {item_name}")
                print(f"  Старые накопления: {current_savings}")
                print(f"  Добавляем: {amount}")
                print(f"  Новые накопления: {new_savings}")
                print(f"  Цена: {price}")
                
                # Обновляем покупку
                update_data = {"current_savings": new_savings}
                
                if self.auth_system.update_purchase(self.current_user, purchase_id, update_data):
                    messagebox.showinfo("Успех", f"✅ Добавлено {amount:,} ₽".replace(",", " "))
                    
                    # Проверяем, достигли ли цели
                    if new_savings >= price:
                        messagebox.showinfo("Поздравляем!", 
                                        f"🎉 Вы накопили достаточно средств!\n"
                                        f"Покупка '{item_name}' теперь отмечена как купленная.")
                    
                    dialog.destroy()
                    self.show_purchases_screen()  # Обновляем экран
                else:
                    messagebox.showerror("Ошибка", "❌ Не удалось сохранить накопления")
                    
            except ValueError:
                messagebox.showerror("Ошибка", "⚠️ Введите корректную сумму (например: 1500)")
                amount_entry.focus_set()
            except Exception as e:
                messagebox.showerror("Ошибка", f"❌ Ошибка: {str(e)}")
                import traceback
                traceback.print_exc()
        
        # Обработка нажатия Enter
        def on_enter_pressed(event):
            save_savings()
        
        amount_entry.bind("<Return>", on_enter_pressed)
        
        # Кнопка Сохранить (БОЛЬШАЯ и ЗАМЕТНАЯ)
        save_btn = tk.Button(button_frame, text="💾 СОХРАНИТЬ",
                        font=("Arial", 14, "bold"),
                        bg=self.DARK_THEME["success"], fg="#000000",
                        relief=tk.FLAT, bd=0,
                        command=save_savings,
                        padx=30, pady=12)
        save_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Кнопка Отмена
        cancel_btn = tk.Button(button_frame, text="Отмена",
                            font=("Arial", 12),
                            bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"],
                            relief=tk.FLAT, bd=0,
                            command=dialog.destroy,
                            padx=20, pady=10)
        cancel_btn.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Фокус на поле ввода
        amount_entry.focus_set()
        
        # Обработка закрытия окна
        dialog.protocol("WM_DELETE_WINDOW", dialog.destroy)
        
        # Принудительное обновление окна
        dialog.update()
    
    def delete_purchase(self, purchase_id):
        if messagebox.askyesno("Подтверждение", "Вы уверены, что хотите удалить эту покупку?"):
            try:
                user_data = self.auth_system.get_user_data(self.current_user)
                purchases = user_data.get("purchases", [])
                new_purchases = [p for p in purchases if p.get("id") != purchase_id]
                if len(new_purchases) < len(purchases):
                    if self.auth_system.update_user_data(self.current_user, {"purchases": new_purchases}):
                        messagebox.showinfo("Успех", "Покупка удалена")
                        self.show_purchases_screen()
                    else:
                        messagebox.showerror("Ошибка", "Не удалось удалить покупку")
                else:
                    messagebox.showerror("Ошибка", "Покупка не найдена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при удалении: {str(e)}")
    
    def filter_purchases(self):
        try:
            user_data = self.auth_system.get_user_data(self.current_user)
            purchases = user_data.get("purchases", [])
            purchases_sorted = sorted(purchases, 
                                     key=lambda x: x.get("added_at", ""), 
                                     reverse=True)
            self.display_purchases(purchases_sorted)
        except Exception as e:
            print(f"Ошибка фильтрации: {e}")
    
    def show_add_purchase(self):
        self.clear_content()
        self.show_navigation(True)
        self.current_screen = "add_purchase"
        header_frame = tk.Frame(self.content_container, bg=self.DARK_THEME["bg"])
        header_frame.pack(fill=tk.X, pady=(20, 0))
        back_btn = tk.Label(header_frame, text="←", font=("Arial", 20),
                           fg=self.DARK_THEME["text"], bg=self.DARK_THEME["bg"],
                           cursor="hand2")
        back_btn.pack(side=tk.LEFT, padx=20)
        back_btn.bind("<Button-1>", lambda e: self.show_purchases_screen())
        tk.Label(header_frame, text="Новая покупка", 
                font=("Arial", 20, "bold"), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"]).pack(side=tk.LEFT)
        content_frame = tk.Frame(self.content_container, bg=self.DARK_THEME["bg"], 
                                padx=24, pady=24)
        content_frame.pack(fill=tk.BOTH, expand=True)
        input_frame = tk.Frame(content_frame, bg=self.DARK_THEME["bg"])
        input_frame.pack(fill=tk.X, pady=(0, 20))
        tk.Label(input_frame, text="Название товара", 
                font=("Arial", 11), fg=self.DARK_THEME["secondary"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 5))
        self.purchase_name_entry = tk.Entry(input_frame, font=("Arial", 14), 
                                           bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"], 
                                           relief=tk.FLAT, bd=0, highlightthickness=1,
                                           highlightbackground=self.DARK_THEME["divider"],
                                           highlightcolor=self.DARK_THEME["accent"])
        self.purchase_name_entry.pack(fill=tk.X, pady=(0, 15), ipady=10)
        tk.Label(input_frame, text="Категория", 
                font=("Arial", 11), fg=self.DARK_THEME["secondary"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 5))
        self.purchase_category_var = tk.StringVar()
        purchase_category_combo = ttk.Combobox(input_frame, textvariable=self.purchase_category_var,
                                             font=("Arial", 14), state="readonly")
        purchase_category_combo['values'] = [
            "Электроника", "Одежда и обувь", "Бытовая техника", "Автомобиль",
            "Путешествия", "Образование", "Здоровье и спорт", "Дом и ремонт",
            "Хобби и развлечения", "Еда и напитки", "Красота и здоровье",
            "Другое"
        ]
        purchase_category_combo.pack(fill=tk.X, pady=(0, 15), ipady=10)
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TCombobox", fieldbackground=self.DARK_THEME["surface"],
                       foreground=self.DARK_THEME["text"],
                       background=self.DARK_THEME["surface"],
                       borderwidth=0, highlightthickness=1,
                       highlightbackground=self.DARK_THEME["divider"],
                       highlightcolor=self.DARK_THEME["accent"])
        tk.Label(input_frame, text="Цена (₽)", 
                font=("Arial", 11), fg=self.DARK_THEME["secondary"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 5))
        self.purchase_price_entry = tk.Entry(input_frame, font=("Arial", 14), 
                                            bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"], 
                                            relief=tk.FLAT, bd=0, highlightthickness=1,
                                            highlightbackground=self.DARK_THEME["divider"],
                                            highlightcolor=self.DARK_THEME["accent"])
        self.purchase_price_entry.pack(fill=tk.X, pady=(0, 25), ipady=10)
        analyze_btn = tk.Button(content_frame, text="🔍 Проанализировать", 
                               font=("Arial", 14, "bold"),
                               bg=self.DARK_THEME["accent"], fg="#000000",
                               relief=tk.FLAT, bd=0,
                               command=self.analyze_purchase,
                               padx=0, pady=12)
        analyze_btn.pack(fill=tk.X)
    
    def analyze_purchase(self):
        item_name = self.purchase_name_entry.get().strip()
        category = self.purchase_category_var.get()
        price_str = self.purchase_price_entry.get().strip()
        if not item_name:
            messagebox.showerror("Ошибка", "Введите название товара")
            return
        if not category:
            messagebox.showerror("Ошибка", "Выберите категорию")
            return
        try:
            price = float(price_str)
            if price <= 0:
                messagebox.showerror("Ошибка", "Цена должна быть положительным числом")
                return
        except ValueError:
            messagebox.showerror("Ошибка", "Введите корректную цену")
            return
        try:
            cooling_result = self.cooling_manager.calculate_cooling_period(price, category, item_name)
            result_window = tk.Toplevel(self.root)
            result_window.title("Результат анализа")
            result_window.geometry("450x600")
            result_window.configure(bg=self.DARK_THEME["bg"])
            result_window.resizable(False, True)
            x = self.root.winfo_x() + 25
            y = self.root.winfo_y() + 150
            result_window.geometry(f"450x600+{x}+{y}")
            header_frame = tk.Frame(result_window, bg=self.DARK_THEME["accent"], 
                                    height=80)
            header_frame.pack(fill=tk.X)
            header_frame.pack_propagate(False)
            if cooling_result.get("recommended", True):
                title = "✅ Анализ завершен"
            else:
                title = "❌ Рекомендация отказаться"
            tk.Label(header_frame, text=title, 
                    font=("Arial", 16, "bold"), fg="#000000", 
                    bg=self.DARK_THEME["accent"]).pack(pady=25)
            content_frame = tk.Frame(result_window, bg=self.DARK_THEME["bg"])
            content_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
            canvas = tk.Canvas(content_frame, bg=self.DARK_THEME["bg"], 
                              highlightthickness=0)
            scrollbar = ttk.Scrollbar(content_frame, orient="vertical", 
                                     command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg=self.DARK_THEME["bg"])
            scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            message = cooling_result.get("message", "")
            lines = message.split('\n')
            for line in lines:
                if line.startswith("🎯 **") or line.startswith("✅ **") or line.startswith("❌ **"):
                    text = line.replace("🎯 **", "").replace("✅ **", "").replace("❌ **", "").replace("**", "")
                    tk.Label(scrollable_frame, text=text, 
                            font=("Arial", 14, "bold"), fg=self.DARK_THEME["text"], 
                            bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 10))
                elif line.startswith("💰 **"):
                    text = line.replace("💰 **", "").replace("**", "")
                    tk.Label(scrollable_frame, text=text, 
                            font=("Arial", 12, "bold"), fg=self.DARK_THEME["text"], 
                            bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(5, 0))
                elif line.startswith("📁 **"):
                    text = line.replace("📁 **", "").replace("**", "")
                    tk.Label(scrollable_frame, text=text, 
                            font=("Arial", 11), fg=self.DARK_THEME["secondary"], 
                            bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(5, 0))
                elif line.startswith("📊 **"):
                    text = line.replace("📊 **", "").replace("**", "")
                    tk.Label(scrollable_frame, text=text, 
                            font=("Arial", 12, "bold"), fg=self.DARK_THEME["text"], 
                            bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(15, 5))
                elif line.startswith("⏱️ **"):
                    text = line.replace("⏱️ **", "").replace("**", "")
                    tk.Label(scrollable_frame, text=text, 
                            font=("Arial", 11, "bold"), fg=self.DARK_THEME["accent"], 
                            bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(5, 0))
                elif line.startswith("📅 **"):
                    text = line.replace("📅 **", "").replace("**", "")
                    tk.Label(scrollable_frame, text=text, 
                            font=("Arial", 11), fg=self.DARK_THEME["success"], 
                            bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(5, 0))
                elif line.startswith("💵 **"):
                    text = line.replace("💵 **", "").replace("**", "")
                    tk.Label(scrollable_frame, text=text, 
                            font=("Arial", 11), fg=self.DARK_THEME["info"], 
                            bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(5, 0))
                elif line.startswith("💡 **"):
                    text = line.replace("💡 **", "").replace("**", "")
                    tk.Label(scrollable_frame, text=text, 
                            font=("Arial", 12, "bold"), fg=self.DARK_THEME["text"], 
                            bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(15, 5))
                elif line.startswith("   • ") or line.startswith("• "):
                    text = line[4:] if line.startswith("   • ") else line[2:]
                    tk.Label(scrollable_frame, text=f"    {text}", 
                            font=("Arial", 10), fg=self.DARK_THEME["secondary"], 
                            bg=self.DARK_THEME["bg"], 
                            wraplength=300, justify=tk.LEFT).pack(anchor=tk.W, pady=2)
                elif line.startswith("1.") or line.startswith("2.") or line.startswith("3."):
                    tk.Label(scrollable_frame, text=line, 
                            font=("Arial", 10, "bold"), fg=self.DARK_THEME["text"], 
                            bg=self.DARK_THEME["bg"],
                            wraplength=300, justify=tk.LEFT).pack(anchor=tk.W, pady=5)
                elif line.strip():
                    tk.Label(scrollable_frame, text=line, 
                            font=("Arial", 10), fg=self.DARK_THEME["secondary"], 
                            bg=self.DARK_THEME["bg"],
                            wraplength=300, justify=tk.LEFT).pack(anchor=tk.W, pady=3)
            button_frame = tk.Frame(result_window, bg=self.DARK_THEME["bg"], pady=16)
            button_frame.pack(fill=tk.X, padx=16)
            if cooling_result.get("recommended", True) and cooling_result.get("total_days", 0) > 0:
                add_btn = tk.Button(button_frame, text="➕ Добавить в охлаждение", 
                                   font=("Arial", 12, "bold"),
                                   bg=self.DARK_THEME["accent"], fg="#000000",
                                   relief=tk.FLAT, bd=0,
                                   command=lambda: self.add_to_cooling(item_name, price, category, cooling_result, result_window),
                                   padx=0, pady=10)
                add_btn.pack(fill=tk.X, pady=(0, 8))
            close_btn = tk.Button(button_frame, text="← Назад", 
                                 font=("Arial", 11),
                                 bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"],
                                 relief=tk.FLAT, bd=0,
                                 command=result_window.destroy,
                                 padx=0, pady=8)
            close_btn.pack(fill=tk.X)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при анализе: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def add_to_cooling(self, item_name, price, category, cooling_result, parent_window):
        try:
            purchase_item = self.cooling_manager.create_purchase_item(item_name, price, category, cooling_result)
            
            # ЯВНО устанавливаем статус
            purchase_item["status"] = "cooling"
            
            print(f"[MAIN] Добавляем покупку в охлаждение:")
            print(f"  Название: {item_name}")
            print(f"  Статус: {purchase_item.get('status')}")
            print(f"  Цена: {price}")
            
            if self.auth_system.add_purchase(self.current_user, purchase_item):
                messagebox.showinfo("Успех", f"Покупка '{item_name}' добавлена в систему охлаждения на {cooling_result.get('total_days', 0)} дней")
                parent_window.destroy()
                self.show_purchases_screen()
            else:
                messagebox.showerror("Ошибка", "Не удалось добавить покупку")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при добавлении покупки: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def show_ai_chat(self):
        if not self.current_user:
            return
        if not self.ai_assistant:
            if not self.init_openai_assistant():
                self.show_no_ai_warning()
                return
        self.clear_content()
        self.show_navigation(True)
        self.set_active_nav("AI Помощник")
        self.current_screen = "ai_chat"
        header_frame = tk.Frame(self.content_container, bg="#1A1A1A",  # Темный фон
                                height=140)  # Увеличить высоту
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="🤖", font=("Arial", 40),  # Увеличить иконку
                fg=self.DARK_THEME["accent"], bg="#1A1A1A").pack(pady=(25, 8))  # Желтый текст
        tk.Label(header_frame, text="AI Финансовый Ассистент",  # Изменить название
                font=("Arial", 20, "bold"), fg=self.DARK_THEME["accent"], bg="#1A1A1A").pack()  # Желтый
        tk.Label(header_frame, text="Ваш персональный помощник по покупкам и финансам", 
                font=("Arial", 13), fg=self.DARK_THEME["accent"],  # Желтый
                bg="#1A1A1A").pack(pady=(0, 25))  # Увеличить отступ
        main_container = tk.Frame(self.content_container, bg=self.DARK_THEME["bg"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(10, 16))
        status_frame = tk.Frame(main_container, bg="#2C2C2C", relief=tk.FLAT)
        status_frame.pack(fill=tk.X, pady=(0, 16))
        # Получаем реальный статус
        if hasattr(self, 'ai_assistant') and self.ai_assistant and not self.ai_assistant.test_mode:
            status_text = f"✅ Подключено к {self.ai_assistant.model}"
        else:
            status_text = "⚠️ Тестовый режим (без OpenAI)"

        tk.Label(status_frame, text=status_text, 
                font=("Arial", 12, "bold"), fg="#FFFFFF",  # Белый текст
                bg="#2C2C2C").pack(pady=12)  # Увеличить отступы
        chat_frame = tk.Frame(main_container, bg=self.DARK_THEME["bg"])
        chat_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 16))
        chat_canvas = tk.Canvas(chat_frame, bg=self.DARK_THEME["bg"], 
                              highlightthickness=0)
        scrollbar = ttk.Scrollbar(chat_frame, orient="vertical", 
                                 command=chat_canvas.yview)
        self.chat_container = tk.Frame(chat_canvas, bg=self.DARK_THEME["bg"])
        self.chat_container.bind("<Configure>", lambda e: chat_canvas.configure(scrollregion=chat_canvas.bbox("all")))
        chat_canvas.create_window((0, 0), window=self.chat_container, anchor="nw", width=440)
        chat_canvas.configure(yscrollcommand=scrollbar.set)
        chat_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        input_frame = tk.Frame(main_container, bg=self.DARK_THEME["bg"])
        input_frame.pack(fill=tk.X, side=tk.BOTTOM)
        self.chat_input = tk.Text(input_frame, font=("Arial", 12), 
                                bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"], 
                                relief=tk.FLAT, bd=0, highlightthickness=1,
                                highlightbackground=self.DARK_THEME["divider"],
                                highlightcolor=self.DARK_THEME["accent"],
                                height=3, wrap=tk.WORD)
        self.chat_input.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8), pady=8)
        send_btn = tk.Button(input_frame, text="➤", 
                            font=("Arial", 16, "bold"),
                            bg=self.DARK_THEME["accent"], fg="#000000",
                            relief=tk.FLAT, bd=0,
                            command=self.send_openai_message,
                            width=3, height=3)
        send_btn.pack(side=tk.RIGHT, pady=8)
        self.chat_input.bind("<Return>", self.on_enter_pressed)
        self.chat_input.bind("<Shift-Return>", lambda e: "break")
        quick_questions_frame = tk.Frame(main_container, bg=self.DARK_THEME["bg"])
        quick_questions_frame.pack(fill=tk.X, pady=(0, 16))
        tk.Label(quick_questions_frame, text="Быстрые вопросы:", 
                font=("Arial", 12, "bold"), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 8))
        quick_questions = [
            "💸 Как экономить на покупках?",
            "📱 Стоит ли покупать новый iPhone?",
            "💰 Как составить семейный бюджет?",
            "🏠 Как накопить на квартиру?",
            "💳 Взять кредит или копить?",
            "📊 Проанализируй мои покупки"
        ]
        for i in range(0, len(quick_questions), 2):
            row_frame = tk.Frame(quick_questions_frame, bg=self.DARK_THEME["bg"])
            row_frame.pack(fill=tk.X, pady=(0, 8))
            for j in range(2):
                if i + j < len(quick_questions):
                    question = quick_questions[i + j]
                    btn = tk.Button(row_frame, text=question,
                                  font=("Arial", 10),
                                  bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"],
                                  relief=tk.FLAT, bd=0,
                                  command=lambda q=question: self.ask_quick_question(q),
                                  wraplength=160, justify=tk.LEFT,
                                  padx=8, pady=6)
                    btn.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8) if j == 0 else 0)
        history_frame = tk.Frame(main_container, bg=self.DARK_THEME["bg"])
        history_frame.pack(fill=tk.X, pady=(8, 0))
        clear_btn = tk.Button(history_frame, text="🧹 Очистить историю", 
                             font=("Arial", 10),
                             bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"],
                             relief=tk.FLAT, bd=0,
                             command=self.clear_openai_chat,
                             padx=12, pady=6)
        clear_btn.pack(side=tk.LEFT)
        welcome_message = "Привет! Я ваш финансовый помощник на базе OpenAI GPT. 🤖\n\n"
        welcome_message += "Могу помочь с:\n"
        welcome_message += "• Анализом покупок\n• Составлением бюджета\n• Советами по экономии\n"
        welcome_message += "• Накоплениями\n• Кредитными вопросами\n\n"
        welcome_message += "Задавайте вопросы или используйте быстрые вопросы выше!"
        self.show_ai_message("🤖 Финансовый помощник", welcome_message)
    
    def show_user_message(self, message):
        from datetime import datetime
        theme = self.DARK_THEME  # Добавь эту строку
        
        message_frame = tk.Frame(self.chat_container, bg=theme["bg"])
        message_frame.pack(fill=tk.X, pady=(0, 12))
        
        # Замени primary_light на accent или добавь прозрачность
        msg_container = tk.Frame(message_frame, bg=theme["accent"])
        msg_container.pack(anchor=tk.E, padx=8)
        
        tk.Label(msg_container, text=f"👤 {self.current_user}", 
                font=("Arial", 10, "bold"), fg="#000000",  # Черный текст на желтом
                bg=theme["accent"]).pack(anchor=tk.E, padx=12, pady=(8, 4))
        
        message_label = tk.Label(msg_container, text=message, 
                               font=("Arial", 11), fg="#000000",  # Черный текст
                               bg=theme["accent"],
                               wraplength=280, justify=tk.LEFT)
        message_label.pack(anchor=tk.E, padx=12, pady=(0, 8))
        
        time_str = datetime.now().strftime("%H:%M")
        tk.Label(msg_container, text=time_str, 
                font=("Arial", 9), fg="#666666",  # Темно-серый
                bg=theme["accent"]).pack(anchor=tk.E, padx=12, pady=(0, 8))
        
        self.chat_container.update_idletasks()
        canvas = self.chat_container.master
        if canvas:
            canvas.yview_moveto(1.0)

    def show_ai_message(self, sender, message):
        from datetime import datetime
        theme = self.DARK_THEME  # Добавь эту строку
        
        message_frame = tk.Frame(self.chat_container, bg=theme["bg"])
        message_frame.pack(fill=tk.X, pady=(0, 12))
        
        msg_container = tk.Frame(message_frame, bg=theme["surface"])
        msg_container.pack(anchor=tk.W, padx=8)
        
        tk.Label(msg_container, text=sender, 
                font=("Arial", 10, "bold"), fg=theme["text"], 
                bg=theme["surface"]).pack(anchor=tk.W, padx=12, pady=(8, 4))
        
        message_label = tk.Label(msg_container, text=message, 
                            font=("Arial", 11), fg=theme["text"], 
                            bg=theme["surface"],
                            wraplength=280, justify=tk.LEFT)
        message_label.pack(anchor=tk.W, padx=12, pady=(0, 8))
        
        time_str = datetime.now().strftime("%H:%M")
        tk.Label(msg_container, text=time_str, 
                font=("Arial", 9), fg=theme["text_disabled"], 
                bg=theme["surface"]).pack(anchor=tk.W, padx=12, pady=(0, 8))
        
        self.chat_container.update_idletasks()
        canvas = self.chat_container.master
        if canvas:
            canvas.yview_moveto(1.0)

    def send_openai_message(self):
        if not self.ai_assistant:
            self.show_ai_message("❌ Ошибка", "AI помощник не инициализирован")
            return
        message = self.chat_input.get("1.0", tk.END).strip()
        if not message:
            return
        self.show_user_message(message)
        self.chat_input.delete("1.0", tk.END)
        loading_msg = self.show_loading_message()
        try:
            import threading
            def get_response():
                try:
                    response = self.ai_assistant.generate_response(self.current_user, message)
                    self.root.after(0, lambda: self.update_chat_response(loading_msg, response))
                except Exception as e:
                    error_msg = f"Ошибка: {str(e)}"
                    self.root.after(0, lambda: self.update_chat_response(loading_msg, error_msg))
            thread = threading.Thread(target=get_response, daemon=True)
            thread.start()
        except Exception as e:
            self.remove_loading_message(loading_msg)
            self.show_ai_message("❌ Ошибка", f"Не удалось отправить сообщение: {str(e)}")
    
    def on_enter_pressed(self, event):
        if not event.state & 0x1:
            self.send_openai_message()
            return "break"
        return None
    
    def ask_quick_question(self, question):
        question_text = question.split(maxsplit=1)[-1]
        self.chat_input.delete("1.0", tk.END)
        self.chat_input.insert("1.0", question_text)
        self.send_openai_message()
    
    def clear_openai_chat(self):
        if self.ai_assistant and self.current_user:
            result = self.ai_assistant.clear_history(self.current_user)
            self.show_ai_message("🧹 Очистка", result)
        for widget in self.chat_container.winfo_children():
            widget.destroy()
        self.show_ai_message("🤖 Финансовый помощник", 
                           "История очищена. Чем могу помочь?")
    
    def show_loading_message(self):
        message_frame = tk.Frame(self.chat_container, bg=self.DARK_THEME["bg"])
        message_frame.pack(fill=tk.X, pady=(0, 12))
        msg_container = tk.Frame(message_frame, bg=self.DARK_THEME["surface"])
        msg_container.pack(anchor=tk.W, padx=8)
        tk.Label(msg_container, text="🤖 Финансовый помощник", 
                font=("Arial", 10, "bold"), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["surface"]).pack(anchor=tk.W, padx=12, pady=(8, 4))
        dots_label = tk.Label(msg_container, text="Думаю", 
                            font=("Arial", 11), fg=self.DARK_THEME["secondary"], 
                            bg=self.DARK_THEME["surface"])
        dots_label.pack(anchor=tk.W, padx=12, pady=(0, 8))
        def animate_dots(count=0):
            dots = "." * ((count % 3) + 1)
            dots_label.config(text=f"Думаю{dots}")
            if hasattr(message_frame, 'exists') and message_frame.winfo_exists():
                self.root.after(500, lambda: animate_dots(count + 1))
        animate_dots()
        return message_frame

    def remove_loading_message(self, message_frame):
        if message_frame.winfo_exists():
            message_frame.destroy()

    def update_chat_response(self, loading_frame, response):
        self.remove_loading_message(loading_frame)
        self.show_ai_message("🤖 Финансовый помощник", response)

    def show_no_ai_warning(self):
        self.clear_content()
        self.show_navigation(True)
        self.set_active_nav("AI Помощник")
        header_frame = tk.Frame(self.content_container, bg=self.DARK_THEME["warning"], 
                                height=120)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="⚠️", font=("Arial", 36), 
                fg="#000000", bg=self.DARK_THEME["warning"]).pack(pady=(20, 5))
        tk.Label(header_frame, text="AI Помощник недоступен", 
                font=("Arial", 18, "bold"), fg="#000000", 
                bg=self.DARK_THEME["warning"]).pack()
        content_frame = tk.Frame(self.content_container, bg=self.DARK_THEME["bg"], 
                                padx=24, pady=24)
        content_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(content_frame, text="Для использования AI помощника:", 
                font=("Arial", 14, "bold"), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 20))
        steps = [
            "1. Получите API ключ на platform.openai.com",
            "2. Добавьте ключ в файл config.py:",
            "   OPENAI_API_KEY = 'ваш-ключ-здесь'",
            "3. Перезапустите приложение"
        ]
        for step in steps:
            tk.Label(content_frame, text=step, 
                    font=("Arial", 11), fg=self.DARK_THEME["text"], 
                    bg=self.DARK_THEME["bg"], justify=tk.LEFT).pack(anchor=tk.W, pady=2)
        local_btn = tk.Button(content_frame, text="🔄 Использовать локального помощника", 
                            font=("Arial", 12, "bold"),
                            bg=self.DARK_THEME["accent"], fg="#000000",
                            relief=tk.FLAT, bd=0,
                            command=self.show_local_ai_assistant,
                            padx=0, pady=12)
        local_btn.pack(fill=tk.X, pady=(20, 0))
    
    def show_local_ai_assistant(self):
        self.show_ai_message("🤖 Локальный помощник", 
                           "Локальный помощник еще не реализован. Пожалуйста, настройте OpenAI API ключ.")
    
    def show_scanner_screen(self):
        if not self.current_user:
            return
        
        theme = self.DARK_THEME
        
        self.clear_content()
        self.show_navigation(True)
        self.set_active_nav("Сканер")
        self.current_screen = "scanner"
        
        # Основной контейнер
        main_frame = tk.Frame(self.content_container, bg=theme["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0)
        
        # Canvas и скроллбар
        canvas = tk.Canvas(main_frame, bg=theme["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        
        # Прокручиваемый фрейм
        scrollable_frame = tk.Frame(canvas, bg=theme["bg"])
        
        # Создаем окно в Canvas
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Функция для обновления ширины
        def configure_scrollable(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(window_id, width=event.width)
        
        # Привязываем события
        scrollable_frame.bind("<Configure>", configure_scrollable)
        canvas.bind("<Configure>", configure_scrollable)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # НОВАЯ ШАПКА - ТЕМНЫЙ ФОН, ЖЕЛТЫЙ ТЕКСТ
        header_frame = tk.Frame(scrollable_frame, bg="#1A1A1A", height=140)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg="#1A1A1A")
        header_content.pack(expand=True)
        
        # Иконка
        tk.Label(header_content, text="🔍", 
                font=("Arial", 38),  # Увеличенная иконка
                fg=theme["accent"], bg="#1A1A1A").pack(pady=(25, 8))
        
        # Заголовок
        tk.Label(header_content, text="Сканер покупок", 
                font=("Arial", 20, "bold"), fg=theme["accent"], 
                bg="#1A1A1A").pack()
        
        # Подзаголовок
        tk.Label(header_content, text="Автоматическое обнаружение покупок в браузере", 
                font=("Arial", 13), fg=theme["accent"], 
                bg="#1A1A1A").pack(pady=(5, 25))
        
        # Основной контент
        content_frame = tk.Frame(scrollable_frame, bg=theme["bg"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Карточка статуса
        status_card = tk.Frame(content_frame, bg=theme["surface"], 
                              relief=tk.FLAT)
        status_card.pack(fill=tk.X, pady=(0, 24))
        
        # Статус сканера
        scanner_status_label = tk.Label(status_card, 
                                        text="Сканер выключен" if not self.scanner_running else "Сканер активен ✓", 
                                        font=("Arial", 16),  # Увеличен шрифт
                                        fg=theme["text"] if not self.scanner_running else theme["success"], 
                                        bg=theme["surface"])
        scanner_status_label.pack(pady=20)
        
        # Сохраняем ссылку на метку статуса
        self.current_scanner_status_label = scanner_status_label
        
        # Кнопки управления
        control_frame = tk.Frame(content_frame, bg=theme["bg"])
        control_frame.pack(fill=tk.X, pady=(0, 24))
        
        # Кнопка запуска
        start_btn = tk.Button(control_frame, text="▶️ Запустить сканер", 
                             font=("Arial", 14, "bold"),
                             bg="#28A745", fg="#000000",  # Зеленый
                             relief="flat", bd=0,
                             command=self.start_scanner,
                             padx=0, pady=12)
        start_btn.pack(fill=tk.X, pady=(0, 12))
        
        # Кнопка остановки
        stop_btn = tk.Button(control_frame, text="⏸️ Остановить сканер", 
                            font=("Arial", 14, "bold"),
                            bg="#FFC107", fg="#000000",  # Желтый
                            relief="flat", bd=0,
                            command=self.stop_scanner,
                            padx=0, pady=12)
        stop_btn.pack(fill=tk.X)
        
        # Информационная карточка
        info_card = tk.Frame(content_frame, bg=theme["surface"], 
                            relief=tk.FLAT)
        info_card.pack(fill=tk.X)
        
        tk.Label(info_card, text="Как работает сканер:", 
                font=("Arial", 14, "bold"), fg=theme["text"],  # Увеличен шрифт
                bg=theme["surface"]).pack(anchor=tk.W, padx=16, pady=(16, 8))
        
        info_text = """• Отслеживает активные окна браузера
    • Обнаруживает страницы покупок
    • Предлагает добавить товар в охлаждение
    • Работает в фоновом режиме
    • Безопасен и не собирает личные данные"""
        
        tk.Label(info_card, text=info_text, font=("Arial", 12),  # Увеличен шрифт
                fg=theme["secondary"], bg=theme["surface"],
                justify=tk.LEFT).pack(anchor=tk.W, padx=16, pady=(0, 16))
    

    def show_profile_screen(self):
        if not self.current_user:
            return
        
        theme = self.DARK_THEME
        
        self.clear_content()
        self.show_navigation(True)
        self.set_active_nav("Профиль")
        self.current_screen = "profile"
        
        # Основной контейнер
        main_frame = tk.Frame(self.content_container, bg=theme["bg"])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=0)
        
        # Canvas и скроллбар
        canvas = tk.Canvas(main_frame, bg=theme["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        
        # Прокручиваемый фрейм
        scrollable_frame = tk.Frame(canvas, bg=theme["bg"])
        
        # Создаем окно в Canvas
        window_id = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Функция для обновления ширины
        def configure_scrollable(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(window_id, width=event.width)
        
        # Привязываем события
        scrollable_frame.bind("<Configure>", configure_scrollable)
        canvas.bind("<Configure>", configure_scrollable)
        
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # НОВАЯ ШАПКА - ТЕМНЫЙ ФОН, ЖЕЛТЫЙ ТЕКСТ
        header_frame = tk.Frame(scrollable_frame, bg="#1A1A1A", height=140)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_content = tk.Frame(header_frame, bg="#1A1A1A")
        header_content.pack(expand=True)
        
        # Иконка
        tk.Label(header_content, text="👤", 
                font=("Arial", 40),  # Увеличенная иконка
                fg=theme["accent"], bg="#1A1A1A").pack(pady=(25, 8))
        
        # Имя пользователя
        tk.Label(header_content, text=self.current_user, 
                font=("Arial", 20, "bold"), fg=theme["accent"], 
                bg="#1A1A1A").pack()
        
        # Email (если есть)
        user_data = self.auth_system.get_user_data(self.current_user)
        email = user_data.get("email", "")
        if email:
            tk.Label(header_content, text=email, 
                    font=("Arial", 13), fg=theme["accent"], 
                    bg="#1A1A1A").pack(pady=(5, 25))
        else:
            tk.Label(header_content, text="Персональный профиль", 
                    font=("Arial", 13), fg=theme["accent"], 
                    bg="#1A1A1A").pack(pady=(5, 25))
        
        # Настройки профиля
        settings_frame = tk.Frame(scrollable_frame, bg=theme["bg"])
        settings_frame.pack(fill=tk.X, padx=20, pady=20)
        
        tk.Label(settings_frame, text="Настройки профиля", 
                font=("Arial", 18, "bold"), fg=theme["text"], 
                bg=theme["bg"]).pack(anchor=tk.W, pady=(0, 16))
        
        settings_items = [
            ("💰", "Финансовый профиль", lambda: self.show_personal_profile_setup()),
            ("🚫", "Запрещенные категории", lambda: self.show_forbidden_categories()),
            ("⏱️", "Диапазоны охлаждения", lambda: self.show_cooling_periods()),
            ("🔔", "Уведомления", lambda: self.show_notification_settings()),
            ("⚙️", "Настройки приложения", lambda: self.show_app_settings())
        ]
        
        for icon, text, command in settings_items:
            item_frame = tk.Frame(settings_frame, bg=theme["surface"], 
                                relief=tk.FLAT, cursor="hand2", height=60)
            item_frame.pack(fill=tk.X, pady=(0, 8))
            item_frame.pack_propagate(False)
            
            item_content = tk.Frame(item_frame, bg=theme["surface"])
            item_content.pack(fill=tk.BOTH, expand=True, padx=16)
            
            # Иконка
            tk.Label(item_content, text=icon, font=("Arial", 20), 
                    fg=theme["accent"], bg=theme["surface"]).pack(side=tk.LEFT)
            
            # Текст
            tk.Label(item_content, text=text, font=("Arial", 14), 
                    fg=theme["text"], bg=theme["surface"]).pack(side=tk.LEFT, padx=12, fill=tk.X, expand=True)
            
            # Стрелка
            tk.Label(item_content, text="›", font=("Arial", 20), 
                    fg=theme["secondary"], bg=theme["surface"]).pack(side=tk.RIGHT)
            
            # Делаем кликабельным
            def bind_command(widget, cmd):
                widget.bind("<Button-1>", lambda e: cmd())
            
            for widget in [item_frame, item_content] + item_content.winfo_children():
                bind_command(widget, command)
                widget.config(cursor="hand2")
        
        # Кнопка выхода
        logout_frame = tk.Frame(scrollable_frame, bg=theme["bg"])
        logout_frame.pack(fill=tk.X, padx=20, pady=(20, 40))
        
        logout_btn = tk.Button(logout_frame, text="🚪 Выйти из аккаунта", 
                              font=("Arial", 14, "bold"),
                              bg="#DC3545", fg="#000000",  # Красный
                              relief="flat", bd=0,
                              command=self.handle_logout,
                              padx=0, pady=12)
        logout_btn.pack(fill=tk.X)


    
    def show_quick_analysis(self):
        analysis_window = tk.Toplevel(self.root)
        analysis_window.title("Быстрый анализ")
        analysis_window.geometry("350x400")
        analysis_window.configure(bg=self.DARK_THEME["bg"])
        analysis_window.resizable(False, False)
        x = self.root.winfo_x() + 25
        y = self.root.winfo_y() + 200
        analysis_window.geometry(f"350x400+{x}+{y}")
        header_frame = tk.Frame(analysis_window, bg=self.DARK_THEME["accent"], 
                                height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        tk.Label(header_frame, text="⚡ Быстрый анализ", 
                font=("Arial", 16, "bold"), fg="#000000", 
                bg=self.DARK_THEME["accent"]).pack(pady=25)
        content_frame = tk.Frame(analysis_window, bg=self.DARK_THEME["bg"], 
                                padx=24, pady=24)
        content_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(content_frame, text="Сумма покупки (₽):", 
                font=("Arial", 12), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 8))
        price_entry = tk.Entry(content_frame, font=("Arial", 14), 
                              bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"], 
                              relief=tk.FLAT, bd=0, highlightthickness=1,
                              highlightbackground=self.DARK_THEME["divider"],
                              highlightcolor=self.DARK_THEME["accent"])
        price_entry.pack(fill=tk.X, pady=(0, 20), ipady=10)
        tk.Label(content_frame, text="Категория:", 
                font=("Arial", 12), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 8))
        category_var = tk.StringVar()
        category_combo = ttk.Combobox(content_frame, textvariable=category_var,
                                     font=("Arial", 14), state="readonly")
        category_combo['values'] = [
            "Электроника", "Одежда и обувь", "Бытовая техника", "Автомобиль",
            "Путешествия", "Образование", "Здоровье и спорт", "Дом и ремонт",
            "Хобби и развлечения", "Еда и напитки", "Красота и здоровье",
            "Другое"
        ]
        category_combo.pack(fill=tk.X, pady=(0, 30), ipady=10)
        def analyze_quick():
            try:
                price = float(price_entry.get())
                category = category_var.get()
                if price <= 0:
                    messagebox.showerror("Ошибка", "Цена должна быть положительной")
                    return
                if not category:
                    messagebox.showerror("Ошибка", "Выберите категорию")
                    return
                user_data = self.auth_system.get_user_data(self.current_user)
                profile = user_data.get("personal_profile", {})
                monthly_income = profile.get("monthly_income", 30000)
                cooling_result = self.cooling_manager.calculate_cooling_period(price, category, "")
                result_text = f"Анализ покупки за {price:,} ₽\n\n".replace(",", " ")
                if price > monthly_income * 0.3:
                    result_text += "⚠️ Внимание: покупка составляет более 30% вашего месячного дохода!\n\n"
                if cooling_result.get("recommended", True):
                    total_days = cooling_result.get("total_days", 0)
                    if total_days > 0:
                        result_text += f"✅ Рекомендуется период охлаждения: {total_days} дней\n\n"
                        if "cooling_until" in cooling_result:
                            try:
                                cooling_until = datetime.strptime(cooling_result["cooling_until"], "%Y-%m-%d %H:%M:%S")
                                result_text += f"📅 Можно купить после: {cooling_until.strftime('%d.%m.%Y')}\n\n"
                            except:
                                pass
                        daily_savings = price / total_days if total_days > 0 else 0
                        result_text += f"💡 Чтобы накопить за этот период, откладывайте примерно {daily_savings:.0f} ₽ в день"
                    else:
                        result_text += "✅ Можно покупать сразу"
                else:
                    result_text += "❌ Рекомендуется отказаться от этой покупки\n\n"
                    result_text += "💡 Рассмотрите более дешевые альтернативы или подождите лучшего времени"
                messagebox.showinfo("Результат анализа", result_text)
                analysis_window.destroy()
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректную сумму")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при анализе: {str(e)}")
        analyze_btn = tk.Button(content_frame, text="🔍 Проанализировать", 
                               font=("Arial", 14, "bold"),
                               bg=self.DARK_THEME["accent"], fg="#000000",
                               relief=tk.FLAT, bd=0,
                               command=analyze_quick,
                               padx=0, pady=12)
        analyze_btn.pack(fill=tk.X)
    
    def show_statistics_screen(self):
        user_data = self.auth_system.get_user_data(self.current_user)
        purchases = user_data.get("purchases", [])
        if not purchases:
            messagebox.showinfo("Статистика", "У вас пока нет покупок для анализа")
            return
        total_purchases = len(purchases)
        cooling_purchases = len([p for p in purchases if p.get("status") == "cooling"])
        purchased_items = len([p for p in purchases if p.get("status") == "purchased"])
        total_value = sum(p.get("price", 0) for p in purchases)
        stats_window = tk.Toplevel(self.root)
        stats_window.title("Статистика")
        stats_window.geometry("350x400")
        stats_window.configure(bg=self.DARK_THEME["bg"])
        x = self.root.winfo_x() + 25
        y = self.root.winfo_y() + 200
        stats_window.geometry(f"350x400+{x}+{y}")
        header = tk.Frame(stats_window, bg=self.DARK_THEME["accent"], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="📊 Статистика", 
                font=("Arial", 16, "bold"), fg="#000000", 
                bg=self.DARK_THEME["accent"]).pack(pady=25)
        content = tk.Frame(stats_window, bg=self.DARK_THEME["bg"], 
                          padx=16, pady=16)
        content.pack(fill=tk.BOTH, expand=True)
        stats_items = [
            ("Всего покупок:", f"{total_purchases}"),
            ("На охлаждении:", f"{cooling_purchases}"),
            ("Куплено:", f"{purchased_items}"),
            ("Общая сумма:", f"{total_value:,} ₽".replace(",", " "))
        ]
        for label, value in stats_items:
            row = tk.Frame(content, bg=self.DARK_THEME["bg"])
            row.pack(fill=tk.X, pady=12)
            tk.Label(row, text=label, font=("Arial", 12), 
                    fg=self.DARK_THEME["text"], bg=self.DARK_THEME["bg"]).pack(side=tk.LEFT)
            tk.Label(row, text=value, font=("Arial", 12, "bold"), 
                    fg=self.DARK_THEME["accent"], bg=self.DARK_THEME["bg"]).pack(side=tk.RIGHT)
        close_btn = tk.Button(stats_window, text="Закрыть", 
                             font=("Arial", 12, "bold"),
                             bg=self.DARK_THEME["accent"], fg="#000000",
                             relief=tk.FLAT, bd=0,
                             command=stats_window.destroy,
                             padx=0, pady=10)
        close_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=16)
    
    def show_personal_profile_setup(self):
        user_data = self.auth_system.get_user_data(self.current_user)
        profile = user_data.get("personal_profile", {})
        profile_window = tk.Toplevel(self.root)
        profile_window.title("Финансовый профиль")
        profile_window.geometry("350x450")
        profile_window.configure(bg=self.DARK_THEME["bg"])
        x = self.root.winfo_x() + 25
        y = self.root.winfo_y() + 175
        profile_window.geometry(f"350x450+{x}+{y}")
        header = tk.Frame(profile_window, bg=self.DARK_THEME["accent"], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="💰 Финансовый профиль", 
                font=("Arial", 16, "bold"), fg="#000000", 
                bg=self.DARK_THEME["accent"]).pack(pady=25)
        content = tk.Frame(profile_window, bg=self.DARK_THEME["bg"], 
                          padx=16, pady=16)
        content.pack(fill=tk.BOTH, expand=True)
        input_frame = tk.Frame(content, bg=self.DARK_THEME["bg"])
        input_frame.pack(fill=tk.X, pady=(0, 20))
        tk.Label(input_frame, text="Месячный доход (₽)", 
                font=("Arial", 11), fg=self.DARK_THEME["secondary"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 5))
        income_entry = tk.Entry(input_frame, font=("Arial", 14), 
                               bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"], 
                               relief=tk.FLAT, bd=0, highlightthickness=1,
                               highlightbackground=self.DARK_THEME["divider"],
                               highlightcolor=self.DARK_THEME["accent"])
        income_entry.insert(0, str(profile.get("monthly_income", 0)))
        income_entry.pack(fill=tk.X, pady=(0, 15), ipady=10)
        tk.Label(input_frame, text="Откладываю в месяц (₽)", 
                font=("Arial", 11), fg=self.DARK_THEME["secondary"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 5))
        savings_entry = tk.Entry(input_frame, font=("Arial", 14), 
                                bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"], 
                                relief=tk.FLAT, bd=0, highlightthickness=1,
                                highlightbackground=self.DARK_THEME["divider"],
                                highlightcolor=self.DARK_THEME["accent"])
        savings_entry.insert(0, str(profile.get("savings_per_month", 0)))
        savings_entry.pack(fill=tk.X, pady=(0, 15), ipady=10)
        tk.Label(input_frame, text="Текущие накопления (₽)", 
                font=("Arial", 11), fg=self.DARK_THEME["secondary"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 5))
        current_savings_entry = tk.Entry(input_frame, font=("Arial", 14), 
                                        bg=self.DARK_THEME["surface"], fg=self.DARK_THEME["text"], 
                                        relief=tk.FLAT, bd=0, highlightthickness=1,
                                        highlightbackground=self.DARK_THEME["divider"],
                                        highlightcolor=self.DARK_THEME["accent"])
        current_savings_entry.insert(0, str(profile.get("current_savings", 0)))
        current_savings_entry.pack(fill=tk.X, pady=(0, 15), ipady=10)
        def save_profile():
            try:
                monthly_income = float(income_entry.get())
                savings_per_month = float(savings_entry.get())
                current_savings = float(current_savings_entry.get())
                if monthly_income < 0 or savings_per_month < 0 or current_savings < 0:
                    messagebox.showerror("Ошибка", "Значения не могут быть отрицательными")
                    return
                user_data = {
                    "personal_profile": {
                        "monthly_income": monthly_income,
                        "savings_per_month": savings_per_month,
                        "current_savings": current_savings
                    }
                }
                if self.auth_system.update_user_data(self.current_user, user_data):
                    messagebox.showinfo("Успех", "Профиль сохранен")
                    profile_window.destroy()
                else:
                    messagebox.showerror("Ошибка", "Ошибка сохранения")
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректные числа")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка: {str(e)}")
        save_btn = tk.Button(content, text="💾 Сохранить", 
                            font=("Arial", 14, "bold"),
                            bg=self.DARK_THEME["accent"], fg="#000000",
                            relief=tk.FLAT, bd=0,
                            command=save_profile,
                            padx=0, pady=12)
        save_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
    
    def show_forbidden_categories(self):
        user_data = self.auth_system.get_user_data(self.current_user)
        forbidden_categories = user_data.get("forbidden_categories", [])
        categories_window = tk.Toplevel(self.root)
        categories_window.title("Запрещенные категории")
        categories_window.geometry("350x500")
        categories_window.configure(bg=self.DARK_THEME["bg"])
        x = self.root.winfo_x() + 25
        y = self.root.winfo_y() + 150
        categories_window.geometry(f"350x500+{x}+{y}")
        header = tk.Frame(categories_window, bg=self.DARK_THEME["accent"], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🚫 Запрещенные категории", 
                font=("Arial", 16, "bold"), fg="#000000", 
                bg=self.DARK_THEME["accent"]).pack(pady=25)
        content = tk.Frame(categories_window, bg=self.DARK_THEME["bg"])
        content.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        categories = [
            "Электроника", "Одежда и обувь", "Бытовая техника", "Автомобиль",
            "Путешествия", "Образование", "Здоровье и спорт", "Дом и ремонт",
            "Хобби и развлечения", "Еда и напитки", "Красота и здоровье",
            "Дети и товары для детей", "Животные и товары для животных",
            "Цифровые товары", "Услуги", "Азартные игры", "Лотереи",
            "Дорогие рестораны", "Брендовая одежда", "Ювелирные изделия"
        ]
        category_vars = {}
        for category in categories:
            var = tk.BooleanVar(value=category in forbidden_categories)
            category_vars[category] = var
            check = tk.Checkbutton(content, text=category, 
                                  variable=var,
                                  font=("Arial", 11), fg=self.DARK_THEME["text"],
                                  bg=self.DARK_THEME["bg"],
                                  selectcolor=self.DARK_THEME["accent"])
            check.pack(anchor=tk.W, pady=5)
        def save_categories():
            new_forbidden = []
            for category, var in category_vars.items():
                if var.get():
                    new_forbidden.append(category)
            user_data = {"forbidden_categories": new_forbidden}
            if self.auth_system.update_user_data(self.current_user, user_data):
                messagebox.showinfo("Успех", f"Сохранено {len(new_forbidden)} запрещенных категорий")
                categories_window.destroy()
            else:
                messagebox.showerror("Ошибка", "Ошибка сохранения")
        save_btn = tk.Button(categories_window, text="💾 Сохранить", 
                            font=("Arial", 14, "bold"),
                            bg=self.DARK_THEME["accent"], fg="#000000",
                            relief=tk.FLAT, bd=0,
                            command=save_categories,
                            padx=0, pady=12)
        save_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=16)
    
    def show_cooling_periods(self):
        user_data = self.auth_system.get_user_data(self.current_user)
        cooling_periods = user_data.get("cooling_periods", [])
        if not cooling_periods:
            cooling_periods = [
                {"min_price": 0, "max_price": 5000, "days": 1},
                {"min_price": 5001, "max_price": 20000, "days": 3},
                {"min_price": 20001, "max_price": 50000, "days": 7},
                {"min_price": 50001, "max_price": 100000, "days": 14},
                {"min_price": 100001, "max_price": 200000, "days": 30},
                {"min_price": 200001, "max_price": 500000, "days": 60},
                {"min_price": 500001, "max_price": 1000000, "days": 90}
            ]
        
        periods_window = tk.Toplevel(self.root)
        periods_window.title("Диапазоны охлаждения")
        periods_window.geometry("400x875")
        periods_window.configure(bg=self.DARK_THEME["bg"])
        
        x = self.root.winfo_x() + 25
        y = self.root.winfo_y() + 150
        periods_window.geometry(f"400x875+{x}+{y}")
        
        header = tk.Frame(periods_window, bg=self.DARK_THEME["accent"], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text="⏱️ Диапазоны охлаждения", 
                font=("Arial", 16, "bold"), fg="#000000", 
                bg=self.DARK_THEME["accent"]).pack(pady=25)
        
        canvas = tk.Canvas(periods_window, bg=self.DARK_THEME["bg"], 
                        highlightthickness=0)
        scrollbar = ttk.Scrollbar(periods_window, orient="vertical", 
                                command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.DARK_THEME["bg"])
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        content = tk.Frame(scrollable_frame, bg=self.DARK_THEME["bg"])
        content.pack(fill=tk.BOTH, expand=True, padx=16, pady=16)
        
        # Кнопка сохранения вверху (внутри content, но перед настройками)
        save_btn = tk.Button(content, text="💾 Сохранить настройки", 
                            font=("Arial", 14, "bold"),
                            bg=self.DARK_THEME["accent"], fg="#000000",
                            relief=tk.FLAT, bd=0,
                            padx=0, pady=12)
        save_btn.pack(side=tk.TOP, fill=tk.X, pady=(0, 20))
        
        tk.Label(content, text="Настройте периоды охлаждения:", 
                font=("Arial", 12, "bold"), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 12))
        
        entries = []
        for i, period in enumerate(cooling_periods):
            period_frame = tk.Frame(content, bg=self.DARK_THEME["surface"], 
                                relief=tk.FLAT)
            period_frame.pack(fill=tk.X, pady=(0, 8))
            
            tk.Label(period_frame, text=f"Диапазон {i+1}:", 
                    font=("Arial", 11), fg=self.DARK_THEME["text"], 
                    bg=self.DARK_THEME["surface"]).pack(anchor=tk.W, padx=12, pady=(8, 4))
            
            min_frame = tk.Frame(period_frame, bg=self.DARK_THEME["surface"])
            min_frame.pack(fill=tk.X, padx=12, pady=(0, 4))
            tk.Label(min_frame, text="От:", font=("Arial", 10), 
                    fg=self.DARK_THEME["secondary"], bg=self.DARK_THEME["surface"]).pack(side=tk.LEFT)
            min_entry = tk.Entry(min_frame, font=("Arial", 11), 
                                bg=self.DARK_THEME["bg"], fg=self.DARK_THEME["text"], 
                                relief=tk.FLAT, bd=0, highlightthickness=1,
                                highlightbackground=self.DARK_THEME["divider"],
                                highlightcolor=self.DARK_THEME["accent"], width=10)
            min_entry.insert(0, str(period["min_price"]))
            min_entry.pack(side=tk.LEFT, padx=5, ipady=4)
            tk.Label(min_frame, text="₽", font=("Arial", 10), 
                    fg=self.DARK_THEME["secondary"], bg=self.DARK_THEME["surface"]).pack(side=tk.LEFT, padx=5)
            
            max_frame = tk.Frame(period_frame, bg=self.DARK_THEME["surface"])
            max_frame.pack(fill=tk.X, padx=12, pady=(0, 4))
            tk.Label(max_frame, text="До:", font=("Arial", 10), 
                    fg=self.DARK_THEME["secondary"], bg=self.DARK_THEME["surface"]).pack(side=tk.LEFT)
            max_entry = tk.Entry(max_frame, font=("Arial", 11), 
                                bg=self.DARK_THEME["bg"], fg=self.DARK_THEME["text"], 
                                relief=tk.FLAT, bd=0, highlightthickness=1,
                                highlightbackground=self.DARK_THEME["divider"],
                                highlightcolor=self.DARK_THEME["accent"], width=10)
            max_entry.insert(0, str(period["max_price"]))
            max_entry.pack(side=tk.LEFT, padx=5, ipady=4)
            tk.Label(max_frame, text="₽", font=("Arial", 10), 
                    fg=self.DARK_THEME["secondary"], bg=self.DARK_THEME["surface"]).pack(side=tk.LEFT, padx=5)
            
            days_frame = tk.Frame(period_frame, bg=self.DARK_THEME["surface"])
            days_frame.pack(fill=tk.X, padx=12, pady=(0, 8))
            tk.Label(days_frame, text="Дней охлаждения:", font=("Arial", 10), 
                    fg=self.DARK_THEME["secondary"], bg=self.DARK_THEME["surface"]).pack(side=tk.LEFT)
            days_entry = tk.Entry(days_frame, font=("Arial", 11), 
                                bg=self.DARK_THEME["bg"], fg=self.DARK_THEME["text"], 
                                relief=tk.FLAT, bd=0, highlightthickness=1,
                                highlightbackground=self.DARK_THEME["divider"],
                                highlightcolor=self.DARK_THEME["accent"], width=8)
            days_entry.insert(0, str(period["days"]))
            days_entry.pack(side=tk.LEFT, padx=5, ipady=4)
            
            entries.append((min_entry, max_entry, days_entry))
    
    def save_periods():
        new_periods = []
        for min_entry, max_entry, days_entry in entries:
            try:
                min_price = int(min_entry.get())
                max_price = int(max_entry.get())
                days = int(days_entry.get())
                if min_price < 0 or max_price < 0 or days < 0:
                    messagebox.showerror("Ошибка", "Значения не могут быть отрицательными")
                    return
                if min_price > max_price:
                    messagebox.showerror("Ошибка", "Минимальная цена не может быть больше максимальной")
                    return
                new_periods.append({
                    "min_price": min_price,
                    "max_price": max_price,
                    "days": days
                })
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректные числа")
                return
        
        new_periods.sort(key=lambda x: x["min_price"])
        user_data = {"cooling_periods": new_periods}
        if self.auth_system.update_user_data(self.current_user, user_data):
            messagebox.showinfo("Успех", f"Сохранено {len(new_periods)} диапазонов")
            periods_window.destroy()
        else:
            messagebox.showerror("Ошибка", "Ошибка сохранения")
    
        # Теперь устанавливаем команду для кнопки после определения функции
        save_btn.configure(command=save_periods)
    
    def show_notification_settings(self):
        user_data = self.auth_system.get_user_data(self.current_user)
        notification_settings = user_data.get("notification_settings", {})
        notify_window = tk.Toplevel(self.root)
        notify_window.title("Настройки уведомлений")
        notify_window.geometry("350x500")
        notify_window.configure(bg=self.DARK_THEME["bg"])
        x = self.root.winfo_x() + 25
        y = self.root.winfo_y() + 200
        notify_window.geometry(f"350x500+{x}+{y}")
        header = tk.Frame(notify_window, bg=self.DARK_THEME["accent"], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="🔔 Настройки уведомлений", 
                font=("Arial", 16, "bold"), fg="#000000", 
                bg=self.DARK_THEME["accent"]).pack(pady=25)
        content = tk.Frame(notify_window, bg=self.DARK_THEME["bg"], 
                          padx=16, pady=16)
        content.pack(fill=tk.BOTH, expand=True)
        enabled_var = tk.BooleanVar(value=notification_settings.get("enabled", True))
        enabled_check = tk.Checkbutton(content, text="Включить уведомления", 
                                      variable=enabled_var,
                                      font=("Arial", 12), fg=self.DARK_THEME["text"],
                                      bg=self.DARK_THEME["bg"],
                                      selectcolor=self.DARK_THEME["accent"])
        enabled_check.pack(anchor=tk.W, pady=(0, 20))
        tk.Label(content, text="Частота напоминаний:", 
                font=("Arial", 12), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 8))
        frequency_var = tk.StringVar(value=str(notification_settings.get("frequency_days", 7)))
        frequency_frame = tk.Frame(content, bg=self.DARK_THEME["bg"])
        frequency_frame.pack(fill=tk.X, pady=(0, 20))
        frequencies = [("1 день", "1"), ("3 дня", "3"), ("7 дней", "7"), ("14 дней", "14"), ("30 дней", "30")]
        for text, value in frequencies:
            tk.Radiobutton(frequency_frame, text=text, 
                          variable=frequency_var, value=value,
                          font=("Arial", 11), fg=self.DARK_THEME["text"],
                          bg=self.DARK_THEME["bg"],
                          selectcolor=self.DARK_THEME["accent"]).pack(side=tk.LEFT, padx=2)
        tk.Label(content, text="Канал уведомлений:", 
                font=("Arial", 12), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 8))
        channel_var = tk.StringVar(value=notification_settings.get("channel", "in_app"))
        channel_frame = tk.Frame(content, bg=self.DARK_THEME["bg"])
        channel_frame.pack(fill=tk.X, pady=(0, 20))
        channels = [("В приложении", "in_app")]
        for text, value in channels:
            tk.Radiobutton(channel_frame, text=text, 
                          variable=channel_var, value=value,
                          font=("Arial", 11), fg=self.DARK_THEME["text"],
                          bg=self.DARK_THEME["bg"],
                          selectcolor=self.DARK_THEME["accent"]).pack(side=tk.LEFT, padx=2)
        def save_notifications():
            try:
                frequency_days = int(frequency_var.get())
                if frequency_days <= 0:
                    messagebox.showerror("Ошибка", "Частота должна быть положительным числом")
                    return
            except ValueError:
                messagebox.showerror("Ошибка", "Введите корректную частоту")
                return
            new_settings = {
                "notification_settings": {
                    "enabled": enabled_var.get(),
                    "frequency_days": frequency_days,
                    "excluded_items": notification_settings.get("excluded_items", []),
                    "channel": channel_var.get()
                }
            }
            if self.auth_system.update_user_data(self.current_user, new_settings):
                messagebox.showinfo("Успех", "Настройки сохранены")
                notify_window.destroy()
            else:
                messagebox.showerror("Ошибка", "Ошибка сохранения")
        save_btn = tk.Button(content, text="💾 Сохранить", 
                            font=("Arial", 14, "bold"),
                            bg=self.DARK_THEME["accent"], fg="#000000",
                            relief=tk.FLAT, bd=0,
                            command=save_notifications,
                            padx=0, pady=12)
        save_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
    
    def show_app_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Настройки приложения")
        settings_window.geometry("350x400")
        settings_window.configure(bg=self.DARK_THEME["bg"])
        x = self.root.winfo_x() + 25
        y = self.root.winfo_y() + 200
        settings_window.geometry(f"350x400+{x}+{y}")
        header = tk.Frame(settings_window, bg=self.DARK_THEME["accent"], height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        tk.Label(header, text="⚙️ Настройки приложения", 
                font=("Arial", 16, "bold"), fg="#000000", 
                bg=self.DARK_THEME["accent"]).pack(pady=25)
        content = tk.Frame(settings_window, bg=self.DARK_THEME["bg"], 
                          padx=16, pady=16)
        content.pack(fill=tk.BOTH, expand=True)
        tk.Label(content, text="Общие настройки:", 
                font=("Arial", 14, "bold"), fg=self.DARK_THEME["text"], 
                bg=self.DARK_THEME["bg"]).pack(anchor=tk.W, pady=(0, 12))
        dark_mode_var = tk.BooleanVar(value=False)
        dark_mode_check = tk.Checkbutton(content, text="Темная тема", 
                                        variable=dark_mode_var,
                                        font=("Arial", 12), fg=self.DARK_THEME["text"],
                                        bg=self.DARK_THEME["bg"],
                                        selectcolor=self.DARK_THEME["accent"])
        dark_mode_check.pack(anchor=tk.W, pady=(0, 15))
        auto_scanner_var = tk.BooleanVar(value=False)
        auto_scanner_check = tk.Checkbutton(content, text="Автозапуск сканера", 
                                           variable=auto_scanner_var,
                                           font=("Arial", 12), fg=self.DARK_THEME["text"],
                                           bg=self.DARK_THEME["bg"],
                                        selectcolor=self.DARK_THEME["accent"])
        auto_scanner_check.pack(anchor=tk.W, pady=(0, 15))
        sound_var = tk.BooleanVar(value=True)
        sound_check = tk.Checkbutton(content, text="Звуковые уведомления", 
                                    variable=sound_var,
                                    font=("Arial", 12), fg=self.DARK_THEME["text"],
                                    bg=self.DARK_THEME["bg"],
                                    selectcolor=self.DARK_THEME["accent"])
        sound_check.pack(anchor=tk.W, pady=(0, 15))
        def save_app_settings():
            messagebox.showinfo("Сохранено", "Настройки приложения сохранены")
            settings_window.destroy()
        save_btn = tk.Button(content, text="💾 Сохранить настройки", 
                            font=("Arial", 14, "bold"),
                            bg=self.DARK_THEME["accent"], fg="#000000",
                            relief=tk.FLAT, bd=0,
                            command=save_app_settings,
                            padx=0, pady=12)
        save_btn.pack(side=tk.BOTTOM, fill=tk.X, pady=(20, 0))
    
    def check_notifications(self):
        try:
            notifications = self.notification_manager.check_pending_notifications(self.current_user)
            if not notifications:
                messagebox.showinfo("Уведомления", "Нет новых уведомлений")
            else:
                messagebox.showinfo("Уведомления", f"У вас {len(notifications)} новых уведомлений\n\nTelegram @ai_t_assitant_bot")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка проверки уведомлений: {str(e)}")
    
    def handle_logout(self):
        # Удаляем нижнее меню навигации, если оно существует
        if hasattr(self, "navigation_frame") and self.navigation_frame:
            self.navigation_frame.destroy()
            self.navigation_frame = None

        # Сбрасываем текущего пользователя
        self.current_user = None

        # Возвращаемся на экран логина
        self.show_login_screen()



    def mark_as_purchased(self, purchase_id):
        """Помечает покупку как купленную (ручное нажатие кнопки)"""
        try:
            # Получаем текущие данные покупки
            purchase = self.auth_system.get_purchase(self.current_user, purchase_id)
            if not purchase:
                messagebox.showerror("Ошибка", "Покупка не найдена")
                return False
            
            # Проверяем, есть ли уже накопления
            current_savings = purchase.get("current_savings", 0)
            price = purchase.get("price", 0)
            
            # Если накоплений нет, спрашиваем подтверждение
            if current_savings < price:
                response = messagebox.askyesno(
                    "Подтверждение", 
                    f"Вы накопили только {current_savings:,} ₽ из {price:,} ₽. Вы уверены, что хотите отметить покупку как купленную?".replace(",", " ")
                )
                if not response:
                    return False
            
            # Используем метод mark_purchase_as_purchased
            if self.auth_system.mark_purchase_as_purchased(self.current_user, purchase_id):
                messagebox.showinfo("Успех", "Покупка отмечена как совершенная")
                self.show_purchases_screen()
                return True
            else:
                messagebox.showerror("Ошибка", "Не удалось отметить покупку")
                return False
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {str(e)}")
            return False
    
    def set_filter_and_update(self, filter_name):
        """Устанавливает фильтр и обновляет список покупок"""
        if hasattr(self, 'purchase_filter_var'):
            self.purchase_filter_var.set(filter_name)
        # Вызываем существующий метод фильтрации
        self.filter_purchases()

    def start_scanner(self):
        if not self.scanner_running:
            self.scanner_running = True
            self.scanner_thread = threading.Thread(
                target=start_scanner,
                args=(self.trigger_queue, lambda: self.scanner_running),
                daemon=True
            )
            self.scanner_thread.start()
            
            # Обновляем статус если метка существует
            if hasattr(self, 'current_scanner_status_label') and self.current_scanner_status_label:
                self.current_scanner_status_label.config(
                    text="Сканер активен ✓", 
                    fg=self.DARK_THEME["success"]
                )
            
            messagebox.showinfo("Сканер", "Сканер запущен")

    def stop_scanner(self):
        self.scanner_running = False
        
        # Обновляем статус если метка существует
        if hasattr(self, 'current_scanner_status_label') and self.current_scanner_status_label:
            self.current_scanner_status_label.config(
                text="Сканер остановлен", 
                fg=self.DARK_THEME["error"]
            )

    
    def logout(self):
        self.current_user = None
        self.stop_scanner()
        # self.show_auth_screen() old
        self.show_login_screen()

    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = MainApplication()
    app.run()