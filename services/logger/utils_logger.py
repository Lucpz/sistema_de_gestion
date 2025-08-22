import os
import datetime

def crear_directorio_logs():
    log_dir = os.path.join('services', 'logger')
    os.makedirs(log_dir, exist_ok=True)
    return log_dir

def obtener_ruta_log(nombre_archivo):
    log_dir = crear_directorio_logs()
    return os.path.join(log_dir, nombre_archivo)

def limpiar_logs_antiguos(dias_antiguedad=30):
    import datetime
    import glob
    
    log_dir = crear_directorio_logs()
    patron_logs = os.path.join(log_dir, '*.txt')
    
    fecha_limite = datetime.datetime.now() - datetime.timedelta(days=dias_antiguedad)
    
    for archivo_log in glob.glob(patron_logs):
        try:
            fecha_modificacion = datetime.datetime.fromtimestamp(os.path.getmtime(archivo_log))
            if fecha_modificacion < fecha_limite:
                os.remove(archivo_log)
                print(f"📁 Archivo de log eliminado: {archivo_log}")
        except Exception as e:
            print(f"⚠️ Error eliminando archivo {archivo_log}: {e}")

def listar_archivos_log():
    import glob
    
    log_dir = crear_directorio_logs()
    patron_logs = os.path.join(log_dir, '*.txt')
    
    return glob.glob(patron_logs)

def obtener_tamaño_logs():
    archivos = listar_archivos_log()
    tamaño_total = 0
    info_archivos = {}
    
    for archivo in archivos:
        try:
            tamaño = os.path.getsize(archivo)
            tamaño_total += tamaño
            nombre_archivo = os.path.basename(archivo)
            info_archivos[nombre_archivo] = {
                'tamaño_bytes': tamaño,
                'tamaño_kb': round(tamaño / 1024, 2),
                'ruta': archivo
            }
        except Exception as e:
            print(f"⚠️ Error obteniendo tamaño de {archivo}: {e}")
    
    return {
        'tamaño_total_bytes': tamaño_total,
        'tamaño_total_kb': round(tamaño_total / 1024, 2),
        'tamaño_total_mb': round(tamaño_total / (1024 * 1024), 2),
        'cantidad_archivos': len(archivos),
        'archivos': info_archivos
    }

def inicializar_sistema_logs():
    print("🔧 Inicializando sistema de logs...")
    
    log_dir = crear_directorio_logs()
    print(f"📁 Directorio de logs: {log_dir}")
    
    archivos_base = ['log_stock.txt', 'log_usuarios.txt', 'servidor_logs.txt']
    
    for archivo in archivos_base:
        ruta_archivo = obtener_ruta_log(archivo)
        if not os.path.exists(ruta_archivo):
            with open(ruta_archivo, 'w', encoding='utf-8') as f:
                f.write(f"=== ARCHIVO DE LOG: {archivo.upper()} ===\n")
                f.write(f"Creado: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
            print(f"📄 Archivo creado: {archivo}")
        else:
            print(f"📄 Archivo existente: {archivo}")
    
    print("✅ Sistema de logs inicializado correctamente")

if __name__ == "__main__":
    import datetime
    inicializar_sistema_logs()
    
    print("\n📊 Información de logs:")
    info = obtener_tamaño_logs()
    print(f"  Total de archivos: {info['cantidad_archivos']}")
    print(f"  Tamaño total: {info['tamaño_total_kb']} KB")
    
    for nombre, datos in info['archivos'].items():
        print(f"  - {nombre}: {datos['tamaño_kb']} KB")