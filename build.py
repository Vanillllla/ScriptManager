import os
import sys
from PyInstaller.__main__ import run

# Добавляем пути для импорта модулей
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    opts = [
        'main.py',
        '--name=Python Script Manager (PSM)',
        '--onefile',
        '--windowed',
        '--icon=icon.ico',  # Если есть иконка
        '--hidden-import=pystray',
        '--hidden-import=PIL',
        '--hidden-import=PIL.Image',
        '--hidden-import=PIL.ImageDraw',
        '--hidden-import=win32com',
        '--hidden-import=win32com.client',
        '--hidden-import=winshell',
        '--hidden-import=psutil',
        '--collect-all=pystray',
        '--collect-all=PIL',
        '--noconfirm',
        '--clean'
    ]

    run(opts)