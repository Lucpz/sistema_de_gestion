import socket
import json
import datetime
import threading
import time
from typing import Dict, Any, Optional

class ClienteLog:
    def __init__(self, host='localhost', puerto=8888, nombre_cliente='Cliente-Stock'):
        self.host = host
        self.puerto = puerto
        self.nombre_cliente = nombre_cliente
        self.socket_cliente = None
        self.conectado = False
        self.auto_reconectar = True
        self.intervalo_heartbeat = 30
    
    def conectar(self) -> bool:
        try:
            self.socket_cliente = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket_cliente.connect((self.host, self.puerto))
            self.conectado = True
            
            print(f"🟢 Conectado al servidor de logs en {self.host}:{self.puerto}")
            
            self.enviar_log({
                "operacion": "CONEXION_INICIAL",
                "usuario": "SISTEMA",
                "nivel": "INFO",
                "detalles": {
                    "cliente": self.nombre_cliente,
                    "timestamp_conexion": datetime.datetime.now().isoformat()
                }
            })
            
            if self.auto_reconectar:
                hilo_heartbeat = threading.Thread(target=self._heartbeat)
                hilo_heartbeat.daemon = True
                hilo_heartbeat.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error al conectar: {e}")
            self.conectado = False
            return False
    
    def _heartbeat(self):
        while self.conectado and self.auto_reconectar:
            time.sleep(self.intervalo_heartbeat)
            if self.conectado:
                try:
                    self.enviar_log({
                        "operacion": "HEARTBEAT",
                        "usuario": "SISTEMA",
                        "nivel": "DEBUG",
                        "detalles": {
                            "cliente": self.nombre_cliente,
                            "timestamp": datetime.datetime.now().isoformat()
                        }
                    })
                except:
                    if self.auto_reconectar:
                        self._intentar_reconexion()
    
    def _intentar_reconexion(self):
        print("🔄 Intentando reconectar al servidor...")
        self.conectado = False
        
        intentos = 0
        max_intentos = 5
        
        while intentos < max_intentos and self.auto_reconectar:
            time.sleep(2 ** intentos)
            intentos += 1
            
            if self.conectar():
                print("🟢 Reconexión exitosa")
                return True
            else:
                print(f"🔄 Intento {intentos}/{max_intentos} fallido")
        
        print("❌ No se pudo reconectar al servidor")
        return False
    
    def enviar_log(self, datos: Dict[str, Any]) -> bool:
        if not self.conectado or not self.socket_cliente:
            print("❌ No hay conexión con el servidor")
            return False
        
        try:
            datos['timestamp'] = datetime.datetime.now().isoformat()
            datos['cliente'] = self.nombre_cliente
            
            mensaje_json = json.dumps(datos, ensure_ascii=False)
            self.socket_cliente.send(mensaje_json.encode('utf-8'))
            
            respuesta = self.socket_cliente.recv(1024).decode('utf-8')
            
            try:
                resp_json = json.loads(respuesta)
                if resp_json.get('status') == 'ok':
                    return True
                else:
                    print(f"⚠️ Respuesta del servidor: {respuesta}")
                    return False
            except json.JSONDecodeError:
                if respuesta:
                    return True
                else:
                    return False
                    
        except Exception as e:
            print(f"❌ Error enviando log: {e}")
            self.conectado = False
            if self.auto_reconectar:
                self._intentar_reconexion()
            return False
    
    def enviar_mensaje_texto(self, mensaje: str) -> bool:
        if not self.conectado or not self.socket_cliente:
            print("❌ No hay conexión con el servidor")
            return False
        
        try:
            self.socket_cliente.send(mensaje.encode('utf-8'))
            respuesta = self.socket_cliente.recv(1024).decode('utf-8')
            return True if respuesta else False
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            self.conectado = False
            return False
    
    def log_operacion_stock(self, operacion: str, usuario: str, detalles: Dict[str, Any], nivel: str = "INFO"):
        return self.enviar_log({
            "operacion": f"STOCK_{operacion}",
            "usuario": usuario,
            "nivel": nivel,
            "detalles": detalles
        })
    
    def log_venta(self, numero_venta: str, cliente_venta: str, vendedor: str, total: float, productos: list):
        return self.enviar_log({
            "operacion": "VENTA_REALIZADA",
            "usuario": vendedor,
            "nivel": "INFO",
            "detalles": {
                "numero_venta": numero_venta,
                "cliente": cliente_venta,
                "total": total,
                "cantidad_productos": len(productos),
                "productos": productos
            }
        })
    
    def log_error(self, error: str, contexto: str = "", usuario: str = "SISTEMA"):
        return self.enviar_log({
            "operacion": "ERROR",
            "usuario": usuario,
            "nivel": "ERROR",
            "detalles": {
                "error": error,
                "contexto": contexto,
                "timestamp_error": datetime.datetime.now().isoformat()
            }
        })
    
    def desconectar(self):
        if self.conectado:
            try:
                self.enviar_log({
                    "operacion": "DESCONEXION",
                    "usuario": "SISTEMA",
                    "nivel": "INFO",
                    "detalles": {
                        "cliente": self.nombre_cliente,
                        "motivo": "Desconexión solicitada por cliente"
                    }
                })
            except:
                pass
        
        self.conectado = False
        self.auto_reconectar = False
        
        if self.socket_cliente:
            self.socket_cliente.close()
            self.socket_cliente = None
        
        print("🔴 Desconectado del servidor de logs")

