import flet as ft
from controller.controlador import ControladorStock
import threading
import time
import sys
import os

def iniciar_servidor_logs():
    try:
        from services.logger.servidor_log import ServidorLog

        print("🟡Iniciando servidor de logs...")
        servidor = ServidorLog()

        hilo_servidor = threading.Thread(target=servidor.iniciar_servidor)
        hilo_servidor.daemon = True 
        hilo_servidor.start()

        time.sleep(2)
        print("🟢 Servidor de logs iniciado correctamente")

        return servidor
    
    except ImportError as e:
        print(f"⚠️ No se pudo iniciar el servidor de logs: {e}")
        print("⚠️ La aplicación continuará sin servidor de logs")
        return None
    
def main(page: ft.Page):
    page.title = "Sistema de Gestión"
    page.window_width = 1000
    page.window_height = 700
    page.window_resizable = True
    
    controlador = ControladorStock(page)
    controlador.iniciar()

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 INICIANDO SISTEMA DE GESTIÓN")
    print("=" * 60)

    servidor = iniciar_servidor_logs()
    
    try:
        ft.app(target=main)
    except KeyboardInterrupt:
        print("\n🔴 Cerrando aplicación...")
        if servidor:
            servidor.detener_servidor()
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error en la aplicación: {e}")
        if servidor:
            servidor.detener_servidor()
        sys.exit(1)