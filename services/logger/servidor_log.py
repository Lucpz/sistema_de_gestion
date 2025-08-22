import socket
import threading
import json
import datetime
import os
from typing import Dict, Any

class ServidorLog:
    def __init__(self, host='localhost', puerto=8888):
        self.host = host
        self.puerto = puerto
        self.socket_servidor = None
        self.ejecutando = False
        
        log_dir = os.path.join('services', 'logger')
        os.makedirs(log_dir, exist_ok=True)
        
        self.archivo_log = os.path.join(log_dir, 'servidor_logs.txt')
        self.clientes_conectados = []

        if not os.path.exists(self.archivo_log):
            with open(self.archivo_log, 'w', encoding='utf-8') as f:
                f.write(f"=== SERVIDOR DE LOGS INICIADO ===\n")
                f.write(f"Fecha de inicio: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")

    def iniciar_servidor(self):
        try:
            self.socket_servidor = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_servidor.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket_servidor.bind((self.host, self.puerto))
            self.socket_servidor.listen(5)
            self.ejecutando = True
            
            print(f"🟢 Servidor de logs iniciado en {self.host}:{self.puerto}")
            self.escribir_log_servidor(f"Servidor iniciado en {self.host}:{self.puerto}")
            
            while self.ejecutando:
                try:
                    cliente_socket, direccion_cliente = self.socket_servidor.accept()
                    print(f"🔵 Cliente conectado desde: {direccion_cliente}")
                    self.escribir_log_servidor(f"Cliente conectado: {direccion_cliente}")
                    
                    hilo_cliente = threading.Thread(
                        target=self.manejar_cliente, 
                        args=(cliente_socket, direccion_cliente)
                    )
                    hilo_cliente.daemon = True
                    hilo_cliente.start()
                    
                except socket.error as e:
                    if self.ejecutando:
                        print(f"❌ Error al aceptar conexión: {e}")
                        self.escribir_log_servidor(f"Error al aceptar conexión: {e}")
                        
        except Exception as e:
            print(f"❌ Error al iniciar servidor: {e}")
            self.escribir_log_servidor(f"Error al iniciar servidor: {e}")

    def manejar_cliente(self, cliente_socket, direccion_cliente):
        cliente_info = f"{direccion_cliente[0]}:{direccion_cliente[1]}"
        self.clientes_conectados.append(cliente_info)
        
        try:
            while self.ejecutando:
                datos = cliente_socket.recv(1024).decode('utf-8')
                
                if not datos:
                    break
                
                try:
                    mensaje_json = json.loads(datos)
                    self.procesar_mensaje_cliente(mensaje_json, cliente_info)
                    
                    respuesta = {
                        "status": "ok",
                        "mensaje": "Log recibido correctamente",
                        "timestamp": datetime.datetime.now().isoformat()
                    }
                    cliente_socket.send(json.dumps(respuesta).encode('utf-8'))
                    
                except json.JSONDecodeError:
                    self.procesar_mensaje_texto(datos, cliente_info)
                    cliente_socket.send(b"Mensaje recibido")
                
        except ConnectionResetError:
            print(f"🔴 Cliente {cliente_info} desconectado inesperadamente")
            self.escribir_log_servidor(f"Cliente {cliente_info} desconectado inesperadamente")
        except Exception as e:
            print(f"❌ Error manejando cliente {cliente_info}: {e}")
            self.escribir_log_servidor(f"Error manejando cliente {cliente_info}: {e}")
        finally:
            self.clientes_conectados.remove(cliente_info)
            cliente_socket.close()
            print(f"🔴 Cliente {cliente_info} desconectado")
            self.escribir_log_servidor(f"Cliente {cliente_info} desconectado")

    def procesar_mensaje_cliente(self, mensaje: Dict[str, Any], cliente_info: str):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        tipo_operacion = mensaje.get('operacion', 'N/A')
        usuario = mensaje.get('usuario', 'N/A')
        detalles = mensaje.get('detalles', {})
        nivel = mensaje.get('nivel', 'INFO')
        
        entrada_log = (
            f"[{timestamp}] [{nivel}] Cliente: {cliente_info}\n"
            f"  Operación: {tipo_operacion}\n"
            f"  Usuario: {usuario}\n"
        )
        
        if detalles:
            entrada_log += "  Detalles:\n"
            for clave, valor in detalles.items():
                entrada_log += f"    {clave}: {valor}\n"
        
        entrada_log += "-" * 60 + "\n"
        
        with open(self.archivo_log, 'a', encoding='utf-8') as f:
            f.write(entrada_log)
        
        print(f"📝 Log recibido de {cliente_info}: {tipo_operacion}")

    def procesar_mensaje_texto(self, mensaje: str, cliente_info: str):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        entrada_log = (
            f"[{timestamp}] [TEXT] Cliente: {cliente_info}\n"
            f"  Mensaje: {mensaje.strip()}\n"
            f"{'-' * 60}\n"
        )
        
        with open(self.archivo_log, 'a', encoding='utf-8') as f:
            f.write(entrada_log)
        
        print(f"📝 Mensaje texto de {cliente_info}: {mensaje.strip()[:50]}...")

    def escribir_log_servidor(self, mensaje: str):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        entrada_log = f"[{timestamp}] [SERVIDOR] {mensaje}\n"
        
        with open(self.archivo_log, 'a', encoding='utf-8') as f:
            f.write(entrada_log)

    def obtener_estadisticas(self):
        return {
            "clientes_conectados": len(self.clientes_conectados),
            "lista_clientes": self.clientes_conectados,
            "servidor_activo": self.ejecutando,
            "archivo_log": self.archivo_log
        }

    def detener_servidor(self):
        print("🔴 Deteniendo servidor...")
        self.escribir_log_servidor("Servidor detenido por el usuario")
        self.ejecutando = False
        
        if self.socket_servidor:
            self.socket_servidor.close()
        
        print("🔴 Servidor detenido")

