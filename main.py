import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import psutil
import os
import sys
import json
import threading
import time
import pystray
from PIL import Image, ImageDraw
import winshell
from win32com.client import Dispatch
from datetime import datetime
import uuid
import shutil
import winreg


def find_system_python():
    """
    Находит системный интерпретатор Python в следующих местах:
    1. В переменной PATH
    2. В реестре Windows (установленные версии Python)
    3. Стандартные пути установки
    """
    # 1. Поиск в PATH
    # python_path = shutil.which("python")
    # if python_path and os.path.exists(python_path):
    #     return python_path

    # 2. Поиск в реестре Windows
    try:
        # Пытаемся найти в реестре установленные версии Python
        registry_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Python\PythonCore"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Python\PythonCore"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Wow6432Node\Python\PythonCore")
        ]

        for hive, path in registry_paths:
            try:
                with winreg.OpenKey(hive, path) as key:
                    # Получаем список установленных версий
                    i = 0
                    while True:
                        try:
                            version = winreg.EnumKey(key, i)
                            try:
                                with winreg.OpenKey(hive, f"{path}\\{version}\\InstallPath") as install_key:
                                    install_path, _ = winreg.QueryValueEx(install_key, "")
                                    python_exe = os.path.join(install_path, "python.exe")
                                    if os.path.exists(python_exe):
                                        return python_exe
                            except:
                                pass
                            i += 1
                        except WindowsError:
                            break
            except:
                pass
    except:
        pass

    # 3. Стандартные пути установки
    standard_paths = [
        r"C:\Python*\python.exe",
        r"C:\Program Files\Python*\python.exe",
        r"C:\Users\{}\AppData\Local\Programs\Python\Python*\python.exe".format(os.getenv('USERNAME')),
    ]

    for path in standard_paths:
        if os.path.exists(path):
            return path

    # 4. Если ничего не найдено, возвращаем текущий интерпретатор
    return sys.executable

# Определяем базовый путь для работы с файлами в EXE
def get_base_path():
    if getattr(sys, 'frozen', False):
        # Если программа запущена как EXE
        return os.path.dirname(sys.executable)
    else:
        # Если программа запущена как скрипт
        return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

# Настройки тем
THEMES = {
    "light": {
        "bg": "#ffffff",
        "fg": "#000000",
        "frame_bg": "#f0f0f0",
        "button_bg": "#e0e0e0",
        "button_fg": "#000000",
        "listbox_bg": "#ffffff",
        "listbox_fg": "#000000",
        "progress_bg": "#e0e0e0",
        "progress_fg": "#0078d7",
        "label_bg": "#f0f0f0",
        "label_fg": "#000000",
        "console_bg": "#000000",
        "console_fg": "#00ff00",
        "tree_bg": "#ffffff",
        "tree_fg": "#000000"
    },
    "dark": {
        "bg": "#2d2d30",
        "fg": "#ffffff",
        "frame_bg": "#3e3e42",
        "button_bg": "#007acc",
        "button_fg": "#ffffff",
        "listbox_bg": "#1e1e1e",
        "listbox_fg": "#d4d4d4",
        "progress_bg": "#3e3e42",
        "progress_fg": "#007acc",
        "label_bg": "#3e3e42",
        "label_fg": "#ffffff",
        "console_bg": "#0c0c0c",
        "console_fg": "#00ff00",
        "tree_bg": "#1e1e1e",
        "tree_fg": "#d4d4d4"
    }
}


class ConsoleDialog(tk.Toplevel):
    def __init__(self, parent, script_name, process, theme="light"):
        super().__init__(parent)
        self.theme = theme
        self.colors = THEMES.get(theme, THEMES["light"])
        self.script_name = script_name
        self.process = process

        self.title(f"Консоль: {script_name}")
        self.geometry("800x600")
        self.resizable(True, True)

        self.setup_ui()

    def setup_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Output area
        output_frame = ttk.LabelFrame(main_frame, text="Вывод консоли", padding=5)
        output_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Text widget for console output - make it read-only
        self.output_text = tk.Text(
            output_frame,
            wrap=tk.WORD,
            bg=self.colors["console_bg"],
            fg=self.colors["console_fg"],
            font=("Consolas", 10),
            insertbackground=self.colors["console_fg"],
            state=tk.DISABLED
        )

        output_scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output_text.yview)
        self.output_text.configure(yscrollcommand=output_scrollbar.set)

        self.output_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        output_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Input area
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="Ввод:").pack(side=tk.LEFT, padx=(0, 5))

        self.input_entry = ttk.Entry(input_frame)
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        self.input_entry.bind('<Return>', self.send_input)

        ttk.Button(input_frame, text="Отправить", command=self.send_input).pack(side=tk.RIGHT)

        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)

        ttk.Button(buttons_frame, text="Очистить вывод",
                   command=self.clear_output).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="Закрыть",
                   command=self.destroy).pack(side=tk.RIGHT)

    def clear_output(self):
        self.output_text.config(state=tk.NORMAL)
        self.output_text.delete(1.0, tk.END)
        self.output_text.config(state=tk.DISABLED)

    def send_input(self, event=None):
        input_text = self.input_entry.get()
        if input_text and self.process and self.process.poll() is None:
            try:
                # Кодируем ввод в UTF-8 перед отправкой
                encoded_input = (input_text + '\n').encode('utf-8')
                self.process.stdin.write(encoded_input)
                self.process.stdin.flush()

                # Показываем введенную команду в выводе
                self.append_text(f"> {input_text}\n")

                # Очищаем поле ввода
                self.input_entry.delete(0, tk.END)
            except Exception as e:
                self.append_text(f"Ошибка ввода: {str(e)}\n")

    def append_text(self, text):
        """Безопасное добавление текста в текстовое поле"""
        self.output_text.config(state=tk.NORMAL)
        self.output_text.insert(tk.END, text)
        self.output_text.see(tk.END)
        self.output_text.config(state=tk.DISABLED)

    def load_historical_output(self, historical_output):
        """Загружает исторический вывод при открытии консоли"""
        if historical_output:
            self.append_text(historical_output)


