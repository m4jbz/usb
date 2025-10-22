import psutil, os
from pathlib import Path

def encontrar_usb():
    """Busca la primera unidad USB (extraíble) conectada."""
    particiones = psutil.disk_partitions()
    for p in particiones:
        # La opción 'removable' es un buen indicador de una USB
        if 'removable' in p.opts:
            # p.mountpoint es la letra de la unidad (ej. "E:\")
            return Path(p.mountpoint)
    return None

# --- Script principal ---
ruta_usb = encontrar_usb()

if ruta_usb:
    print(f"USB detectada en: {ruta_usb}")
    
    # Ahora puedes acceder a un directorio dentro de ella
    ruta_directorio = ruta_usb / "Baul"
    
    if ruta_directorio.exists():
        print(f"Contenido de '{ruta_directorio}':")
        for item in ruta_directorio.iterdir():
            print(f"  - {item.name}")
    else:
        ruta_directorio.mkdir()
        
else:
    print("No se detectó ninguna unidad USB.")