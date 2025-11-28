import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import psutil
import os
import sys
from threading import Thread
import time


class ScriptManagerTkinter:
    def __init__(self, root):
        self.root = root
        self.root.title("Script Manager")
        self.root.geometry("1000x700")

        self.scripts = []
        self.script_frames = []
        self.process_cpu_usage = {}  # Для отслеживания использования CPU процессами

        self.setup_ui()
        self.start_monitoring()

    def setup_ui(self):
        # Main menu (simplified)
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="ФАЙЛ", menu=file_menu)
        file_menu.add_command(label="Добавить скрипт", command=self.add_script)

        menubar.add_cascade(label="ГЛАВНАЯ", menu=tk.Menu(menubar, tearoff=0))
        menubar.add_cascade(label="ВИД", menu=tk.Menu(menubar, tearoff=0))
        menubar.add_cascade(label="ДОБАВИТЬ СКРИПТ", menu=tk.Menu(menubar, tearoff=0))

        # System monitoring - СУММАРНАЯ нагрузка всех процессов
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

        # Scripts area
        scripts_label = ttk.Label(self.root, text="Активные скрипты:", font=("Arial", 12, "bold"))
        scripts_label.pack(anchor="w", padx=10, pady=(10, 0))

        # Canvas and scrollbar for script frames
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

        # Script catalog
        catalog_frame = ttk.LabelFrame(self.root, text="КАТАЛОГ ВСЕХ СКРИПТОВ", padding=10)
        catalog_frame.pack(fill="x", padx=10, pady=5)

        self.script_listbox = tk.Listbox(catalog_frame)
        self.script_listbox.pack(fill="both", expand=True)

    def add_script(self):
        script_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
        if script_path:
            script_name = os.path.basename(script_path).replace('.py', '')
            script_info = {
                'name': script_name,
                'path': script_path,
                'interpreter': sys.executable
            }
            self.scripts.append(script_info)
            self.create_script_frame(script_info)
            self.script_listbox.insert(tk.END, script_name)

    def create_script_frame(self, script_info):
        frame = ttk.LabelFrame(self.scrollable_frame, text=script_info['name'], padding=10)
        frame.pack(fill="x", pady=5)

        # Controls
        controls_frame = ttk.Frame(frame)
        controls_frame.pack(fill="x")

        ttk.Button(controls_frame, text="Настройки",
                   command=lambda: self.configure_script(script_info)).pack(side="right", padx=2)
        ttk.Button(controls_frame, text="Стоп",
                   command=lambda: self.stop_script(script_info)).pack(side="right", padx=2)
        ttk.Button(controls_frame, text="Пауза",
                   command=lambda: self.pause_script(script_info)).pack(side="right", padx=2)
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
            'is_paused': False,
            'last_cpu_times': 0,  # Для расчета CPU использования
            'last_check_time': time.time()
        }

        self.script_frames.append(script_frame_data)

    def configure_script(self, script_info):
        # Диалог настройки интерпретатора
        config_window = tk.Toplevel(self.root)
        config_window.title("Настройки скрипта")
        config_window.geometry("400x200")

        ttk.Label(config_window, text=f"Настройки для: {script_info['name']}").pack(pady=10)

        interpreter_frame = ttk.Frame(config_window)
        interpreter_frame.pack(fill="x", padx=20, pady=10)

        ttk.Label(interpreter_frame, text="Интерпретатор:").pack(anchor="w")

        interpreter_var = tk.StringVar(value=script_info['interpreter'])
        interpreter_entry = ttk.Entry(interpreter_frame, textvariable=interpreter_var, width=50)
        interpreter_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))

        def browse_interpreter():
            path = filedialog.askopenfilename(filetypes=[("Executable files", "*.exe"), ("All files", "*.*")])
            if path:
                interpreter_var.set(path)

        ttk.Button(interpreter_frame, text="Обзор", command=browse_interpreter).pack(side="right")

        def save_config():
            script_info['interpreter'] = interpreter_var.get()
            config_window.destroy()
            messagebox.showinfo("Успех", "Настройки сохранены")

        ttk.Button(config_window, text="Сохранить", command=save_config).pack(pady=20)

    def start_script(self, script_info):
        for script_data in self.script_frames:
            if script_data['script_info'] == script_info:
                try:
                    if not os.path.exists(script_info['path']):
                        messagebox.showerror("Ошибка", f"Файл {script_info['path']} не найден")
                        return

                    script_data['process'] = subprocess.Popen([
                        script_info['interpreter'],
                        script_info['path']
                    ])
                    script_data['pid'] = script_data['process'].pid
                    script_data['is_running'] = True
                    script_data['is_paused'] = False
                    script_data['last_cpu_times'] = 0
                    script_data['last_check_time'] = time.time()

                    # Инициализация отслеживания CPU
                    try:
                        process = psutil.Process(script_data['pid'])
                        script_data['last_cpu_times'] = process.cpu_times().user + process.cpu_times().system
                    except:
                        pass

                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось запустить скрипт: {str(e)}")
                break

    def pause_script(self, script_info):
        for script_data in self.script_frames:
            if script_data['script_info'] == script_info and script_data['process']:
                try:
                    if not script_data['is_paused']:
                        script_data['process'].suspend()
                        script_data['is_paused'] = True
                    else:
                        script_data['process'].resume()
                        script_data['is_paused'] = False
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось изменить состояние: {str(e)}")
                break

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
                script_data['is_paused'] = False
                script_data['cpu_var'].set(0)
                script_data['memory_var'].set(0)
                script_data['cpu_label'].config(text="0%")
                script_data['memory_label'].config(text="0%")
                break

    def calculate_process_cpu_usage(self, script_data):
        """Правильный расчет CPU использования для процесса"""
        if not script_data['is_running'] or script_data['is_paused'] or not script_data['pid']:
            return 0

        try:
            process = psutil.Process(script_data['pid'])
            current_time = time.time()
            time_delta = current_time - script_data['last_check_time']

            if time_delta > 0:
                current_cpu_times = process.cpu_times().user + process.cpu_times().system
                cpu_delta = current_cpu_times - script_data['last_cpu_times']

                # CPU usage в процентах
                cpu_percent = (cpu_delta / time_delta) * 100

                script_data['last_cpu_times'] = current_cpu_times
                script_data['last_check_time'] = current_time

                return min(100, max(0, cpu_percent))

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            script_data['is_running'] = False
            script_data['process'] = None

        return 0

    def start_monitoring(self):
        def monitor():
            while True:
                total_cpu = 0
                total_memory = 0
                active_processes = 0

                # Мониторинг индивидуальных скриптов
                for script_data in self.script_frames:
                    if script_data['is_running'] and not script_data['is_paused']:
                        # CPU usage
                        cpu_usage = self.calculate_process_cpu_usage(script_data)
                        script_data['cpu_var'].set(int(cpu_usage))
                        script_data['cpu_label'].config(text=f"{cpu_usage:.1f}%")

                        # Memory usage
                        try:
                            if script_data['pid']:
                                process = psutil.Process(script_data['pid'])
                                memory_percent = (process.memory_info().rss / psutil.virtual_memory().total) * 100
                                script_data['memory_var'].set(int(memory_percent))
                                script_data['memory_label'].config(text=f"{memory_percent:.1f}%")

                                total_cpu += cpu_usage
                                total_memory += memory_percent
                                active_processes += 1
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            script_data['is_running'] = False
                            script_data['process'] = None
                    else:
                        script_data['cpu_var'].set(0)
                        script_data['memory_var'].set(0)
                        script_data['cpu_label'].config(text="0%")
                        script_data['memory_label'].config(text="0%")

                # Общая нагрузка (сумма всех процессов)
                self.total_cpu_var.set(int(total_cpu))
                self.total_memory_var.set(int(total_memory))
                self.total_cpu_label.config(text=f"{total_cpu:.1f}%")
                self.total_memory_label.config(text=f"{total_memory:.1f}%")

                time.sleep(1)

        monitor_thread = Thread(target=monitor, daemon=True)
        monitor_thread.start()


if __name__ == "__main__":
    root = tk.Tk()
    app = ScriptManagerTkinter(root)
    root.mainloop()