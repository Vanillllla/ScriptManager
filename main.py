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


class ErrorDialog(tk.Toplevel):
    def __init__(self, parent, script_name, error_message):
        super().__init__(parent)
        self.title("Ошибка скрипта")
        self.geometry("700x500")
        self.resizable(True, True)
        self.transient(parent)
        self.grab_set()

        self.script_name = script_name
        self.error_message = error_message

        self.init_ui()

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
        self.title("Настройки Script Manager")
        self.geometry("500x400")
        self.resizable(False, False)

        self.result = None
        self.init_ui()

    def init_ui(self):
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Autostart setting
        autostart_frame = ttk.LabelFrame(main_frame, text="Настройки приложения", padding=10)
        autostart_frame.pack(fill=tk.X, pady=(0, 10))

        self.autostart_var = tk.BooleanVar(value=self.settings.get('autostart', False))
        ttk.Checkbutton(autostart_frame, text="Запускать Script Manager при старте системы",
                        variable=self.autostart_var,
                        command=self.toggle_autostart).pack(anchor=tk.W)

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

    def toggle_autostart(self):
        """Включение/выключение автозапуска"""
        try:
            startup_folder = winshell.startup()
            shortcut_path = os.path.join(startup_folder, "Script Manager.lnk")

            if self.autostart_var.get():
                # Создаем ярлык в автозагрузке
                target = sys.executable
                wDir = os.path.dirname(sys.executable)
                icon = sys.executable

                shell = Dispatch('WScript.Shell')
                shortcut = shell.CreateShortCut(shortcut_path)
                shortcut.Targetpath = target
                shortcut.WorkingDirectory = wDir
                shortcut.IconLocation = icon
                shortcut.save()
            else:
                # Удаляем ярлык из автозагрузки
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось настроить автозапуск: {str(e)}")

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


