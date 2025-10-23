import os
import subprocess
import customtkinter
import pywinstyles
import sys
from pathlib import Path

print("Iniciando el proceso de construcción del Baúl Seguro...")

try:
    # 1. Encontrar las rutas de los paquetes necesarios
    ctk_path = Path(customtkinter.__file__).parent
    ctk_assets_path = ctk_path / "assets"
    print(f"Ruta de assets de CustomTkinter: {ctk_assets_path}")

    pws_path = Path(pywinstyles.__file__).parent
    print(f"Ruta de PyWinStyles: {pws_path}")

    # 2. Definir el separador de rutas (';' en Windows)
    path_sep = os.pathsep

    # 3. Construir el comando de PyInstaller
    # --onedir: Crea una carpeta (más fiable que --onefile para apps complejas)
    # --windowed: Oculta la consola de comandos al ejecutar el .exe
    # --add-data: Le dice a PyInstaller que incluya las carpetas de 'assets'
    # --hidden-import: Fuerza la inclusión de módulos que PyInstaller no ve
    command = [
        'pyinstaller',
        '--noconfirm',
        '--onedir',
        '--windowed',
        '--name=BaulSeguro',
        f'--add-data={ctk_assets_path}{path_sep}customtkinter/assets',
        f'--add-data={pws_path}{path_sep}pywinstyles',
        '--hidden-import=watchdog.observers.api',
        'run.py'  # Tu script principal
    ]

    print("\nEjecutando el siguiente comando:")
    print(" ".join(command))
    print("\nEsto puede tardar varios minutos...")

    # 4. Ejecutar el comando
    subprocess.run(" ".join(command), shell=True, check=True)

    print("\n" + "="*50)
    print("¡ÉXITO! Construcción completada.")
    print(f"Tu aplicación ejecutable está en la carpeta:")
    print(f"{Path.cwd() / 'dist' / 'BaulSeguro'}")
    print("="*50)

except subprocess.CalledProcessError as e:
    print("\n" + "="*50)
    print("¡ERROR! PyInstaller falló.")
    print(f"Error: {e}")
    print("="*50)
except FileNotFoundError:
    print("\n" + "="*50)
    print("¡ERROR! No se encontró PyInstaller.")
    print("Asegúrate de haberlo instalado con: pip install pyinstaller")
    print("="*50)
except Exception as e:
    print(f"\n¡Un error inesperado ocurrió!: {e}")