class LoggerCliente:
    _instancia = None
    _cliente_log = None
    
    def __new__(cls):
        if cls._instancia is None:
            cls._instancia = super(LoggerCliente, cls).__new__(cls)
            cls._cliente_log = ClienteLog()
        return cls._instancia
    
    def conectar(self):
        """Conectar al servidor de logs"""
        return self._cliente_log.conectar()
    
    def log_operacion_stock(self, operacion: str, usuario: str, detalles: Dict[str, Any], nivel: str = "INFO"):
        """Log para operaciones de stock"""
        if self._cliente_log.conectado:
            return self._cliente_log.log_operacion_stock(operacion, usuario, detalles, nivel)
        return False
    
    def log_venta(self, numero_venta: str, cliente_venta: str, vendedor: str, total: float, productos: list):
        """Log para ventas"""
        if self._cliente_log.conectado:
            return self._cliente_log.log_venta(numero_venta, cliente_venta, vendedor, total, productos)
        return False
    
    def log_error(self, error: str, contexto: str = "", usuario: str = "SISTEMA"):
        """Log para errores"""
        if self._cliente_log.conectado:
            return self._cliente_log.log_error(error, contexto, usuario)
        return False
    
    def desconectar(self):
        """Desconectar del servidor"""
        if self._cliente_log:
            self._cliente_log.desconectar()

def main():
    """Función principal para probar el cliente"""
    cliente = ClienteLog(nombre_cliente="Cliente-Test")
    
    if not cliente.conectar():
        print("❌ No se pudo conectar al servidor")
        return
    
    print("\n" + "="*50)
    print("📱 CLIENTE DE LOGS ACTIVO")
    print("="*50)
    print("Comandos disponibles:")
    print("  'stock' - Simular operación de stock")
    print("  'venta' - Simular venta")
    print("  'error' - Simular error")
    print("  'mensaje' - Enviar mensaje personalizado")
    print("  'quit' - Desconectar")
    print("="*50 + "\n")
    
    try:
        while cliente.conectado:
            comando = input("Cliente> ").strip().lower()
            
            if comando == 'quit':
                break
            elif comando == 'stock':
                cliente.log_operacion_stock(
                    operacion="AGREGAR_PRODUCTO",
                    usuario="admin",
                    detalles={
                        "producto_id": 123,
                        "nombre": "Producto Test",
                        "cantidad": 50,
                        "precio": 25.99
                    }
                )
                print("✅ Log de stock enviado")
            elif comando == 'venta':
                cliente.log_venta(
                    numero_venta="V20240804123456",
                    cliente_venta="Juan Pérez",
                    vendedor="admin",
                    total=75.50,
                    productos=[
                        {"id": 123, "nombre": "Producto A", "cantidad": 2},
                        {"id": 124, "nombre": "Producto B", "cantidad": 1}
                    ]
                )
                print("✅ Log de venta enviado")
            elif comando == 'error':
                cliente.log_error(
                    error="Stock insuficiente para el producto",
                    contexto="Operación de venta",
                    usuario="admin"
                )
                print("✅ Log de error enviado")
            elif comando == 'mensaje':
                texto = input("Ingrese el mensaje: ")
                cliente.enviar_mensaje_texto(texto)
                print("✅ Mensaje enviado")
            else:
                print("❌ Comando no reconocido")
    
    except KeyboardInterrupt:
        print("\n🔴 Interrupción detectada")
    finally:
        cliente.desconectar()

if __name__ == "__main__":
    main()