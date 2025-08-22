from peewee import *
import datetime
import os
from services.decoradores import log_operacion
from model.observers.observador import Sujeto
import flet as ft
# db = SqliteDatabase('stock.db')
db_directory = os.path.join('model', 'database')
os.makedirs(db_directory, exist_ok=True)
db_path = os.path.join(db_directory, 'stock.db')
db = SqliteDatabase(db_path)

class BaseModel(Model):
    class Meta:
        database = db

class Producto(BaseModel, Sujeto):
    def __init__(self, *args, **kwargs):
        BaseModel.__init__(self, *args, **kwargs)
        Sujeto.__init__(self)
    nombre = CharField()
    descripcion = TextField()
    precio = DecimalField(max_digits=10, decimal_places=2)
    stock = IntegerField()
    categoria = CharField()
    fecha_actualizacion = DateTimeField(default=datetime.datetime.now)

class MovimientoStock(BaseModel):
    producto = ForeignKeyField(Producto, backref='movimientos')
    tipo = CharField()
    cantidad = IntegerField()
    fecha = DateTimeField(default=datetime.datetime.now)
    usuario = CharField()

db.connect()
db.create_tables([Producto, MovimientoStock])

class StockManager:
    def __init__(self):
        # Crear directorio de logs si no existe
        self.log_dir = os.path.join('services', 'logger')
        os.makedirs(self.log_dir, exist_ok=True)
        self.log_file_path = os.path.join(self.log_dir, 'log_stock.txt')
    
    @log_operacion
    def agregar_producto(self, nombre, descripcion, precio, stock, categoria):
        producto = Producto.create(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            stock=stock,
            categoria=categoria
        )
        producto.notificar(f"Nuevo producto agregado: {nombre}")
        return producto
    @log_operacion
    def actualizar_stock(self, producto_id, cantidad, usuario, tipo='entrada'):
        
        producto = Producto.get(Producto.id == producto_id)
        if tipo == 'entrada':
            producto.stock += cantidad
        elif tipo == 'salida':
            if producto.stock < cantidad:
                
                raise ValueError("Stock insuficiente")
            producto.stock -= cantidad
        producto.fecha_actualizacion = datetime.datetime.now()
        producto.save()
        MovimientoStock.create(
            producto=producto,
            tipo=tipo,
            cantidad=cantidad,
            usuario=usuario
        )
        producto.notificar(f"Stock actualizado: {producto.nombre} - {tipo} de {cantidad} unidades")
        
        return producto

    def eliminar_producto(self, producto_id):
        from peewee import DoesNotExist
        try:
            
            producto = Producto.get_by_id(producto_id)
            
            producto.delete_instance(recursive=True)
            
            return True
        except DoesNotExist:
            
            raise ValueError("Producto no encontrado")
        except Exception as ex:
            
            raise ex
    def listar_productos(self):
        return Producto.select().order_by(Producto.nombre)

    def buscar_producto(self, nombre):
        return Producto.select().where(Producto.nombre.contains(nombre))