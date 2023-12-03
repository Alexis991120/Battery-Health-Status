import os
import subprocess
import re
import ctypes
from win10toast import ToastNotifier
import pystray
from PIL import Image
import requests

# Importar módulo psutil
try:
    import psutil
except ImportError:
    print("Por favor, instale las dependencias necesarias. Puede hacerlo ejecutando:")
    print("pip install psutil")
    exit(1)

# URL pública del archivo en Google Drive
drive_url = "https://drive.google.com/uc?id=1w-NoWcc3fW7eQaRKmJbr5kX2hECy440p"

# Nombre del archivo de icono
icon_file = "bateria.ico"

# Nombre de la carpeta en C:\ donde se almacenará el informe
folder_name = "Battery Health Status"

# Crear la carpeta si no existe
folder_path = os.path.join("C:\\", folder_name)
os.makedirs(folder_path, exist_ok=True)

# Cambiar al directorio de la nueva carpeta
os.chdir(folder_path)

# Función para descargar el archivo desde Google Drive
def download_file_from_google_drive(id, destination):
    # Descargar el archivo desde Google Drive
    URL = "https://drive.google.com/uc?id=" + id
    response = requests.get(URL)
    with open(destination, "wb") as f:
        f.write(response.content)

# Descargar el archivo desde Google Drive solo si no está presente
if not os.path.exists(icon_file):
    file_id = drive_url.split("=")[-1]
    download_file_from_google_drive(file_id, icon_file)

try:
    # Generar reporte de batería en la nueva carpeta
    result = subprocess.run(["powercfg", "/batteryreport", "/output", "battery-report.html"], capture_output=True)
except PermissionError:
    ctypes.windll.user32.MessageBoxW(0, "Este script requiere permisos de administrador para ejecutarse.", "Error", 0x10)
    exit(1)

# Leer reporte HTML desde la nueva carpeta
report_path = os.path.join(folder_path, "battery-report.html")

with open(report_path) as f:
    report = f.read()

# Obtener capacidades
design_capacity = re.search(r"DESIGN CAPACITY</span></td><td>([\d|,]*) mWh", report).group(1)
design_capacity = int(design_capacity.replace(",", ""))
full_charge_capacity = re.search(r"FULL CHARGE CAPACITY</span></td><td>([\d|,]*) mWh", report).group(1)
full_charge_capacity = int(full_charge_capacity.replace(",", ""))
# Calcular desgaste
percent_wear = full_charge_capacity / design_capacity * 100
# Configurar icono
image = Image.open(icon_file)
toaster = ToastNotifier()

# Función para mostrar información de la batería
def show_info(icon, item):
    battery = psutil.sensors_battery()
    percent = battery.percent

    toaster.show_toast("Batería",
                       f"Nivel: {percent}% - Vida util: {percent_wear:.2f}%",
                       icon_path=icon_file,
                       duration=5)

# Función para salir del programa
def exit_program(icon, item):
    icon.stop()
    global running
    running = False

running = True

# Bucle principal
while running:
    menu_items = [
        pystray.MenuItem(text="Mostrar Info", action=show_info, default=True),
        pystray.MenuItem('Salir', exit_program)
    ]

    menu = pystray.Menu(*menu_items)
    icon = pystray.Icon("Batería", image, menu=menu, title="Battery Health Status")

    icon.run()
