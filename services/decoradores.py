import datetime
import os
from functools import wraps

def log_operacion(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        log_dir = os.path.join('services', 'logger')
        os.makedirs(log_dir, exist_ok=True)
        
        # Ruta del archivo de log
        log_file_path = os.path.join(log_dir, 'log_stock.txt')
        
        instancia = args[0]
        nombre_metodo = func.__name__
        
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(f"[DEBUG] Entrando a {nombre_metodo} con args={args[1:]}, kwargs={kwargs}\n")
        
        try:
            resultado = func(*args, **kwargs)
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(
                    f"Operación: {nombre_metodo} | "
                    f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"Argumentos: {args[1:]} {kwargs} | "
                    f"Resultado: Éxito\n"
                )
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(f"[DEBUG] Saliendo de {nombre_metodo} (éxito)\n")
            return resultado
        except Exception as e:
            with open(log_file_path, 'a', encoding='utf-8') as log_file:
                log_file.write(
                    f"Operación: {nombre_metodo} | "
                    f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                    f"Argumentos: {args[1:]} {kwargs} | "
                    f"Error: {str(e)}\n"
                )
                log_file.write(f"[DEBUG] Saliendo de {nombre_metodo} (error)\n")
            raise
    return wrapper