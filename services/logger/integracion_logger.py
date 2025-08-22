import datetime
from services.logger.cliente_log import LoggerCliente

class LogObservadorConServidor:
    """Observador que escribe en archivo local Y envía al servidor de logs"""
    
    def __init__(self):
        self.logger_cliente = LoggerCliente()
        self.servidor_disponible = self.logger_cliente.conectar()
        if not self.servidor_disponible:
            print("⚠️ Servidor de logs no disponible, solo se guardará en archivo local")
    
    def actualizar(self, sujeto, mensaje):
        with open('log_usuarios.txt', 'a', encoding='utf-8') as log_file:
            log_file.write(
                f"Evento: {mensaje} | "
                f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                f"Tipo: {type(sujeto).__name__}\n"
            )
        
        if self.servidor_disponible:
            try:
                tipo_sujeto = type(sujeto).__name__
                
                if "agregado" in mensaje.lower():
                    operacion = "AGREGAR_PRODUCTO"
                elif "actualizado" in mensaje.lower() or "stock" in mensaje.lower():
                    operacion = "ACTUALIZAR_STOCK"
                elif "eliminado" in mensaje.lower():
                    operacion = "ELIMINAR_PRODUCTO"
                else:
                    operacion = "OPERACION_GENERICA"
                
                detalles = {
                    "mensaje_original": mensaje,
                    "tipo_sujeto": tipo_sujeto,
                    "timestamp_local": datetime.datetime.now().isoformat()
                }
                
                if hasattr(sujeto, 'id'):
                    detalles["producto_id"] = sujeto.id
                if hasattr(sujeto, 'nombre'):
                    detalles["producto_nombre"] = sujeto.nombre
                if hasattr(sujeto, 'stock'):
                    detalles["stock_actual"] = sujeto.stock
                if hasattr(sujeto, 'precio'):
                    detalles["precio"] = float(sujeto.precio)
                
                self.logger_cliente.log_operacion_stock(
                    operacion=operacion,
                    usuario="admin",
                    detalles=detalles,
                    nivel="INFO"
                )
                
            except Exception as e:
                print(f"⚠️ Error enviando log al servidor: {e}")

class ConsolaObservadorConServidor:
    def __init__(self):
        self.logger_cliente = LoggerCliente()
        self.servidor_disponible = self.logger_cliente.conectar()
    
    def actualizar(self, sujeto, mensaje):
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"[CONSOLA] {timestamp} - {mensaje}")
        
        if self.servidor_disponible:
            try:
                self.logger_cliente.log_operacion_stock(
                    operacion="EVENTO_CONSOLA",
                    usuario="sistema",
                    detalles={
                        "mensaje": mensaje,
                        "tipo_sujeto": type(sujeto).__name__,
                        "timestamp": timestamp
                    },
                    nivel="DEBUG"
                )
            except Exception as e:
                print(f"⚠️ Error enviando log de consola al servidor: {e}")

def log_venta_servidor(numero_venta, cliente, vendedor, total, productos):
    try:
        logger = LoggerCliente()
        if logger._cliente_log and logger._cliente_log.conectado:
            productos_info = []
            for item in productos:
                productos_info.append({
                    "id": item.get('producto_id', 'N/A'),
                    "nombre": item.get('nombre', 'N/A'),
                    "cantidad": item.get('cantidad', 0),
                    "precio_unitario": item.get('precio_unitario', 0),
                    "subtotal": item.get('subtotal', 0)
                })
            
            logger.log_venta(
                numero_venta=numero_venta,
                cliente_venta=cliente,
                vendedor=vendedor,
                total=float(total),
                productos=productos_info
            )
            return True
    except Exception as e:
        print(f"⚠️ Error registrando venta en servidor: {e}")
    return False

def log_error_servidor(error, contexto="", usuario="sistema"):
    try:
        logger = LoggerCliente()
        if logger._cliente_log and logger._cliente_log.conectado:
            logger.log_error(error=str(error), contexto=contexto, usuario=usuario)
            return True
    except Exception as e:
        print(f"⚠️ Error registrando error en servidor: {e}")
    return False