def main():
    servidor = ServidorLog()
    
    try:
        hilo_servidor = threading.Thread(target=servidor.iniciar_servidor)
        hilo_servidor.daemon = True
        hilo_servidor.start()
        
        print("\n" + "="*50)
        print("🖥️  SERVIDOR DE LOGS ACTIVO")
        print("="*50)
        print("Comandos disponibles:")
        print("  'stats' - Ver estadísticas")
        print("  'clientes' - Ver clientes conectados")
        print("  'log' - Ver últimas entradas del log")
        print("  'quit' - Detener servidor")
        print("="*50 + "\n")
        
        while True:
            comando = input("Servidor> ").strip().lower()
            
            if comando == 'quit':
                servidor.detener_servidor()
                break
            elif comando == 'stats':
                stats = servidor.obtener_estadisticas()
                print(f"\n📊 ESTADÍSTICAS:")
                print(f"  Clientes conectados: {stats['clientes_conectados']}")
                print(f"  Servidor activo: {stats['servidor_activo']}")
                print(f"  Archivo de log: {stats['archivo_log']}")
            elif comando == 'clientes':
                stats = servidor.obtener_estadisticas()
                print(f"\n👥 CLIENTES CONECTADOS ({len(stats['lista_clientes'])}):")
                for cliente in stats['lista_clientes']:
                    print(f"  • {cliente}")
            elif comando == 'log':
                try:
                    with open(servidor.archivo_log, 'r', encoding='utf-8') as f:
                        lineas = f.readlines()
                        print(f"\n📋 ÚLTIMAS 10 ENTRADAS DEL LOG:")
                        print("".join(lineas[-20:]))  # Mostrar últimas 20 líneas
                except FileNotFoundError:
                    print("❌ Archivo de log no encontrado")
            elif comando == 'help':
                print("\n📋 COMANDOS DISPONIBLES:")
                print("  stats    - Ver estadísticas del servidor")
                print("  clientes - Ver clientes conectados")
                print("  log      - Ver últimas entradas del log")
                print("  help     - Mostrar esta ayuda")
                print("  quit     - Detener servidor")
            else:
                print("❌ Comando no reconocido. Usa 'help' para ver comandos disponibles.")
    
    except KeyboardInterrupt:
        print("\n🔴 Interrupción detectada. Deteniendo servidor...")
        servidor.detener_servidor()

if __name__ == "__main__":
    main()