class ErrorDialog(tk.Toplevel):
    def __init__(self, parent, script_name, error_message, theme="light"):
        super().__init__(parent)
        self.theme = theme
        self.colors = THEMES.get(theme, THEMES["light"])

        self.title("Ошибка скрипта")
        self.geometry("700x500")
        self.resizable(True, True)
        self.transient(parent)
        # УБРАНО: self.grab_set()
        # УБРАНО: self.attributes('-topmost', True)

        self.script_name = script_name
        self.error_message = error_message

        self.apply_theme()
        self.init_ui()

    def apply_theme(self):
        self.configure(bg=self.colors["bg"])

    def init_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Script info
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(info_frame, text="Скрипт:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(info_frame, text=self.script_name, font=('Arial', 10)).pack(anchor=tk.W, pady=(2, 0))

        # Time info
        time_frame = ttk.Frame(main_frame)
        time_frame.pack(fill=tk.X, pady=(0, 10))

        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ttk.Label(time_frame, text="Время ошибки:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        ttk.Label(time_frame, text=current_time, font=('Arial', 10)).pack(anchor=tk.W, pady=(2, 0))

        # Error message
        ttk.Label(main_frame, text="Текст ошибки:", font=('Arial', 10, 'bold')).pack(anchor=tk.W)

        error_frame = ttk.Frame(main_frame)
        error_frame.pack(fill=tk.BOTH, expand=True, pady=(5, 10))

        # Text widget with scrollbar for error message
        self.error_text = tk.Text(error_frame, wrap=tk.WORD, width=80, height=15)
        scrollbar = ttk.Scrollbar(error_frame, orient=tk.VERTICAL, command=self.error_text.yview)
        self.error_text.configure(yscrollcommand=scrollbar.set)

        self.error_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.error_text.insert(tk.END, self.error_message)
        self.error_text.config(state=tk.DISABLED)

        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(buttons_frame, text="Копировать ошибку",
                   command=self.copy_error).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(buttons_frame, text="Закрыть",
                   command=self.destroy).pack(side=tk.RIGHT)

    def copy_error(self):
        """Копирует текст ошибки в буфер обмена"""
        self.clipboard_clear()
        self.clipboard_append(self.error_message)
        messagebox.showinfo("Успех", "Ошибка скопирована в буфер обмена")


class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, settings):
        super().__init__(parent)
        self.settings = settings
        self.parent = parent
        self.title("Настройки Python Script Manager (PSM)")
        self.geometry("500x450")  # Увеличиваем высоту для новой настройки
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.attributes('-topmost', True)

        self.result = None
        self.init_ui()

    def init_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Autostart setting
        autostart_frame = ttk.LabelFrame(main_frame, text="Настройки приложения", padding=10)
        autostart_frame.pack(fill=tk.X, pady=(0, 10))

        self.autostart_var = tk.BooleanVar(value=self.settings.get('autostart', False))
        ttk.Checkbutton(autostart_frame, text="Запускать Python Script Manager (PSM) при старте системы",
                        variable=self.autostart_var,
                        command=self.toggle_autostart).pack(anchor=tk.W)

        # НОВАЯ НАСТРОЙКА: Мониторинг производительности
        self.monitoring_var = tk.BooleanVar(value=self.settings.get('performance_monitoring', True))
        ttk.Checkbutton(autostart_frame, text="Включить мониторинг производительности",
                        variable=self.monitoring_var).pack(anchor=tk.W, pady=(5, 0))

        # Default interpreter
        interpreter_frame = ttk.LabelFrame(main_frame, text="Интерпретатор по умолчанию", padding=10)
        interpreter_frame.pack(fill=tk.X, pady=(0, 10))

        interpreter_subframe = ttk.Frame(interpreter_frame)
        interpreter_subframe.pack(fill=tk.X)

        self.interpreter_var = tk.StringVar(value=self.settings.get('default_interpreter', sys.executable))
        interpreter_entry = ttk.Entry(interpreter_subframe, textvariable=self.interpreter_var)
        interpreter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        ttk.Button(interpreter_subframe, text="Обзор",
                   command=self.browse_interpreter).pack(side=tk.RIGHT)

        ttk.Button(interpreter_frame, text="Показать установленные пакеты",
                   command=self.show_packages).pack(anchor=tk.W, pady=(5, 0))

        # Buttons frame
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)

        ttk.Button(buttons_frame, text="Сохранить",
                   command=self.save_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(buttons_frame, text="Отмена",
                   command=self.destroy).pack(side=tk.RIGHT)

    def save_settings(self):
        self.settings['autostart'] = self.autostart_var.get()
        self.settings['default_interpreter'] = self.interpreter_var.get()
        # СОХРАНЯЕМ НОВУЮ НАСТРОЙКУ
        self.settings['performance_monitoring'] = self.monitoring_var.get()
        self.destroy()

    def toggle_autostart(self):
        """Включение/выключение автозапуска"""
        try:
            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, "Python Script Manager (PSM).lnk")

            if self.autostart_var.get():
                # Определяем путь к исполняемому файлу
                if getattr(sys, 'frozen', False):
                    # Если программа собрана в .exe
                    target_path = sys.executable
                    working_dir = os.path.dirname(sys.executable)
                    icon_path = sys.executable
                    args = ""
                else:
                    # Если запущен как .py скрипт
                    target_path = sys.executable
                    script_path = os.path.abspath(sys.argv[0])
                    working_dir = os.path.dirname(script_path)
                    args = f'"{script_path}"'
                    icon_path = sys.executable

                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = target_path
                if args and not getattr(sys, 'frozen', False):
                    shortcut.Arguments = args
                shortcut.WorkingDirectory = working_dir
                shortcut.IconLocation = icon_path
                shortcut.save()

                # Сохраняем настройку
                self.settings['autostart'] = True
            else:
                # Удаляем ярлык из автозагрузки
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)

                # Сохраняем настройку
                self.settings['autostart'] = False

            # Сохраняем настройки
            self.parent.save_settings()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось настроить автозапуск: {str(e)}")
            # В случае ошибки сбрасываем переключатель
            self.autostart_var.set(not self.autostart_var.get())

    def browse_interpreter(self):
        path = filedialog.askopenfilename(
            title="Выберите интерпретатор Python",
            filetypes=[("Executable files", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.interpreter_var.set(path)

    def show_packages(self):
        interpreter = self.interpreter_var.get()
        if not os.path.exists(interpreter):
            messagebox.showerror("Ошибка", "Указанный интерпретатор не найден")
            return

        try:
            # Get installed packages
            result = subprocess.run([
                interpreter, "-m", "pip", "list"
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Show packages in a new window
                packages_window = tk.Toplevel(self)
                packages_window.title("Установленные пакеты")
                packages_window.geometry("600x400")
                packages_window.transient(self)
                packages_window.grab_set()
                packages_window.attributes('-topmost', True)

                text_frame = ttk.Frame(packages_window, padding=10)
                text_frame.pack(fill=tk.BOTH, expand=True)

                text_widget = tk.Text(text_frame, wrap=tk.WORD)
                scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
                text_widget.config(yscrollcommand=scrollbar.set)

                text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                text_widget.insert(tk.END, result.stdout)
                text_widget.config(state=tk.DISABLED)
            else:
                messagebox.showerror("Ошибка", f"Не удалось получить список пакетов:\n{result.stderr}")

        except subprocess.TimeoutExpired:
            messagebox.showerror("Ошибка", "Таймаут при получении списка пакетов")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при получении списка пакетов: {str(e)}")

    def save_settings(self):
        self.settings['autostart'] = self.autostart_var.get()
        self.settings['default_interpreter'] = self.interpreter_var.get()
        self.destroy()


class RenameDialog(tk.Toplevel):
    def __init__(self, parent, current_name):
        super().__init__(parent)
        self.parent = parent
        self.current_name = current_name
        self.result = None

        self.title("Переименовать скрипт")
        self.geometry("400x150")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.attributes('-topmost', True)

        self.init_ui()

    def init_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Новое имя скрипта:").pack(anchor=tk.W, pady=(0, 5))

        self.name_var = tk.StringVar(value=self.current_name)
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        name_entry.pack(fill=tk.X, pady=(0, 15))
        name_entry.select_range(0, tk.END)
        name_entry.focus()

        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X)

        ttk.Button(buttons_frame, text="Сохранить",
                   command=self.save_name).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(buttons_frame, text="Отмена",
                   command=self.destroy).pack(side=tk.RIGHT)

    def save_name(self):
        new_name = self.name_var.get().strip()
        if new_name:
            self.result = new_name
            self.destroy()


class ScriptManagerTkinter:
    def __init__(self, root):
        self.root = root
        self.root.title("Python Script Manager (PSM)")
        self.root.geometry("1200x800")

        # Текущая тема
        self.current_theme = "light"

        # Инициализация переменных до setup_ui
        self.active_scripts = []  # UUID скриптов с активными панелями
        self.saved_scripts = {}  # Все сохраненные скрипты по UUID
        self.script_frames = []
        self.scripts_file = os.path.join(BASE_PATH, "scripts.json")
        self.settings_file = os.path.join(BASE_PATH, "settings.json")
        self.settings = {}

        # Для отслеживания ошибок
        self.error_messages = {}  # script_uuid -> error_message

        # Словарь для хранения открытых консолей
        self.open_consoles = {}

        # Словарь для хранения буферов вывода каждого процесса
        self.process_output_buffers = {}

        # Флаг для отслеживания состояния трея
        self.tray_icon = None
        self.tray_thread = None

        # Переопределяем закрытие окна - скрываем в трей
        self.root.protocol('WM_DELETE_WINDOW', self.hide_to_tray)

        self.setup_ui()
        self.load_settings()
        self.load_scripts()
        self.start_monitoring()

        # Настраиваем иконку в трее после создания основного интерфейса
        self.root.after(100, self.setup_tray_icon)

    def apply_theme(self, theme_name):
        """Применяет выбранную тему"""
        self.current_theme = theme_name
        colors = THEMES.get(theme_name, THEMES["light"])

        # Настройка стилей для ttk
        style = ttk.Style()

        if theme_name == "dark":
            style.theme_use('clam')
        else:
            style.theme_use('vista')

        # Настройка цветов для Treeview
        style.configure("Treeview",
                        background=colors["tree_bg"],
                        foreground=colors["tree_fg"],
                        fieldbackground=colors["tree_bg"])

        style.configure("Treeview.Heading",
                        background=colors["button_bg"],
                        foreground=colors["button_fg"])

        # Настройка цветов для других элементов
        style.configure("TFrame", background=colors["frame_bg"])
        style.configure("TLabel", background=colors["label_bg"], foreground=colors["label_fg"])
        style.configure("TButton", background=colors["button_bg"], foreground=colors["button_fg"])
        style.configure("TProgressbar", background=colors["progress_bg"], troughcolor=colors["progress_bg"])
        style.configure("TLabelframe", background=colors["frame_bg"], foreground=colors["fg"])
        style.configure("TLabelframe.Label", background=colors["frame_bg"], foreground=colors["fg"])

        # Стили для кнопок запуска/остановки
        style.configure("Start.TButton", background="#d4edda", foreground="#155724")
        style.configure("Stop.TButton", background="#f8d7da", foreground="#721c24")

        # Применяем цвета к основному окну
        self.root.configure(bg=colors["bg"])

        # Обновляем цвет фона canvas
        if hasattr(self, 'canvas'):
            self.canvas.configure(bg=colors["bg"])

    def setup_ui(self):
        # Main menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ФАЙЛ", menu=file_menu)
        file_menu.add_command(label="Настройки", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Свернуть в трей", command=self.hide_to_tray)
        file_menu.add_command(label="Закрыть", command=self.quit_application)

        # Меню ВИД с выбором темы
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ВИД", menu=view_menu)
        view_menu.add_command(label="Светлая тема", command=lambda: self.change_theme("light"))
        view_menu.add_command(label="Тёмная тема", command=lambda: self.change_theme("dark"))

        # НОВОЕ МЕНЮ: СПРАВКА
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="СПРАВКА", menu=help_menu)
        help_menu.add_command(label="Информация", command=self.show_info)
        help_menu.add_command(label="Репозиторий GitHub", command=self.open_github)

        # System monitoring
        system_frame = ttk.LabelFrame(self.root, text="Общая нагрузка (сумма всех скриптов):", padding=10)
        system_frame.pack(fill="x", padx=10, pady=5)

        self.total_cpu_var = tk.IntVar()
        self.total_memory_var = tk.IntVar()

        ttk.Label(system_frame, text="CPU:").grid(row=0, column=0, sticky="w")
        self.total_cpu_bar = ttk.Progressbar(system_frame, variable=self.total_cpu_var, maximum=100)
        self.total_cpu_bar.grid(row=0, column=1, sticky="ew", padx=5)
        self.total_cpu_label = ttk.Label(system_frame, text="0%")
        self.total_cpu_label.grid(row=0, column=2, padx=5)

        ttk.Label(system_frame, text="Память:").grid(row=1, column=0, sticky="w")
        self.total_memory_bar = ttk.Progressbar(system_frame, variable=self.total_memory_var, maximum=100)
        self.total_memory_bar.grid(row=1, column=1, sticky="ew", padx=5)
        self.total_memory_label = ttk.Label(system_frame, text="0%")
        self.total_memory_label.grid(row=1, column=2, padx=5)

        system_frame.columnconfigure(1, weight=1)

        # Active scripts area
        scripts_label = ttk.Label(self.root, text="Активные скрипты:", font=("Arial", 12, "bold"))
        scripts_label.pack(anchor="w", padx=10, pady=(10, 0))

        # Frame for active scripts with scrollbar - ИЗМЕНЕНО: создаем отдельный фрейм для области с прокруткой
        active_scripts_frame = ttk.Frame(self.root)
        active_scripts_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)

        # Canvas and scrollbar for active script frames - ИЗМЕНЕНО: переносим в active_scripts_frame
        self.canvas = tk.Canvas(active_scripts_frame, bg=THEMES[self.current_theme]["bg"])
        self.scrollbar = ttk.Scrollbar(active_scripts_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Упаковка canvas и scrollbar в active_scripts_frame
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        self.scrollbar.pack(side="right", fill="y")

        # Right panel for saved scripts catalog - УВЕЛИЧЕНА ШИРИНА в 1.3 раза
        right_frame = ttk.Frame(self.root, width=585)  # Было 450, стало 450 * 1.3 = 585
        right_frame.pack(side="right", fill="y", padx=10, pady=5)
        right_frame.pack_propagate(False)

        # Saved scripts catalog
        saved_catalog_frame = ttk.LabelFrame(right_frame, text="КАТАЛОГ СКРИПТОВ", padding=10)
        saved_catalog_frame.pack(fill="both", expand=True)

        # Buttons for saved catalog
        saved_buttons_frame = ttk.Frame(saved_catalog_frame)
        saved_buttons_frame.pack(fill="x", pady=5)

        ttk.Button(saved_buttons_frame, text="Добавить",
                   command=self.add_script).pack(side="left", padx=2)
        ttk.Button(saved_buttons_frame, text="Удалить",
                   command=self.delete_script).pack(side="left", padx=2)
        ttk.Button(saved_buttons_frame, text="Переименовать",
                   command=self.rename_script).pack(side="left", padx=2)
        # ДОБАВЛЕНА КНОПКА: Показать файл
        ttk.Button(saved_buttons_frame, text="Показать файл",
                   command=self.show_script_file).pack(side="left", padx=2)

        # Treeview for saved scripts - ОБНОВЛЕНО: добавлен столбец autostart
        tree_frame = ttk.Frame(saved_catalog_frame)
        tree_frame.pack(fill="both", expand=True)

        # ОБНОВЛЕНО: Добавлен столбец "autostart"
        self.saved_tree = ttk.Treeview(tree_frame, columns=("status", "autostart"), show="tree headings", height=15)
        self.saved_tree.heading("#0", text="Скрипты")
        self.saved_tree.column("#0", width=250)  # уменьшена ширина для нового столбца
        self.saved_tree.heading("status", text="Статус")
        self.saved_tree.column("status", width=100)
        self.saved_tree.heading("autostart", text="Автозапуск")
        self.saved_tree.column("autostart", width=100)

        tree_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.saved_tree.yview)
        self.saved_tree.configure(yscrollcommand=tree_scrollbar.set)

        self.saved_tree.pack(side="left", fill="both", expand=True)
        tree_scrollbar.pack(side="right", fill="y")

        # Bind double-click to toggle active state
        self.saved_tree.bind("<Double-Button-1>", self.on_tree_double_click)

        # Применяем тему после создания всех элементов
        self.apply_theme(self.current_theme)

    def show_info(self):
        """Показывает информацию о программе"""
        info_text = """Python Script Manager (PSM) - менеджер для управления Python-скриптами

Версия: 2.0
Разработчик: Vanillllla

Основные возможности:
• Запуск и остановка Python-скриптов
• Мониторинг потребления ресурсов (CPU, память)
• Интерактивная консоль для взаимодействия со скриптами
• Каталог скриптов с возможностью группировки
• Темная и светлая темы оформления
• Автозапуск скриптов при старте программы
• Работа в системном трее
• Обработка и отображение ошибок

Использование:
1. Добавьте скрипты через кнопку 'Добавить' в каталоге
2. Активируйте скрипты двойным кликом или через меню
3. Запускайте/останавливайте скрипты кнопками в основном окне
4. Используйте консоль для взаимодействия с запущенными скриптами
5. Настройте автозапуск в настройках скрипта

Для получения дополнительной информации посетите репозиторий GitHub."""

        info_window = tk.Toplevel(self.root)
        info_window.title("Информация о программе")
        info_window.geometry("600x500")
        info_window.resizable(False, False)
        info_window.transient(self.root)
        info_window.grab_set()
        info_window.attributes('-topmost', True)

        main_frame = ttk.Frame(info_window, padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="Python Script Manager (PSM)",
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))

        # Text widget for info with scrollbar
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        text_widget = tk.Text(
            text_frame,
            wrap=tk.WORD,
            padx=10,
            pady=10,
            font=("Arial", 10),
            bg=THEMES[self.current_theme]["listbox_bg"],
            fg=THEMES[self.current_theme]["listbox_fg"]
        )
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)

        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        text_widget.insert(tk.END, info_text)
        text_widget.config(state=tk.DISABLED)

        # Close button
        ttk.Button(main_frame, text="Закрыть", command=info_window.destroy).pack(pady=10)

    def open_github(self):
        """Открывает репозиторий GitHub в браузере"""
        try:
            import webbrowser
            webbrowser.open("https://github.com/Vanillllla/ScriptManager")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть браузер: {str(e)}")

    def setup_tray_icon(self):
        """Создает иконку в системном трее"""
        try:
            # Создаем изображение для иконки
            image = Image.new('RGB', (64, 64), color='white')
            dc = ImageDraw.Draw(image)
            dc.rectangle([16, 16, 48, 48], fill='blue')
            dc.text((25, 25), 'PSM', fill='white')

            # Создаем функцию для показа окна
            def show_window(icon, item):
                self.show_from_tray()

            # Создаем меню для иконки в трее
            menu = pystray.Menu(
                pystray.MenuItem('Развернуть окно', show_window),
                pystray.MenuItem('Закрыть', self.quit_application)
            )

            # Создаем иконку в трее
            self.tray_icon = pystray.Icon("script_manager", image, "Python Script Manager (PSM)", menu)

            # Устанавливаем обработчик для левого клика
            self.tray_icon.on_click = show_window

            # Запускаем иконку в трее в отдельном потоке
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
        except Exception as e:
            print(f"Ошибка создания иконки в трее: {e}")

    def hide_to_tray(self):
        """Скрывает окно в трей"""
        self.root.withdraw()
        # Убедимся, что иконка в трее видима
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.visible = True

    def show_from_tray(self, icon=None, item=None):
        """Показывает окно из трея"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', True)
        # Убираем поверх всех окон после показа
        self.root.after(100, lambda: self.root.attributes('-topmost', False))

    def quit_application(self, icon=None, item=None):
        """Полностью выключает программу"""
        # Сохраняем все данные
        self.save_scripts()
        self.save_settings()

        # Останавливаем все скрипты
        for script_data in self.script_frames:
            if script_data['is_running']:
                self.stop_script(script_data['script_uuid'])

        # Закрываем все открытые консоли
        for console in self.open_consoles.values():
            try:
                console.destroy()
            except:
                pass

        # Останавливаем иконку в трее
        if hasattr(self, 'tray_icon') and self.tray_icon:
            self.tray_icon.stop()

        # Закрываем приложение
        self.root.quit()
        self.root.destroy()

    def show_error_dialog(self, script_uuid, error_message):
        """Показывает диалоговое окно с информацией об ошибке"""
        script_info = self.saved_scripts.get(script_uuid)
        if not script_info:
            return

        script_name = script_info.get('display_name', script_info['name'])

        # Накопление ошибок для одного скрипта
        if script_uuid in self.error_messages:
            self.error_messages[script_uuid] += f"\n{error_message}"
        else:
            self.error_messages[script_uuid] = error_message

        # Показываем диалог с накопленными ошибками
        ErrorDialog(self.root, script_name, self.error_messages[script_uuid], self.current_theme)

        # Очищаем накопленные ошибки для этого скрипта
        self.error_messages[script_uuid] = ""

    def open_console(self, script_uuid):
        """Открывает консоль для скрипта"""
        for script_data in self.script_frames:
            if script_data['script_uuid'] == script_uuid and script_data['is_running']:
                script_info = self.saved_scripts.get(script_uuid)
                if not script_info:
                    return

                script_name = script_info.get('display_name', script_info['name'])

                # Если консоль уже открыта, фокусируемся на ней
                if script_uuid in self.open_consoles:
                    try:
                        self.open_consoles[script_uuid].lift()
                        self.open_consoles[script_uuid].focus_force()
                        return
                    except:
                        # Если окно было закрыто, удаляем из словаря
                        del self.open_consoles[script_uuid]

                # Создаем новую консоль
                console = ConsoleDialog(
                    self.root,
                    script_name,
                    script_data['process'],
                    self.current_theme
                )

                # Восстанавливаем предыдущий вывод если он есть
                if script_uuid in self.process_output_buffers:
                    console.load_historical_output(self.process_output_buffers[script_uuid])

                # Сохраняем ссылку на консоль
                self.open_consoles[script_uuid] = console

                # Обработка закрытия консоли
                def on_close(console=console, script_uuid=script_uuid):
                    if script_uuid in self.open_consoles:
                        del self.open_consoles[script_uuid]
                    console.destroy()

                console.protocol("WM_DELETE_WINDOW", on_close)
                break
        else:
            messagebox.showwarning("Предупреждение", "Скрипт не запущен")

    def change_theme(self, theme_name):
        """Изменяет тему приложения"""
        self.current_theme = theme_name
        self.apply_theme(theme_name)
        self.settings['theme'] = theme_name
        self.save_settings()

    def on_tree_double_click(self, event):
        """Обработчик двойного клика по дереву скриптов"""
        selection = self.saved_tree.selection()
        if not selection:
            return

        item = selection[0]
        parent = self.saved_tree.parent(item)

        # Если есть родитель, то это скрипт (а не группа)
        if parent:
            item_text = self.saved_tree.item(item)["text"]
            parent_text = self.saved_tree.item(parent)["text"]

            # Находим скрипт по имени
            script_uuid = None
            for uuid, info in self.saved_scripts.items():
                if info.get('display_name', info['name']) == item_text:
                    script_uuid = uuid
                    break

            if script_uuid:
                if parent_text == "Активные скрипты":
                    # Перемещаем в неактивные с подтверждением
                    if messagebox.askyesno("Подтверждение",
                                           f"Вы уверены, что хотите переместить скрипт '{item_text}' в неактивные?"):
                        self.remove_from_active(script_uuid)
                elif parent_text == "Неактивные скрипты":
                    # Перемещаем в активные
                    self.add_to_active(script_uuid)

    def update_saved_tree(self):
        """Обновляет дерево сохраненных скриптов"""
        self.saved_tree.delete(*self.saved_tree.get_children())

        # Активные скрипты
        active_node = self.saved_tree.insert("", "end", text="Активные скрипты", values=("", ""))
        for script_uuid in self.active_scripts:
            script_info = self.saved_scripts.get(script_uuid)
            if script_info:
                display_name = script_info.get('display_name', script_info['name'])
                # Определяем статус скрипта
                status = "Запущен" if self.is_script_running(script_uuid) else "Остановлен"
                # ОБНОВЛЕНО: Добавляем информацию об автозапуске
                autostart_status = "Автозапуск" if script_info.get('autostart', False) else ""
                self.saved_tree.insert(active_node, "end", text=display_name, values=(status, autostart_status))

        # Неактивные скрипты
        inactive_node = self.saved_tree.insert("", "end", text="Неактивные скрипты", values=("", ""))
        for script_uuid, script_info in self.saved_scripts.items():
            if script_uuid not in self.active_scripts:
                display_name = script_info.get('display_name', script_info['name'])
                # ОБНОВЛЕНО: Добавляем информацию об автозапуске
                autostart_status = "Автозапуск" if script_info.get('autostart', False) else ""
                self.saved_tree.insert(inactive_node, "end", text=display_name, values=("Неактивен", autostart_status))

        # Всегда разворачиваем узлы
        self.saved_tree.item(active_node, open=True)
        self.saved_tree.item(inactive_node, open=True)

    def is_script_running(self, script_uuid):
        """Проверяет, запущен ли скрипт"""
        for script_data in self.script_frames:
            if script_data['script_uuid'] == script_uuid:
                return script_data['is_running']
        return False

    def open_settings(self):
        # ДОБАВЛЕНО: Обновляем состояние автозапуска перед открытием диалога
        startup_folder = winshell.startup()
        shortcut_path = os.path.join(startup_folder, "Python Script Manager (PSM).lnk")
        actual_autostart = os.path.exists(shortcut_path)
        self.settings['autostart'] = actual_autostart

        dialog = SettingsDialog(self.root, self.settings)
        self.root.wait_window(dialog)
        self.save_settings()

    def load_settings(self):
        """Загружает настройки из JSON файла"""
        try:
            settings_path = os.path.join(BASE_PATH, "settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)

                # Применяем сохраненную тему
                saved_theme = self.settings.get('theme', 'light')
                self.change_theme(saved_theme)

                # ДОБАВЛЕНО: Устанавливаем настройку мониторинга производительности по умолчанию в True
                if 'performance_monitoring' not in self.settings:
                    self.settings['performance_monitoring'] = True

                # ОБНОВЛЕНО: Если default_interpreter не установлен, ищем системный Python
                if 'default_interpreter' not in self.settings or not self.settings['default_interpreter']:
                    self.settings['default_interpreter'] = find_system_python()
                    self.save_settings()

            else:
                # ОБНОВЛЕНО: При первом запуске используем системный Python
                self.settings = {
                    'theme': 'light',
                    'performance_monitoring': True,
                    'autostart': False,
                    'default_interpreter': find_system_python()  # Ищем системный Python
                }
                self.save_settings()

            # Проверяем актуальность состояния автозапуска
            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, "Python Script Manager (PSM).lnk")
            actual_autostart = os.path.exists(shortcut_path)

            # Синхронизируем настройку с фактическим состоянием
            if self.settings.get('autostart', False) != actual_autostart:
                self.settings['autostart'] = actual_autostart
                self.save_settings()

        except Exception as e:
            print(f"Ошибка загрузки настроек: {str(e)}")
            self.settings = {
                'theme': 'light',
                'performance_monitoring': True,
                'autostart': False,
                'default_interpreter': find_system_python()  # Ищем системный Python даже при ошибке
            }

    def save_settings(self):
        """Сохраняет настройки в JSON файл"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {str(e)}")

    def save_scripts(self):
        """Сохраняет все скрипты в JSON файл"""
        try:
            # Сохраняем информацию о состоянии скриптов (активные/неактивные)
            scripts_to_save = {}
            for script_uuid, script_info in self.saved_scripts.items():
                script_copy = script_info.copy()
                # Добавляем информацию о том, активен ли скрипт
                script_copy['is_active'] = script_uuid in self.active_scripts
                # Добавляем информацию о состоянии выполнения
                for script_data in self.script_frames:
                    if script_data['script_uuid'] == script_uuid:
                        script_copy['is_running'] = script_data['is_running']
                        script_copy['pid'] = script_data.get('pid')
                        break
                scripts_to_save[script_uuid] = script_copy

            with open(self.scripts_file, 'w', encoding='utf-8') as f:
                json.dump(scripts_to_save, f, indent=4, ensure_ascii=False)

            # Сохраняем настройки
            self.save_settings()
        except Exception as e:
            print(f"Ошибка сохранения скриптов: {str(e)}")

    def load_scripts(self):
        """Загружает скрипты из JSON файла"""
        try:
            if os.path.exists(self.scripts_file):
                with open(self.scripts_file, 'r', encoding='utf-8') as f:
                    loaded_scripts = json.load(f)

                # Очищаем текущие скрипты
                for script_data in self.script_frames:
                    if script_data['is_running']:
                        self.stop_script(script_data['script_uuid'])

                self.saved_scripts.clear()
                self.active_scripts.clear()
                self.script_frames.clear()

                # Очищаем интерфейс
                for widget in self.scrollable_frame.winfo_children():
                    widget.destroy()

                self.update_saved_tree()

                # Загружаем скрипты из файла
                scripts_to_start = []  # Список скриптов для автозапуска

                for script_uuid, script_info in loaded_scripts.items():
                    self.saved_scripts[script_uuid] = script_info

                    # Восстанавливаем активные скрипты
                    if script_info.get('is_active', False):
                        self.active_scripts.append(script_uuid)
                        self.create_script_frame(script_uuid)

                    # Собираем скрипты для автозапуска (только те, у которых autostart=True)
                    if script_info.get('autostart', False):
                        # Если скрипт еще не в активных, добавляем его
                        if script_uuid not in self.active_scripts:
                            self.active_scripts.append(script_uuid)
                            self.create_script_frame(script_uuid)
                        scripts_to_start.append(script_uuid)

                # Обновляем дерево
                self.update_saved_tree()

                # Запускаем только скрипты с autostart=True
                for script_uuid in scripts_to_start:
                    self.root.after(1000, lambda s=script_uuid: self.start_script(s))

        except Exception as e:
            print(f"Ошибка загрузки скриптов: {str(e)}")

    def add_to_active(self, script_uuid=None):
        """Добавляет выбранный скрипт из сохраненных в активные"""
        if script_uuid is None:
            # Старый метод для обратной совместимости
            selection = self.saved_tree.selection()
            if not selection:
                return

            item = selection[0]
            parent = self.saved_tree.parent(item)

            if not parent:
                return

            item_text = self.saved_tree.item(item)["text"]

            # Находим скрипт по имени
            for uuid, info in self.saved_scripts.items():
                if info.get('display_name', info['name']) == item_text:
                    script_uuid = uuid
                    break

        if script_uuid:
            # Проверяем, не добавлен ли уже скрипт в активные
            if script_uuid in self.active_scripts:
                return

            # Добавляем в активные
            self.active_scripts.append(script_uuid)
            self.create_script_frame(script_uuid)
            self.update_saved_tree()
            self.save_scripts()

    def delete_script(self):
        """Удаляет выбранный скрипт из сохраненных"""
        selection = self.saved_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите скрипт для удаления")
            return

        item = selection[0]
        parent = self.saved_tree.parent(item)

        if not parent:
            return

        item_text = self.saved_tree.item(item)["text"]

        # Находим скрипт по имени
        script_uuid = None
        for uuid, info in self.saved_scripts.items():
            if info.get('display_name', info['name']) == item_text:
                script_uuid = uuid
                break

        if not script_uuid:
            return

        script_info = self.saved_scripts.get(script_uuid)
        if not script_info:
            return

        script_name = script_info.get('display_name', script_info['name'])

        if messagebox.askyesno("Подтверждение", f"Вы уверены, что хотите удалить скрипт '{script_name}'?"):
            # Останавливаем скрипт если запущен
            if script_uuid in self.active_scripts:
                self.remove_from_active(script_uuid)

            # Удаляем из сохраненных
            if script_uuid in self.saved_scripts:
                del self.saved_scripts[script_uuid]

            # Удаляем связанные данные
            if script_uuid in self.process_output_buffers:
                del self.process_output_buffers[script_uuid]
            if script_uuid in self.open_consoles:
                try:
                    self.open_consoles[script_uuid].destroy()
                except:
                    pass
                del self.open_consoles[script_uuid]
            if script_uuid in self.error_messages:
                del self.error_messages[script_uuid]

            # Обновляем интерфейс
            self.update_saved_tree()
            self.save_scripts()

    def rename_script(self):
        """Переименовывает выбранный скрипт"""
        selection = self.saved_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите скрипт для переименования")
            return

        item = selection[0]
        parent = self.saved_tree.parent(item)

        if not parent:
            return

        item_text = self.saved_tree.item(item)["text"]

        # Находим скрипт по имени
        script_uuid = None
        for uuid, info in self.saved_scripts.items():
            if info.get('display_name', info['name']) == item_text:
                script_uuid = uuid
                break

        if not script_uuid:
            return

        script_info = self.saved_scripts.get(script_uuid)
        if not script_info:
            return

        current_name = script_info.get('display_name', script_info['name'])

        dialog = RenameDialog(self.root, current_name)
        self.root.wait_window(dialog)

        if dialog.result:
            new_name = dialog.result
            script_info['display_name'] = new_name
            self.update_saved_tree()
            # ИСПРАВЛЕНО: Обновляем только конкретный фрейм вместо всех
            self.update_single_script_frame(script_uuid)
            self.save_scripts()

    def show_script_file(self):
        """Показывает файл скрипта в проводнике"""
        selection = self.saved_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите скрипт для показа файла")
            return

        item = selection[0]
        parent = self.saved_tree.parent(item)

        if not parent:
            return

        item_text = self.saved_tree.item(item)["text"]

        # Находим скрипт по имени
        script_uuid = None
        for uuid, info in self.saved_scripts.items():
            if info.get('display_name', info['name']) == item_text:
                script_uuid = uuid
                break

        if not script_uuid:
            return

        script_info = self.saved_scripts.get(script_uuid)
        if not script_info:
            return

        script_path = script_info['path']
        folder_path = os.path.dirname(script_path)

        if os.path.exists(folder_path):
            try:
                # Открываем папку в проводнике Windows
                os.startfile(folder_path)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось открыть папку: {str(e)}")
        else:
            messagebox.showerror("Ошибка", f"Папка {folder_path} не найдена")

    def update_single_script_frame(self, script_uuid):
        """Обновляет только один фрейм скрипта"""
        for script_data in self.script_frames:
            if script_data['script_uuid'] == script_uuid:
                script_info = self.saved_scripts.get(script_uuid)
                if not script_info:
                    return

                display_name = script_info.get('display_name', script_info['name'])
                # Обновляем заголовок фрейма
                script_data['frame'].configure(text=display_name)
                break

    def update_script_frames(self):
        """Обновляет фреймы активных скриптов"""
        # Очищаем текущие фреймы
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Создаем фреймы заново
        self.script_frames.clear()
        for script_uuid in self.active_scripts:
            self.create_script_frame(script_uuid)

    def add_script(self):
        """Добавляет новый скрипт в оба каталога"""
        script_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
        if script_path:
            script_name = os.path.basename(script_path).replace('.py', '')

            # ОБНОВЛЕНО: Используем интерпретатор из настроек (уже должен быть системный Python)
            default_interpreter = self.settings.get('default_interpreter', find_system_python())

            # Создаем уникальный идентификатор для скрипта
            script_uuid = str(uuid.uuid4())

            script_info = {
                'uuid': script_uuid,
                'name': script_name,
                'display_name': script_name,
                'path': script_path,
                'interpreter': default_interpreter,
                'autostart': False
            }

            # Добавляем в сохраненные
            self.saved_scripts[script_uuid] = script_info

            # Добавляем в активные
            self.active_scripts.append(script_uuid)

            # Обновляем интерфейс
            self.create_script_frame(script_uuid)
            self.update_saved_tree()

            # Сохраняем
            self.save_scripts()

    def create_script_frame(self, script_uuid):
        """Создает фрейм для активного скрипта"""
        script_info = self.saved_scripts.get(script_uuid)
        if not script_info:
            return

        display_name = script_info.get('display_name', script_info['name'])

        # Создаем кастомный фрейм с увеличенной высотой
        frame = ttk.LabelFrame(self.scrollable_frame, text=display_name, padding=10)
        frame.pack(fill="x", pady=8, padx=5)

        # Устанавливаем минимальную высоту фрейма
        frame.configure(height=140)

        # Controls
        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill="x", pady=(0, 8))

        # Кнопка консоли - изначально отключена
        console_btn = ttk.Button(controls_frame, text="Консоль",
                                 state=tk.DISABLED,
                                 command=lambda: self.open_console(script_uuid))
        console_btn.pack(side="right", padx=2)

        ttk.Button(controls_frame, text="Настройки",
                   command=lambda: self.configure_script(script_uuid)).pack(side="right", padx=2)
        ttk.Button(controls_frame, text="Удалить из активных",
                   command=lambda: self.remove_from_active(script_uuid)).pack(side="right", padx=2)

        # Объединенная кнопка запуска/остановки
        toggle_btn = ttk.Button(controls_frame, text="Запуск", style="Start.TButton",
                                command=lambda: self.toggle_script(script_uuid))
        toggle_btn.pack(side="right", padx=2)

        # Resource monitoring
        resources_frame = ttk.Frame(frame)
        resources_frame.pack(fill="x", pady=8)

        cpu_var = tk.IntVar()
        memory_var = tk.IntVar()

        ttk.Label(resources_frame, text="CPU:").grid(row=0, column=0, sticky="w")
        cpu_bar = ttk.Progressbar(resources_frame, variable=cpu_var, maximum=100)
        cpu_bar.grid(row=0, column=1, sticky="ew", padx=5)
        cpu_label = ttk.Label(resources_frame, text="0%")
        cpu_label.grid(row=0, column=2, padx=5)

        ttk.Label(resources_frame, text="Память:").grid(row=1, column=0, sticky="w")
        memory_bar = ttk.Progressbar(resources_frame, variable=memory_var, maximum=100)
        memory_bar.grid(row=1, column=1, sticky="ew", padx=5)
        memory_label = ttk.Label(resources_frame, text="0%")
        memory_label.grid(row=1, column=2, padx=5)

        resources_frame.columnconfigure(1, weight=1)

        script_frame_data = {
            'frame': frame,
            'script_uuid': script_uuid,
            'script_info': script_info,
            'process': None,
            'pid': None,
            'cpu_var': cpu_var,
            'memory_var': memory_var,
            'cpu_label': cpu_label,
            'memory_label': memory_label,
            'toggle_btn': toggle_btn,
            'console_btn': console_btn,
            'is_running': False,
            'last_cpu_times': (0, 0),
            'last_check_time': time.time()
        }

        self.script_frames.append(script_frame_data)

        # Явно устанавливаем начальное состояние кнопок
        self.update_toggle_button(script_frame_data)

        # Обновляем область прокрутки после добавления нового фрейма
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def toggle_script(self, script_uuid):
        """Переключает состояние скрипта (запуск/остановка)"""
        for script_data in self.script_frames:
            if script_data['script_uuid'] == script_uuid:
                if script_data['is_running']:
                    self.stop_script(script_uuid)
                else:
                    self.start_script(script_uuid)
                break

    def update_toggle_button(self, script_data):
        """Обновляет вид кнопки запуска/остановки"""
        # Проверяем, существуют ли еще виджеты
        if not script_data['frame'].winfo_exists():
            return

        try:
            if script_data['is_running']:
                script_data['toggle_btn'].config(text="Остановить", style="Stop.TButton")
                script_data['console_btn'].config(state=tk.NORMAL)
            else:
                script_data['toggle_btn'].config(text="Запуск", style="Start.TButton")
                script_data['console_btn'].config(state=tk.DISABLED)
        except tk.TclError:
            # Игнорируем ошибки, если виджеты уже уничтожены
            pass

    def remove_from_active(self, script_uuid):
        """Удаляет скрипт из активных (но оставляет в сохраненных)"""
        # Останавливаем скрипт если запущен
        for script_data in self.script_frames:
            if script_data['script_uuid'] == script_uuid:
                if script_data['is_running']:
                    self.stop_script(script_uuid)
                break

        # Удаляем из активных
        if script_uuid in self.active_scripts:
            self.active_scripts.remove(script_uuid)

        # ИСПРАВЛЕНО: Удаляем только конкретный фрейм вместо пересоздания всех
        for i, script_data in enumerate(self.script_frames):
            if script_data['script_uuid'] == script_uuid:
                # Уничтожаем фрейм
                script_data['frame'].destroy()
                # Удаляем из списка фреймов
                self.script_frames.pop(i)
                break

        self.update_saved_tree()
        self.save_scripts()

    def configure_script(self, script_uuid):
        script_info = self.saved_scripts.get(script_uuid)
        if not script_info:
            return

        display_name = script_info.get('display_name', script_info['name'])

        config_window = tk.Toplevel(self.root)
        config_window.title(f"Настройки: {display_name}")
        config_window.geometry("500x350")
        config_window.resizable(False, False)
        config_window.transient(self.root)
        config_window.grab_set()
        config_window.attributes('-topmost', True)
        config_window.focus_force()

        main_frame = ttk.Frame(config_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text=f"Настройки для: {display_name}", font=("Arial", 11, "bold")).pack(pady=(0, 10))

        # Display name setting
        name_frame = ttk.Frame(main_frame)
        name_frame.pack(fill=tk.X, pady=5)

        ttk.Label(name_frame, text="Отображаемое имя:").pack(anchor=tk.W)

        name_var = tk.StringVar(value=display_name)
        name_entry = ttk.Entry(name_frame, textvariable=name_var, width=50)
        name_entry.pack(fill=tk.X, pady=(5, 0))

        # Interpreter settings
        interpreter_frame = ttk.Frame(main_frame)
        interpreter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(interpreter_frame, text="Интерпретатор:").pack(anchor=tk.W)

        interpreter_subframe = ttk.Frame(interpreter_frame)
        interpreter_subframe.pack(fill=tk.X, pady=(5, 0))

        interpreter_var = tk.StringVar(value=script_info['interpreter'])
        interpreter_entry = ttk.Entry(interpreter_subframe, textvariable=interpreter_var)
        interpreter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        def browse_interpreter():
            path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe"), ("All files", "*.*")])
            if path:
                interpreter_var.set(path)

        ttk.Button(interpreter_subframe, text="Обзор", command=browse_interpreter).pack(side=tk.RIGHT)

        # ИЗМЕНЕНО: Сначала кнопка пакетов, потом автозапуск
        # Packages button - ПЕРЕМЕЩЕН ВВЕРХ
        ttk.Button(main_frame, text="Показать установленные пакеты",
                   command=lambda: self.show_script_packages(interpreter_var.get())).pack(anchor=tk.W, pady=5)

        # Autostart setting - ПЕРЕМЕЩЕН ВНИЗ
        autostart_frame = ttk.Frame(main_frame)
        autostart_frame.pack(fill=tk.X, pady=5)

        autostart_var = tk.BooleanVar(value=script_info.get('autostart', False))
        ttk.Checkbutton(autostart_frame, text="Запускать скрипт при старте программы",
                        variable=autostart_var).pack(anchor=tk.W)

        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)

        def save_config():
            script_info['display_name'] = name_var.get()
            script_info['interpreter'] = interpreter_var.get()
            script_info['autostart'] = autostart_var.get()

            config_window.destroy()
            self.update_saved_tree()
            self.update_single_script_frame(script_uuid)
            self.save_scripts()

        ttk.Button(buttons_frame, text="Сохранить", command=save_config).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(buttons_frame, text="Отмена", command=config_window.destroy).pack(side=tk.RIGHT)

    def show_script_packages(self, interpreter):
        # ОБНОВЛЕНО: Добавляем проверку интерпретатора
        if not interpreter or not os.path.exists(interpreter):
            # Пытаемся найти системный Python
            system_python = find_system_python()
            if system_python and os.path.exists(system_python):
                interpreter = system_python
                # Обновляем настройки
                self.settings['default_interpreter'] = interpreter
                self.save_settings()
            else:
                messagebox.showerror("Ошибка",
                                     "Интерпретатор Python не найден. Пожалуйста, укажите путь к Python в настройках.")
                return

        try:
            # Get installed packages
            result = subprocess.run([
                interpreter, "-m", "pip", "list"
            ], capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                # Show packages in a new window
                packages_window = tk.Toplevel(self.root)
                packages_window.title("Установленные пакеты")
                packages_window.geometry("600x400")
                packages_window.transient(self.root)
                packages_window.grab_set()
                packages_window.attributes('-topmost', True)
                packages_window.focus_force()

                text_frame = ttk.Frame(packages_window, padding=10)
                text_frame.pack(fill=tk.BOTH, expand=True)

                text_widget = tk.Text(text_frame, wrap=tk.WORD)
                scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
                text_widget.config(yscrollcommand=scrollbar.set)

                text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

                text_widget.insert(tk.END, result.stdout)
                text_widget.config(state=tk.DISABLED)
            else:
                messagebox.showerror("Ошибка", f"Не удалось получить список пакетов:\n{result.stderr}")

        except subprocess.TimeoutExpired:
            messagebox.showerror("Ошибка", "Таймаут при получении списка пакетов")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при получении списка пакетов: {str(e)}")

    def validate_interpreter(self, interpreter_path):
        """Проверяет, существует ли интерпретатор и является ли он валидным Python"""
        if not interpreter_path or not os.path.exists(interpreter_path):
            return False

        # Проверяем, что это исполняемый файл Python
        filename = os.path.basename(interpreter_path).lower()
        if not (filename.startswith('python') and filename.endswith('.exe')):
            return False

        return True

    def start_script(self, script_uuid):
        for script_data in self.script_frames:
            if script_data['script_uuid'] == script_uuid:
                script_info = script_data['script_info']
                try:
                    if not os.path.exists(script_info['path']):
                        messagebox.showerror("Ошибка", f"Файл {script_info['path']} не найден")
                        return

                    # ОБНОВЛЕНО: Проверяем интерпретатор
                    interpreter = script_info['interpreter']
                    if not interpreter or not os.path.exists(interpreter):
                        # Пытаемся использовать системный Python
                        system_python = find_system_python()
                        if system_python and os.path.exists(system_python):
                            interpreter = system_python
                            script_info['interpreter'] = interpreter  # Обновляем настройки скрипта
                        else:
                            messagebox.showerror("Ошибка", f"Интерпретатор Python не найден: {interpreter}")
                            return

                    # Запускаем процесс с правильной кодировкой
                    script_data['process'] = subprocess.Popen([
                        interpreter,
                        script_info['path']
                    ],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        stdin=subprocess.PIPE,
                        bufsize=0,
                        universal_newlines=False)

                    # ... остальной код без изменений ...

                    script_data['pid'] = script_data['process'].pid
                    script_data['is_running'] = True
                    self.update_toggle_button(script_data)

                    # Обновляем статус в дереве
                    self.update_saved_tree()

                    # Инициализируем буфер вывода для этого процесса
                    self.process_output_buffers[script_uuid] = ""

                    # Запускаем мониторинг вывода в отдельном потоке
                    threading.Thread(target=self.monitor_script_output,
                                     args=(script_data,), daemon=True).start()

                    # Инициализация отслеживания CPU
                    try:
                        process = psutil.Process(script_data['pid'])
                        cpu_times = process.cpu_times()
                        script_data['last_cpu_times'] = (cpu_times.user, cpu_times.system)
                        script_data['last_check_time'] = time.time()
                    except:
                        pass

                except Exception as e:
                    error_msg = f"Не удалось запустить скрипт: {str(e)}"
                    # ИСПРАВЛЕНИЕ: Правильный вызов show_error_dialog
                    self.show_error_dialog(script_uuid, error_msg)
                    # Сбрасываем состояние кнопки при ошибке запуска
                    script_data['is_running'] = False
                    self.update_toggle_button(script_data)
                    # Обновляем статус в дереве при ошибке
                    self.update_saved_tree()
                break

    def monitor_script_output(self, script_data):
        """Мониторинг вывода скрипта для перехвата ошибок и вывода в консоль"""
        process = script_data['process']
        script_uuid = script_data['script_uuid']
        script_info = script_data['script_info']

        # Обновляем время для корректного расчета CPU
        script_data['last_check_time'] = time.time()

        # Функция для проверки, существует ли еще скрипт
        def script_still_exists():
            return any(sd for sd in self.script_frames if sd['script_uuid'] == script_uuid)

        # Функция для безопасного добавления текста в консоль
        def safe_append_text(text, console):
            if console and console.winfo_exists() and script_still_exists():
                console.after(0, lambda: console.append_text(text))

        # Функция для декодирования байтов с обработкой ошибок
        def decode_bytes(byte_data):
            try:
                return byte_data.decode('utf-8')
            except UnicodeDecodeError:
                try:
                    # Пробуем другие распространенные кодировки
                    return byte_data.decode('cp1251')
                except UnicodeDecodeError:
                    try:
                        return byte_data.decode('cp866')
                    except UnicodeDecodeError:
                        # Если все кодировки не подходят, заменяем нечитаемые символы
                        return byte_data.decode('utf-8', errors='replace')

        # Читаем stdout и stderr в реальном времени
        def read_stream(stream, is_stderr=False):
            while script_still_exists() and script_data['is_running'] and process.poll() is None:
                try:
                    # Читаем байты вместо текста
                    raw_line = stream.readline()
                    if raw_line:
                        # Декодируем с правильной кодировкой
                        decoded_line = decode_bytes(raw_line)

                        # УБРАНО: Добавление префикса "ERROR: " для stderr
                        output_line = decoded_line  # Теперь и stderr и stdout выводятся как есть

                        # Сохраняем в буфер
                        if script_uuid in self.process_output_buffers:
                            self.process_output_buffers[script_uuid] += output_line
                        else:
                            self.process_output_buffers[script_uuid] = output_line

                        # Отправляем в открытую консоль
                        if script_uuid in self.open_consoles:
                            console = self.open_consoles[script_uuid]
                            safe_append_text(output_line, console)
                    else:
                        # Если строка пустая, возможно процесс завершился
                        time.sleep(0.1)
                except Exception as e:
                    if script_still_exists():
                        print(f"Ошибка чтения {'stderr' if is_stderr else 'stdout'}: {e}")
                    break

        # Запускаем потоки для чтения stdout и stderr
        stdout_thread = threading.Thread(target=read_stream, args=(process.stdout, False), daemon=True)
        stderr_thread = threading.Thread(target=read_stream, args=(process.stderr, True), daemon=True)

        stdout_thread.start()
        stderr_thread.start()

        # Ждем завершения процесса
        process.wait()

        # Читаем оставшиеся данные после завершения, только если скрипт еще существует
        if script_still_exists():
            try:
                remaining_stdout, remaining_stderr = process.communicate(timeout=2)

                if remaining_stdout:
                    decoded_stdout = decode_bytes(remaining_stdout)
                    if script_uuid in self.process_output_buffers:
                        self.process_output_buffers[script_uuid] += decoded_stdout
                    else:
                        self.process_output_buffers[script_uuid] = decoded_stdout

                    if script_uuid in self.open_consoles:
                        console = self.open_consoles[script_uuid]
                        safe_append_text(decoded_stdout, console)

                if remaining_stderr:
                    decoded_stderr = decode_bytes(remaining_stderr)
                    # УБРАНО: Добавление префикса "ERROR: " для stderr
                    error_output = decoded_stderr
                    if script_uuid in self.process_output_buffers:
                        self.process_output_buffers[script_uuid] += error_output
                    else:
                        self.process_output_buffers[script_uuid] = error_output

                    if script_uuid in self.open_consoles:
                        console = self.open_consoles[script_uuid]
                        safe_append_text(error_output, console)

            except subprocess.TimeoutExpired:
                pass

            # Обновляем состояние после завершения процесса, только если скрипт еще существует
            if script_still_exists():
                script_data['is_running'] = False
                script_data['process'] = None
                script_data['pid'] = None
                self.root.after(0, lambda: self.update_toggle_button(script_data))

                # Если процесс завершился с ошибкой, показываем диалог
                if process.returncode != 0:
                    error_output = self.process_output_buffers.get(script_uuid, "")
                    if error_output:  # Показываем диалог если есть любой вывод ошибки
                        self.root.after(0, lambda: self.show_error_dialog(
                            script_uuid,
                            f"Скрипт завершился с ошибкой (код возврата: {process.returncode})\n\n{error_output}"
                        ))

    def stop_script(self, script_uuid):
        for script_data in self.script_frames:
            if script_data['script_uuid'] == script_uuid and script_data['process']:
                try:
                    script_data['process'].terminate()
                    script_data['process'].wait(timeout=5)
                except:
                    try:
                        script_data['process'].kill()
                    except:
                        pass
                finally:
                    script_data['process'] = None
                    script_data['pid'] = None
                    script_data['is_running'] = False

                    # Безопасное обновление интерфейса
                    if script_data['frame'].winfo_exists():
                        script_data['cpu_var'].set(0)
                        script_data['memory_var'].set(0)
                        script_data['cpu_label'].config(text="0%")
                        script_data['memory_label'].config(text="0%")
                        self.update_toggle_button(script_data)

                    # Обновляем статус в дереве
                    self.update_saved_tree()
                break

    def start_monitoring(self):
        def monitor():
            # ПРОВЕРЯЕМ ВКЛЮЧЕН ЛИ МОНИТОРИНГ
            if not self.settings.get('performance_monitoring', True):
                # Если мониторинг отключен, обнуляем все показатели
                self.total_cpu_var.set(0)
                self.total_memory_var.set(0)
                self.total_cpu_label.config(text="0%")
                self.total_memory_label.config(text="0%")

                for script_data in self.script_frames[:]:
                    if script_data['frame'].winfo_exists():
                        script_data['cpu_var'].set(0)
                        script_data['memory_var'].set(0)
                        script_data['cpu_label'].config(text="0%")
                        script_data['memory_label'].config(text="0%")

                # Планируем следующую проверку (на случай если мониторинг включат)
                self.root.after(1000, monitor)
                return

            total_cpu = 0
            total_memory = 0

            # Получаем общую загрузку системы (включая нашу программу и все процессы)
            system_cpu = psutil.cpu_percent(interval=0.1)

            # Мониторинг индивидуальных скриптов
            for script_data in self.script_frames[:]:
                # Проверяем, существует ли еще фрейм
                if not script_data['frame'].winfo_exists():
                    continue

                if script_data['is_running'] and script_data['pid']:
                    try:
                        process = psutil.Process(script_data['pid'])

                        # Правильный расчет CPU использования для процесса
                        cpu_usage = process.cpu_percent(interval=0.1)

                        # Использование памяти
                        memory_usage = process.memory_percent()

                        # Обновляем интерфейс
                        script_data['cpu_var'].set(int(cpu_usage))
                        script_data['memory_var'].set(int(memory_usage))
                        script_data['cpu_label'].config(text=f"{cpu_usage:.1f}%")
                        script_data['memory_label'].config(text=f"{memory_usage:.1f}%")

                        total_cpu += cpu_usage
                        total_memory += memory_usage

                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        script_data['is_running'] = False
                        script_data['process'] = None
                        script_data['cpu_var'].set(0)
                        script_data['memory_var'].set(0)
                        script_data['cpu_label'].config(text="0%")
                        script_data['memory_label'].config(text="0%")
                else:
                    script_data['cpu_var'].set(0)
                    script_data['memory_var'].set(0)
                    script_data['cpu_label'].config(text="0%")
                    script_data['memory_label'].config(text="0%")

            # Общая нагрузка (системная + все субпроцессы)
            # Ограничиваем максимальное значение 100%
            total_cpu = min(system_cpu, 100)
            total_memory = min(total_memory, 100)

            self.total_cpu_var.set(int(total_cpu))
            self.total_memory_var.set(int(total_memory))
            self.total_cpu_label.config(text=f"{total_cpu:.1f}%")
            self.total_memory_label.config(text=f"{total_memory:.1f}%")

            # Планируем следующее обновление
            self.root.after(1000, monitor)

        # Запускаем мониторинг
        self.root.after(1000, monitor)


if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptManagerTkinter(root)
    root.mainloop()