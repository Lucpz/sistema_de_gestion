import datetime
import os

class Sujeto:
    def __init__(self):
        self._observadores = []

    def agregar_observador(self, observador):
        self._observadores.append(observador)

    def quitar_observador(self, observador):
        self._observadores.remove(observador)

    def notificar(self, mensaje):
        for observador in self._observadores:
            observador.actualizar(self, mensaje)

class Observador:
    def actualizar(self, sujeto, mensaje):
        raise NotImplementedError("Debe implementar este método")

class LogObservador(Observador):
    def actualizar(self, sujeto, mensaje):
        log_dir = os.path.join('services', 'logger')
        os.makedirs(log_dir, exist_ok=True)
        
        log_file_path = os.path.join(log_dir, 'log_usuarios.txt')
        
        with open(log_file_path, 'a', encoding='utf-8') as log_file:
            log_file.write(
                f"Evento: {mensaje} | "
                f"Fecha: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
                f"Tipo: {type(sujeto).__name__}\n"
            )

class ConsolaObservador(Observador):
    def actualizar(self, sujeto, mensaje):
        print(f"[CONSOLA] {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {mensaje}")