class ScriptManagerTkinter:
    def __init__(self, root):
        self.root = root
        self.root.title("Script Manager")
        self.root.geometry("1200x800")

        # Настройка иконки в трее
        self.setup_tray_icon()

        # Переопределяем закрытие окна - скрываем в трей
        self.root.protocol('WM_DELETE_WINDOW', self.hide_to_tray)

        self.active_scripts = []  # Скрипты с активными панелями
        self.saved_scripts = []  # Все сохраненные скрипты
        self.script_frames = []
        self.scripts_file = "scripts.json"
        self.settings_file = "settings.json"
        self.settings = {}

        self.setup_ui()
        self.load_settings()
        self.load_scripts()
        self.start_monitoring()

    def setup_tray_icon(self):
        """Создает иконку в системном трее"""
        # Создаем изображение для иконки
        image = Image.new('RGB', (64, 64), color='white')
        dc = ImageDraw.Draw(image)
        dc.rectangle([16, 16, 48, 48], fill='blue')
        dc.text((25, 25), 'SM', fill='white')

        # Создаем меню для иконки в трее
        menu = pystray.Menu(
            pystray.MenuItem('Развернуть окно', self.show_from_tray),
            pystray.MenuItem('Закрыть', self.quit_application)
        )

        # Создаем иконку в трее
        self.tray_icon = pystray.Icon("script_manager", image, "Script Manager", menu)

        # Запускаем иконку в трее в отдельном потоке
        self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
        self.tray_thread.start()

    def hide_to_tray(self):
        """Скрывает окно в трей"""
        self.root.withdraw()

    def show_from_tray(self, icon=None, item=None):
        """Показывает окно из трея"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def quit_application(self, icon=None, item=None):
        """Полностью выключает программу"""
        # Сохраняем все данные
        self.save_scripts()
        self.save_settings()

        # Останавливаем все скрипты
        for script_data in self.script_frames:
            if script_data['is_running']:
                self.stop_script(script_data['script_info'])

        # Останавливаем иконку в трее
        self.tray_icon.stop()

        # Закрываем приложение
        self.root.quit()
        self.root.destroy()

    def show_error_dialog(self, script_name, error_message):
        """Показывает диалоговое окно с информацией об ошибке"""
        ErrorDialog(self.root, script_name, error_message)

    def setup_ui(self):
        # Main menu
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ФАЙЛ", menu=file_menu)
        file_menu.add_command(label="Добавить скрипт", command=self.add_script)
        file_menu.add_command(label="Настройки", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Свернуть в трей", command=self.hide_to_tray)
        file_menu.add_command(label="Закрыть", command=self.quit_application)

        menubar.add_cascade(label="ГЛАВНАЯ", menu=tk.Menu(menubar, tearoff=0))
        menubar.add_cascade(label="ВИД", menu=tk.Menu(menubar, tearoff=0))
        menubar.add_cascade(label="ДОБАВИТЬ СКРИПТ", menu=tk.Menu(menubar, tearoff=0))

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

        # Canvas and scrollbar for active script frames
        self.canvas = tk.Canvas(self.root)
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        self.scrollbar.pack(side="right", fill="y")

        # Right panel for saved scripts catalog
        right_frame = ttk.Frame(self.root)
        right_frame.pack(side="right", fill="y", padx=10, pady=5)

        # Saved scripts catalog
        saved_catalog_frame = ttk.LabelFrame(right_frame, text="КАТАЛОГ ВСЕХ СОХРАНЕННЫХ СКРИПТОВ", padding=10,
                                             width=300)
        saved_catalog_frame.pack(fill="both", expand=True)
        saved_catalog_frame.pack_propagate(False)  # Prevent frame from shrinking

        # Buttons for saved catalog
        saved_buttons_frame = ttk.Frame(saved_catalog_frame)
        saved_buttons_frame.pack(fill="x", pady=5)

        ttk.Button(saved_buttons_frame, text="Добавить в активные",
                   command=self.add_to_active).pack(side="left", padx=2)
        ttk.Button(saved_buttons_frame, text="Удалить из каталога",
                   command=self.delete_from_saved).pack(side="left", padx=2)

        # Listbox for saved scripts
        self.saved_listbox = tk.Listbox(saved_catalog_frame)
        self.saved_listbox.pack(fill="both", expand=True)

        # Bind double-click to add to active
        self.saved_listbox.bind("<Double-Button-1>", lambda e: self.add_to_active())

        # Active scripts catalog (read-only display)
        active_catalog_frame = ttk.LabelFrame(right_frame, text="АКТИВНЫЕ СКРИПТЫ (только отображение)", padding=10,
                                              width=300)
        active_catalog_frame.pack(fill="x", pady=(10, 0))

        self.active_listbox = tk.Listbox(active_catalog_frame, height=6)
        self.active_listbox.pack(fill="both", expand=True)

    def open_settings(self):
        dialog = SettingsDialog(self.root, self.settings)
        self.root.wait_window(dialog)
        self.save_settings()

    def load_settings(self):
        """Загружает настройки из JSON файла"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки настроек: {str(e)}")
            self.settings = {}

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
            scripts_to_save = []
            for script_info in self.saved_scripts:
                script_copy = script_info.copy()
                # Добавляем информацию о том, активен ли скрипт
                script_copy['is_active'] = any(
                    active_script['name'] == script_info['name']
                    for active_script in self.active_scripts
                )
                # Добавляем информацию о состоянии выполнения
                for script_data in self.script_frames:
                    if script_data['script_info']['name'] == script_info['name']:
                        script_copy['is_running'] = script_data['is_running']
                        script_copy['pid'] = script_data.get('pid')
                        break
                scripts_to_save.append(script_copy)

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
                        self.stop_script(script_data['script_info'])

                self.saved_scripts.clear()
                self.active_scripts.clear()
                self.script_frames.clear()

                # Очищаем интерфейс
                for widget in self.scrollable_frame.winfo_children():
                    widget.destroy()

                self.saved_listbox.delete(0, tk.END)
                self.active_listbox.delete(0, tk.END)

                # Загружаем скрипты из файла
                for script_info in loaded_scripts:
                    self.saved_scripts.append(script_info)
                    self.saved_listbox.insert(tk.END, script_info['name'])

                    # Восстанавливаем активные скрипты
                    if script_info.get('is_active', False):
                        self.active_scripts.append(script_info.copy())
                        self.create_script_frame(script_info)
                        self.active_listbox.insert(tk.END, script_info['name'])

                        # Восстанавливаем состояние выполнения
                        if script_info.get('is_running', False):
                            # Запускаем скрипт после небольшой задержки
                            self.root.after(1000, lambda s=script_info: self.start_script(s))

        except Exception as e:
            print(f"Ошибка загрузки скриптов: {str(e)}")

    def update_saved_listbox(self):
        """Обновляет список сохраненных скриптов"""
        self.saved_listbox.delete(0, tk.END)
        for script in self.saved_scripts:
            self.saved_listbox.insert(tk.END, script['name'])

    def update_active_listbox(self):
        """Обновляет список активных скриптов (только отображение)"""
        self.active_listbox.delete(0, tk.END)
        for script in self.active_scripts:
            self.active_listbox.insert(tk.END, script['name'])

    def add_to_active(self):
        """Добавляет выбранный скрипт из сохраненных в активные"""
        selection = self.saved_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        script_name = self.saved_listbox.get(index)

        # Находим скрипт в сохраненных
        script_to_add = None
        for script in self.saved_scripts:
            if script['name'] == script_name:
                script_to_add = script
                break

        if script_to_add:
            # Проверяем, не добавлен ли уже скрипт в активные
            for active_script in self.active_scripts:
                if active_script['name'] == script_to_add['name']:
                    return

            # Добавляем в активные
            self.active_scripts.append(script_to_add.copy())
            self.create_script_frame(script_to_add)
            self.update_active_listbox()
            self.save_scripts()

    def delete_from_saved(self):
        """Удаляет выбранный скрипт из сохраненных"""
        selection = self.saved_listbox.curselection()
        if not selection:
            return

        index = selection[0]
        script_name = self.saved_listbox.get(index)

        # Находим скрипт в сохраненных
        script_to_remove = None
        for script in self.saved_scripts:
            if script['name'] == script_name:
                script_to_remove = script
                break

        if script_to_remove:
            # Удаляем из активных, если он там есть
            for active_script in self.active_scripts:
                if active_script['name'] == script_name:
                    # Останавливаем скрипт если запущен
                    for script_data in self.script_frames:
                        if script_data['script_info']['name'] == script_name:
                            if script_data['is_running']:
                                self.stop_script(script_data['script_info'])
                            break

                    # Удаляем из активных
                    self.active_scripts.remove(active_script)
                    self.update_script_frames()
                    self.update_active_listbox()
                    break

            # Удаляем из сохраненных
            self.saved_scripts.remove(script_to_remove)
            self.update_saved_listbox()
            self.save_scripts()

    def update_script_frames(self):
        """Обновляет фреймы активных скриптов"""
        # Очищаем текущие фреймы
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        # Создаем фреймы заново
        self.script_frames.clear()
        for script_info in self.active_scripts:
            self.create_script_frame(script_info)

    def add_script(self):
        """Добавляет новый скрипт в оба каталога"""
        script_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
        if script_path:
            script_name = os.path.basename(script_path).replace('.py', '')

            # Используем интерпретатор по умолчанию из настроек, если он есть
            default_interpreter = self.settings.get('default_interpreter', sys.executable)

            script_info = {
                'name': script_name,
                'path': script_path,
                'interpreter': default_interpreter
            }

            # Проверяем, нет ли уже такого скрипта в сохраненных
            for saved_script in self.saved_scripts:
                if saved_script['name'] == script_name:
                    return

            # Добавляем в сохраненные и активные
            self.saved_scripts.append(script_info)
            self.active_scripts.append(script_info.copy())

            # Обновляем интерфейс
            self.create_script_frame(script_info)
            self.update_saved_listbox()
            self.update_active_listbox()

            # Сохраняем
            self.save_scripts()

    def create_script_frame(self, script_info):
        """Создает фрейм для активного скрипта"""
        frame = ttk.LabelFrame(self.scrollable_frame, text=script_info['name'], padding=10)
        frame.pack(fill="x", pady=5)

        # Controls
        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill="x")

        ttk.Button(controls_frame, text="Настройки",
                   command=lambda: self.configure_script(script_info)).pack(side="right", padx=2)
        ttk.Button(controls_frame, text="Удалить из активных",
                   command=lambda: self.delete_from_active(script_info)).pack(side="right", padx=2)
        ttk.Button(controls_frame, text="Стоп",
                   command=lambda: self.stop_script(script_info)).pack(side="right", padx=2)
        ttk.Button(controls_frame, text="Запуск",
                   command=lambda: self.start_script(script_info)).pack(side="right", padx=2)

        # Resource monitoring
        resources_frame = ttk.Frame(frame)
        resources_frame.pack(fill="x", pady=5)

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
            'script_info': script_info,
            'process': None,
            'pid': None,
            'cpu_var': cpu_var,
            'memory_var': memory_var,
            'cpu_label': cpu_label,
            'memory_label': memory_label,
            'is_running': False,
            'last_cpu_times': (0, 0),  # (user, system) время
            'last_check_time': time.time()
        }

        self.script_frames.append(script_frame_data)

    def delete_from_active(self, script_info):
        """Удаляет скрипт из активных (но оставляет в сохраненных)"""
        # Останавливаем скрипт если запущен
        for script_data in self.script_frames:
            if script_data['script_info'] == script_info:
                if script_data['is_running']:
                    self.stop_script(script_info)
                break

        # Удаляем из активных
        self.active_scripts.remove(script_info)
        self.update_script_frames()
        self.update_active_listbox()
        self.save_scripts()

    def configure_script(self, script_info):
        """Настройки скрипта"""
        config_window = tk.Toplevel(self.root)
        config_window.title("Настройки скрипта")
        config_window.geometry("400x300")
        config_window.resizable(False, False)

        main_frame = ttk.Frame(config_window, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text=f"Настройки для: {script_info['name']}").pack(pady=10)

        # Interpreter settings
        interpreter_frame = ttk.Frame(main_frame)
        interpreter_frame.pack(fill=tk.X, pady=5)

        ttk.Label(interpreter_frame, text="Интерпретатор:").pack(anchor=tk.W)

        interpreter_var = tk.StringVar(value=script_info['interpreter'])
        interpreter_entry = ttk.Entry(interpreter_frame, textvariable=interpreter_var, width=50)
        interpreter_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        def browse_interpreter():
            path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe"), ("All files", "*.*")])
            if path:
                interpreter_var.set(path)

        ttk.Button(interpreter_frame, text="Обзор", command=browse_interpreter).pack(side=tk.RIGHT)

        # Autostart setting
        autostart_frame = ttk.Frame(main_frame)
        autostart_frame.pack(fill=tk.X, pady=5)

        autostart_var = tk.BooleanVar(value=script_info.get('autostart', False))
        ttk.Checkbutton(autostart_frame, text="Запускать скрипт при старте программы",
                        variable=autostart_var).pack(anchor=tk.W)

        # Packages button
        ttk.Button(main_frame, text="Показать установленные пакеты",
                   command=lambda: self.show_script_packages(interpreter_var.get())).pack(anchor=tk.W, pady=5)

        # Buttons
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(fill=tk.X, pady=10)

        def save_config():
            script_info['interpreter'] = interpreter_var.get()
            script_info['autostart'] = autostart_var.get()

            # Обновляем в сохраненных скриптах
            for saved_script in self.saved_scripts:
                if saved_script['name'] == script_info['name']:
                    saved_script['interpreter'] = interpreter_var.get()
                    saved_script['autostart'] = autostart_var.get()
                    break

            config_window.destroy()
            self.save_scripts()

        ttk.Button(buttons_frame, text="Сохранить", command=save_config).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(buttons_frame, text="Отмена", command=config_window.destroy).pack(side=tk.RIGHT)

    def show_script_packages(self, interpreter):
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
                packages_window = tk.Toplevel(self.root)
                packages_window.title("Установленные пакеты")
                packages_window.geometry("600x400")

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

    def start_script(self, script_info):
        for script_data in self.script_frames:
            if script_data['script_info'] == script_info:
                try:
                    if not os.path.exists(script_info['path']):
                        messagebox.showerror("Ошибка", f"Файл {script_info['path']} не найден")
                        return

                    # Запускаем процесс с перехватом вывода
                    script_data['process'] = subprocess.Popen([
                        script_info['interpreter'],
                        script_info['path']
                    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                    script_data['pid'] = script_data['process'].pid
                    script_data['is_running'] = True

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
                    self.show_error_dialog(script_info['name'], error_msg)
                break

    def monitor_script_output(self, script_data):
        """Мониторинг вывода скрипта для перехвата ошибок"""
        process = script_data['process']

        # Читаем stderr в реальном времени
        while script_data['is_running'] and process.poll() is None:
            try:
                # Читаем строку ошибки
                error_line = process.stderr.readline()
                if error_line and error_line.strip():
                    # Показываем диалог с ошибкой в главном потоке
                    self.root.after(0, lambda: self.show_error_dialog(
                        script_data['script_info']['name'],
                        f"Ошибка выполнения:\n{error_line}"
                    ))
            except:
                break

        # После завершения процесса проверяем код возврата
        if process.poll() is not None and process.returncode != 0:
            try:
                # Получаем оставшиеся ошибки
                _, stderr = process.communicate(timeout=1)
                if stderr and stderr.strip():
                    self.root.after(0, lambda: self.show_error_dialog(
                        script_data['script_info']['name'],
                        f"Процесс завершился с ошибкой (код: {process.returncode}):\n{stderr}"
                    ))
            except:
                pass

    def stop_script(self, script_info):
        for script_data in self.script_frames:
            if script_data['script_info'] == script_info and script_data['process']:
                try:
                    script_data['process'].terminate()
                    script_data['process'].wait(timeout=5)
                except:
                    try:
                        script_data['process'].kill()
                    except:
                        pass
                script_data['process'] = None
                script_data['pid'] = None
                script_data['is_running'] = False
                script_data['cpu_var'].set(0)
                script_data['memory_var'].set(0)
                script_data['cpu_label'].config(text="0%")
                script_data['memory_label'].config(text="0%")
                break

    def calculate_process_cpu_usage(self, script_data):
        """Правильный расчет CPU использования для процесса"""
        if not script_data['is_running'] or not script_data['pid']:
            return 0, 0

        try:
            process = psutil.Process(script_data['pid'])
            current_time = time.time()
            time_delta = current_time - script_data['last_check_time']

            if time_delta > 0:
                # Получаем текущее время CPU
                cpu_times = process.cpu_times()
                current_cpu_times = (cpu_times.user, cpu_times.system)

                # Вычисляем разницу
                prev_user, prev_system = script_data['last_cpu_times']
                cpu_delta = (current_cpu_times[0] - prev_user) + (current_cpu_times[1] - prev_system)

                # CPU usage в процентах (относительно времени и количества ядер)
                cpu_percent = (cpu_delta / time_delta) * 100

                # Обновляем данные для следующего расчета
                script_data['last_cpu_times'] = current_cpu_times
                script_data['last_check_time'] = current_time

                # Получаем использование памяти
                memory_info = process.memory_info()
                memory_percent = (memory_info.rss / psutil.virtual_memory().total) * 100

                return min(100, cpu_percent), memory_percent

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            script_data['is_running'] = False
            script_data['process'] = None

        return 0, 0

    def start_monitoring(self):
        def monitor():
            total_cpu = 0
            total_memory = 0

            # Мониторинг индивидуальных скриптов
            for script_data in self.script_frames:
                if script_data['is_running']:
                    cpu_usage, memory_usage = self.calculate_process_cpu_usage(script_data)

                    # Обновляем интерфейс
                    script_data['cpu_var'].set(int(cpu_usage))
                    script_data['memory_var'].set(int(memory_usage))
                    script_data['cpu_label'].config(text=f"{cpu_usage:.1f}%")
                    script_data['memory_label'].config(text=f"{memory_usage:.1f}%")

                    total_cpu += cpu_usage
                    total_memory += memory_usage
                else:
                    script_data['cpu_var'].set(0)
                    script_data['memory_var'].set(0)
                    script_data['cpu_label'].config(text="0%")
                    script_data['memory_label'].config(text="0%")

            # Общая нагрузка (сумма всех процессов)
            # Ограничиваем общую нагрузку 100% для CPU
            total_cpu = min(total_cpu, 100)
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