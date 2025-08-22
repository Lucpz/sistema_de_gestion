import flet as ft
from model.modelo import StockManager, Producto
from peewee import *
import datetime
from decimal import Decimal
from services.logger.integracion_logger import LogObservadorConServidor, ConsolaObservadorConServidor, log_venta_servidor, log_error_servidor
from model.modelo import db

class Venta(Model):
    numero_venta = CharField(unique=True)
    fecha = DateTimeField(default=datetime.datetime.now)
    cliente = CharField()
    total = DecimalField(max_digits=10, decimal_places=2)
    vendedor = CharField()
    
    
    class Meta:
        database = db

class DetalleVenta(Model):
    venta = ForeignKeyField(Venta, backref='detalles')
    producto = ForeignKeyField(Producto)
    cantidad = IntegerField()
    precio_unitario = DecimalField(max_digits=10, decimal_places=2)
    subtotal = DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        database = db

from model.modelo import db
db.create_tables([Venta, DetalleVenta], safe=True)

class VistaVentas:
    def __init__(self, page: ft.Page): 
        self.page = page
        self.stock_manager = StockManager()
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.auto_scroll = True
        
        self.carrito_items = []
        self.total_venta = 0.0
        
        self.txt_cliente = ft.TextField(label="Nombre del Cliente", width=300)
        self.txt_vendedor = ft.TextField(label="Vendedor", width=300, value="admin")
        
        self.txt_producto_id = ft.TextField(label="ID del Producto", width=150)
        self.txt_cantidad_venta = ft.TextField(label="Cantidad", width=150)
        self.txt_precio_override = ft.TextField(label="Precio (opcional)", width=150)
        
        self.info_producto = ft.Container(
            content=ft.Text("Seleccione un producto", color=ft.Colors.GREY),
            padding=10,
            bgcolor=ft.Colors.ON_SURFACE_VARIANT,
            border_radius=5,
            visible=False
        )
        
        self.carrito_list = ft.ListView(expand=True, spacing=5, padding=10)
        
        self.txt_total = ft.Text("Total: $0.00", 
                                style=ft.TextThemeStyle.HEADLINE_SMALL,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.GREEN)
        
        self.productos_disponibles = ft.ListView(expand=True, spacing=5, padding=10)
        
        # Tabla de historial de ventas
        self.tabla_ventas = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("N° Venta", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Fecha", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Cliente", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Vendedor", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Total", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Acciones", weight=ft.FontWeight.BOLD)),
            ],
            rows=[],
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=10,
            vertical_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
            horizontal_lines=ft.border.BorderSide(1, ft.Colors.OUTLINE),
            heading_row_color=ft.Colors.BLUE_GREY_100,
        )
        
        self.txt_filtro_cliente = ft.TextField(
            label="Filtrar por cliente", 
            width=200,
            on_change=self.filtrar_ventas
        )
        self.txt_filtro_fecha = ft.TextField(
            label="Filtrar por fecha (YYYY-MM-DD)", 
            width=200,
            on_change=self.filtrar_ventas
        )
        
        self.mensaje_container = ft.Container(
            content=ft.Text("", color=ft.Colors.GREEN),
            padding=10,
            margin=10,
            visible=False
        )
    
    def mostrar_snackbar(self, mensaje, es_error=False):
        color = ft.Colors.RED if es_error else ft.Colors.GREEN
        
        snackbar = ft.SnackBar(
            content=ft.Text(mensaje, color=ft.Colors.WHITE),
            bgcolor=color,
            duration=3000,
        )
        
        self.page.overlay.append(snackbar)
        snackbar.open = True
        self.page.update()
    
    def ver_detalle_venta(self, venta_id):
        try:
            venta = Venta.get_by_id(venta_id)
            detalles = DetalleVenta.select().where(DetalleVenta.venta == venta)
            
            detalle_content = ft.Column([
                ft.Text(f"Venta: {venta.numero_venta}", 
                       style=ft.TextThemeStyle.HEADLINE_SMALL,
                       weight=ft.FontWeight.BOLD),
                ft.Text(f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}"),
                ft.Text(f"Cliente: {venta.cliente}"),
                ft.Text(f"Vendedor: {venta.vendedor}"),
                ft.Divider(),
                ft.Text("Productos:", weight=ft.FontWeight.BOLD),
            ])
            
            total_items = 0
            for detalle in detalles:
                try:
                    producto = Producto.get_by_id(detalle.producto)
                    producto_info = ft.Container(
                        content=ft.Row([
                            ft.Text(f"• {producto.nombre}", expand=True),
                            ft.Text(f"Cant: {detalle.cantidad}"),
                            ft.Text(f"Precio: ${detalle.precio_unitario:.2f}"),
                            ft.Text(f"Subtotal: ${detalle.subtotal:.2f}", 
                                   weight=ft.FontWeight.BOLD),
                        ]),
                        padding=5,
                        bgcolor=ft.Colors.ON_SURFACE_VARIANT,
                        border_radius=5,
                        margin=ft.margin.symmetric(vertical=2)
                    )
                    detalle_content.controls.append(producto_info)
                    total_items += detalle.cantidad
                except:
                    producto_info = ft.Container(
                        content=ft.Row([
                            ft.Text(f"• Producto eliminado (ID: {detalle.producto})", 
                                   expand=True, color=ft.Colors.RED),
                            ft.Text(f"Cant: {detalle.cantidad}"),
                            ft.Text(f"Precio: ${detalle.precio_unitario:.2f}"),
                            ft.Text(f"Subtotal: ${detalle.subtotal:.2f}", 
                                   weight=ft.FontWeight.BOLD),
                        ]),
                        padding=5,
                        bgcolor=ft.Colors.ERROR_CONTAINER,
                        border_radius=5,
                        margin=ft.margin.symmetric(vertical=2)
                    )
                    detalle_content.controls.append(producto_info)
                    total_items += detalle.cantidad
            
            # Resumen final
            detalle_content.controls.extend([
                ft.Divider(),
                ft.Text(f"Total de items: {total_items}", weight=ft.FontWeight.BOLD),
                ft.Text(f"TOTAL: ${venta.total:.2f}", 
                       style=ft.TextThemeStyle.HEADLINE_SMALL,
                       weight=ft.FontWeight.BOLD,
                       color=ft.Colors.GREEN),
            ])
            
            def cerrar_detalle(e):
                dialog.open = False
                self.page.update()
            
            dialog = ft.AlertDialog(
                modal=True,
                title=ft.Text("Detalle de Venta", color=ft.Colors.BLUE),
                content=ft.Container(
                    content=detalle_content,
                    width=600,
                    height=400,
                ),
                actions=[
                    ft.TextButton("Cerrar", on_click=cerrar_detalle),
                ],
                actions_alignment=ft.MainAxisAlignment.END,
            )
            
            self.page.overlay.append(dialog)
            dialog.open = True
            self.page.update()
            
        except Exception as ex:
            self.mostrar_dialog("Error", f"Error al cargar detalle: {str(ex)}", True)
    
    def cargar_historial_ventas(self, filtro_cliente=None, filtro_fecha=None):
        try:
            query = Venta.select().order_by(Venta.fecha.desc())
            
            if filtro_cliente:
                query = query.where(Venta.cliente.contains(filtro_cliente))
            
            if filtro_fecha:
                try:
                    fecha_filtro = datetime.datetime.strptime(filtro_fecha, '%Y-%m-%d').date()
                    query = query.where(
                        (Venta.fecha >= fecha_filtro) & 
                        (Venta.fecha < fecha_filtro + datetime.timedelta(days=1))
                    )
                except ValueError:
                    pass  
            
            ventas = query.limit(50) 
            
            self.tabla_ventas.rows.clear()
            
            for venta in ventas:
                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(venta.numero_venta)),
                        ft.DataCell(ft.Text(venta.fecha.strftime('%d/%m/%Y %H:%M'))),
                        ft.DataCell(ft.Text(venta.cliente)),
                        ft.DataCell(ft.Text(venta.vendedor)),
                        ft.DataCell(ft.Text(f"${venta.total:.2f}", 
                                          weight=ft.FontWeight.BOLD,
                                          color=ft.Colors.GREEN)),
                        ft.DataCell(
                            ft.IconButton(
                                icon=ft.Icons.VISIBILITY,
                                tooltip="Ver detalle",
                                icon_color=ft.Colors.BLUE,
                                on_click=lambda e, vid=venta.id: self.ver_detalle_venta(vid)
                            )
                        ),
                    ]
                )
                self.tabla_ventas.rows.append(row)
            
            if not self.tabla_ventas.rows:
                row = ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text("No hay ventas registradas", 
                                          color=ft.Colors.GREY)),
                        ft.DataCell(ft.Text("-")),
                        ft.DataCell(ft.Text("-")),
                        ft.DataCell(ft.Text("-")),
                        ft.DataCell(ft.Text("-")),
                        ft.DataCell(ft.Text("-")),
                    ]
                )
                self.tabla_ventas.rows.append(row)
            
            self.page.update()
            
        except Exception as ex:
            self.mostrar_dialog("Error", f"Error al cargar historial: {str(ex)}", True)
    
    def filtrar_ventas(self, e):
        filtro_cliente = self.txt_filtro_cliente.value.strip() if self.txt_filtro_cliente.value else None
        filtro_fecha = self.txt_filtro_fecha.value.strip() if self.txt_filtro_fecha.value else None
        
        self.cargar_historial_ventas(filtro_cliente, filtro_fecha)

    def exportar_ventas(self, e):
        try:
            ventas = Venta.select().order_by(Venta.fecha.desc())
            
            if not ventas:
                self.mostrar_snackbar("No hay ventas para exportar", True)
                return
            
            contenido = "HISTORIAL DE VENTAS\n"
            contenido += "=" * 50 + "\n\n"
            
            total_general = 0
            for venta in ventas:
                contenido += f"Venta: {venta.numero_venta}\n"
                contenido += f"Fecha: {venta.fecha.strftime('%d/%m/%Y %H:%M')}\n"
                contenido += f"Cliente: {venta.cliente}\n"
                contenido += f"Vendedor: {venta.vendedor}\n"
                contenido += f"Total: ${venta.total:.2f}\n"
                
                detalles = DetalleVenta.select().where(DetalleVenta.venta == venta)
                contenido += "Productos:\n"
                for detalle in detalles:
                    try:
                        producto = Producto.get_by_id(detalle.producto)
                        contenido += f"  - {producto.nombre} x{detalle.cantidad} = ${detalle.subtotal:.2f}\n"
                    except:
                        contenido += f"  - Producto eliminado (ID: {detalle.producto}) x{detalle.cantidad} = ${detalle.subtotal:.2f}\n"
                
                contenido += "-" * 30 + "\n\n"
                total_general += float(venta.total)
            
            contenido += f"TOTAL GENERAL: ${total_general:.2f}\n"
            contenido += f"Total de ventas: {len(list(ventas))}\n"
            
            nombre_archivo = f"ventas_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            self.mostrar_dialog("Exportación Exitosa", 
                f"Historial exportado a: {nombre_archivo}")
            
        except Exception as ex:
            self.mostrar_dialog("Error", f"Error al exportar: {str(ex)}", True)
    
    def mostrar_dialog(self, titulo, mensaje, es_error=False):
        color = ft.Colors.RED if es_error else ft.Colors.GREEN
        
        def cerrar_dialog(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(titulo, color=color),
            content=ft.Text(mensaje),
            actions=[
                ft.TextButton("OK", on_click=cerrar_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def buscar_producto(self, e):
        if not self.txt_producto_id.value:
            self.info_producto.visible = False
            self.page.update()
            return
        
        try:
            producto_id = int(self.txt_producto_id.value)
            producto = Producto.get_by_id(producto_id)
            
            stock_color = ft.Colors.RED if producto.stock < 5 else ft.Colors.GREEN
            
            self.info_producto.content = ft.Column([
                ft.Text(f"Producto: {producto.nombre}", weight=ft.FontWeight.BOLD),
                ft.Text(f"Descripción: {producto.descripcion}"),
                ft.Text(f"Precio: ${producto.precio}"),
                ft.Text(f"Stock disponible: {producto.stock}", color=stock_color),
                ft.Text(f"Categoría: {producto.categoria}"),
            ])
            self.info_producto.visible = True
            
            if not self.txt_precio_override.value:
                self.txt_precio_override.value = str(producto.precio)
            
            self.page.update()
            
        except ValueError:
            self.mostrar_snackbar("El ID debe ser un número válido", True)
        except:
            self.info_producto.content = ft.Text("Producto no encontrado", color=ft.Colors.RED)
            self.info_producto.visible = True
            self.page.update()

    def agregar_al_carrito(self, e):
        try:
            if not self.txt_producto_id.value:
                self.mostrar_snackbar("Debe ingresar un ID de producto", True)
                return
            
            if not self.txt_cantidad_venta.value:
                self.mostrar_snackbar("Debe ingresar una cantidad", True)
                return
            
            producto_id = int(self.txt_producto_id.value)
            cantidad = int(self.txt_cantidad_venta.value)
            
            if cantidad <= 0:
                self.mostrar_snackbar("La cantidad debe ser mayor a 0", True)
                return
            
            # Verificar que el producto existe
            producto = Producto.get_by_id(producto_id)
            
            # Verificar stock disponible
            cantidad_total_carrito = sum(item['cantidad'] for item in self.carrito_items 
                                       if item['producto_id'] == producto_id)
            
            if cantidad + cantidad_total_carrito > producto.stock:
                self.mostrar_snackbar(
                    f"Stock insuficiente. Disponible: {producto.stock}, "
                    f"en carrito: {cantidad_total_carrito}", True)
                return
            
            # Precio (usar override si está especificado, sino el del producto)
            precio = float(self.txt_precio_override.value) if self.txt_precio_override.value else float(producto.precio)
            
            if precio < 0:
                self.mostrar_snackbar("El precio no puede ser negativo", True)
                return
            
            producto_existente = None
            for item in self.carrito_items:
                if item['producto_id'] == producto_id and item['precio_unitario'] == precio:
                    producto_existente = item
                    break
            
            if producto_existente:
                producto_existente['cantidad'] += cantidad
                producto_existente['subtotal'] = producto_existente['cantidad'] * producto_existente['precio_unitario']
            else:
                item = {
                    'producto_id': producto_id,
                    'nombre': producto.nombre,
                    'cantidad': cantidad,
                    'precio_unitario': precio,
                    'subtotal': cantidad * precio
                }
                self.carrito_items.append(item)
            
            self.txt_producto_id.value = ""
            self.txt_cantidad_venta.value = ""
            self.txt_precio_override.value = ""
            self.info_producto.visible = False
            
            self.actualizar_carrito()
            self.calcular_total()
            
            self.mostrar_snackbar(f"Producto agregado al carrito")
            
        except ValueError as ve:
            self.mostrar_snackbar("Valores numéricos inválidos", True)
        except Exception as ex:
            self.mostrar_dialog("Error", f"El producto ingresado es inexistente, porfavor ingrese otro", True)
    
    def quitar_del_carrito(self, index):
        if 0 <= index < len(self.carrito_items):
            producto_nombre = self.carrito_items[index]['nombre']
            self.carrito_items.pop(index)
            self.actualizar_carrito()
            self.calcular_total()
            self.mostrar_snackbar(f"Producto '{producto_nombre}' quitado del carrito")
    
    def actualizar_carrito(self):
        self.carrito_list.controls.clear()
        
        if not self.carrito_items:
            self.carrito_list.controls.append(
                ft.Text("El carrito está vacío", 
                       color=ft.Colors.GREY,
                       style=ft.TextThemeStyle.BODY_LARGE)
            )
        else:
            for i, item in enumerate(self.carrito_items):
                card = ft.Card(
                    content=ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(f"{item['nombre']}", weight=ft.FontWeight.BOLD),
                                ft.Text(f"Cantidad: {item['cantidad']} × ${item['precio_unitario']:.2f}"),
                                ft.Text(f"Subtotal: ${item['subtotal']:.2f}", 
                                        color=ft.Colors.GREEN,
                                        weight=ft.FontWeight.BOLD),
                            ], expand=True),
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                tooltip="Quitar del carrito",
                                icon_color=ft.Colors.RED,
                                on_click=lambda e, idx=i: self.quitar_del_carrito(idx)
                            ),
                        ]),
                        padding=10,
                    )
                )
                self.carrito_list.controls.append(card)
        
        self.page.update()
    
    def calcular_total(self):
        self.total_venta = sum(item['subtotal'] for item in self.carrito_items)
        self.txt_total.value = f"Total: ${self.total_venta:.2f}"
        self.page.update()
    
    def limpiar_carrito(self, e):
        if not self.carrito_items:
            self.mostrar_snackbar("El carrito ya está vacío", True)
            return
        
        def confirmar_limpiar(e):
            self.carrito_items.clear()
            self.actualizar_carrito()
            self.calcular_total()
            self.mostrar_snackbar("Carrito limpiado")
            dialog.open = False
            self.page.update()
        
        def cancelar_limpiar(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar", color=ft.Colors.ORANGE),
            content=ft.Text("¿Está seguro que desea limpiar todo el carrito?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_limpiar),
                ft.TextButton("Limpiar", on_click=confirmar_limpiar),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()
    
    def procesar_venta(self, e):
        try:
            if not self.carrito_items:
                self.mostrar_snackbar("El carrito está vacío", True)
                return
            
            if not self.txt_cliente.value:
                self.mostrar_snackbar("Debe ingresar el nombre del cliente", True)
                return
            
            if not self.txt_vendedor.value:
                self.mostrar_snackbar("Debe ingresar el nombre del vendedor", True)
                return
            
            for item in self.carrito_items:
                producto = Producto.get_by_id(item['producto_id'])
                if producto.stock < item['cantidad']:
                    self.mostrar_snackbar(
                        f"Stock insuficiente para {producto.nombre}. "
                        f"Disponible: {producto.stock}, Requerido: {item['cantidad']}", True)
                    return
            
            # Generar número de venta único
            numero_venta = f"V{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Crear la venta
            venta = Venta.create(
                numero_venta=numero_venta,
                cliente=self.txt_cliente.value,
                total=self.total_venta,
                vendedor=self.txt_vendedor.value
            )
            
            for item in self.carrito_items:
                DetalleVenta.create(
                    venta=venta,
                    producto=item['producto_id'],
                    cantidad=item['cantidad'],
                    precio_unitario=item['precio_unitario'],
                    subtotal=item['subtotal']
                )
                
                self.stock_manager.actualizar_stock(
                    producto_id=item['producto_id'],
                    cantidad=item['cantidad'],
                    usuario=self.txt_vendedor.value,
                    tipo='salida'
                )
            
            try:
                log_venta_servidor(
                    numero_venta=numero_venta,
                    cliente=self.txt_cliente.value,
                    vendedor=self.txt_vendedor.value,
                    total=self.total_venta,
                    productos=self.carrito_items
                )
            except Exception as log_error:
                print(f"⚠️ Error en logging de venta: {log_error}")
            
            self.mostrar_dialog("Venta Procesada", 
                f"Venta {numero_venta} procesada exitosamente\n"
                f"Cliente: {self.txt_cliente.value}\n"
                f"Total: ${self.total_venta:.2f}\n"
                f"Vendedor: {self.txt_vendedor.value}")
            
            self.limpiar_formulario_venta()
            
            self.cargar_productos_disponibles()
            
            self.cargar_historial_ventas()
            
        except Exception as ex:
            log_error_servidor(str(ex), "procesar_venta", self.txt_vendedor.value)
            self.mostrar_dialog("Error", f"Error al procesar venta: {str(ex)}", True)
    
    def limpiar_formulario_venta(self):
        self.txt_cliente.value = ""
        self.txt_vendedor.value = "admin"
        self.carrito_items.clear()
        self.actualizar_carrito()
        self.calcular_total()
        self.page.update()
    
    def cargar_productos_disponibles(self):
        self.productos_disponibles.controls.clear()
        
        try:
            productos = self.stock_manager.listar_productos()
            
            if not productos:
                self.productos_disponibles.controls.append(
                    ft.Text("No hay productos disponibles", 
                           color=ft.Colors.GREY,
                           style=ft.TextThemeStyle.BODY_LARGE)
                )
            else:
                for producto in productos:
                    stock_color = ft.Colors.RED if producto.stock < 5 else ft.Colors.GREEN
                    disponible = producto.stock > 0
                    
                    card = ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Text(f"ID: {producto.id} - {producto.nombre}", 
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(f"Precio: ${producto.precio}"),
                                ft.Text(f"Stock: {producto.stock}", 
                                        color=stock_color,
                                        weight=ft.FontWeight.BOLD),
                                ft.Text(f"Categoría: {producto.categoria}"),
                            ]),
                            padding=10,
                            bgcolor=ft.Colors.ON_SURFACE_VARIANT if not disponible else None,
                        )
                    )
                    self.productos_disponibles.controls.append(card)
                    
        except Exception as ex:
            self.mostrar_dialog("Error", f"Error al cargar productos: {str(ex)}", True)
        
        self.page.update()
    
    def inicializar_ventas(self):
        titulo = ft.Text("Sistema de Ventas", 
                        style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                        weight=ft.FontWeight.BOLD)
        
        form_cliente = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Datos de la Venta", 
                           style=ft.TextThemeStyle.HEADLINE_SMALL,
                           weight=ft.FontWeight.BOLD),
                    ft.Row([self.txt_cliente, self.txt_vendedor], wrap=True),
                ]),
                padding=20,
            )
        )
        
        # Agregar productos al carrito
        form_productos = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Agregar Productos", 
                           style=ft.TextThemeStyle.HEADLINE_SMALL,
                           weight=ft.FontWeight.BOLD),
                    ft.Row([
                        self.txt_producto_id,
                        self.txt_cantidad_venta,
                        self.txt_precio_override,
                        ft.ElevatedButton(
                            "Buscar",
                            icon=ft.Icons.SEARCH,
                            on_click=self.buscar_producto,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.BLUE, color=ft.Colors.WHITE)
                        ),
                    ], wrap=True),
                    self.info_producto,
                    ft.Row([
                        ft.ElevatedButton(
                            "Agregar al Carrito",
                            icon=ft.Icons.ADD_SHOPPING_CART,
                            on_click=self.agregar_al_carrito,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.GREEN, color=ft.Colors.WHITE)
                        ),
                        ft.ElevatedButton(
                            "Limpiar Carrito",
                            icon=ft.Icons.CLEAR,
                            on_click=self.limpiar_carrito,
                            style=ft.ButtonStyle(bgcolor=ft.Colors.ORANGE, color=ft.Colors.WHITE)
                        ),
                    ]),
                ]),
                padding=20,
            )
        )
        
        # Carrito de compras
        carrito_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Carrito de Compras", 
                               style=ft.TextThemeStyle.HEADLINE_SMALL,
                               weight=ft.FontWeight.BOLD),
                        self.txt_total,
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Container(
                        content=self.carrito_list,
                        height=200,
                    ),
                    ft.ElevatedButton(
                        "Procesar Venta",
                        icon=ft.Icons.POINT_OF_SALE,
                        on_click=self.procesar_venta,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.PURPLE,
                            color=ft.Colors.WHITE,
                            shape=ft.RoundedRectangleBorder(radius=10)
                        ),
                        width=200,
                        height=50,
                    ),
                ]),
                padding=20,
            )
        )
        
        productos_ref_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Productos Disponibles", 
                           style=ft.TextThemeStyle.HEADLINE_SMALL,
                           weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=self.productos_disponibles,
                        height=200,
                    )
                ]),
                padding=20,
            )
        )
        
        # Historial de ventas
        historial_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Row([
                        ft.Text("Historial de Ventas", 
                               style=ft.TextThemeStyle.HEADLINE_SMALL,
                               weight=ft.FontWeight.BOLD),
                        ft.ElevatedButton(
                            "Exportar",
                            icon=ft.Icons.DOWNLOAD,
                            on_click=self.exportar_ventas,
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.TEAL,
                                color=ft.Colors.WHITE
                            )
                        ),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    ft.Row([
                        self.txt_filtro_cliente,
                        self.txt_filtro_fecha,
                        ft.ElevatedButton(
                            "Limpiar Filtros",
                            icon=ft.Icons.CLEAR,
                            on_click=lambda e: self.limpiar_filtros(),
                            style=ft.ButtonStyle(
                                bgcolor=ft.Colors.ORANGE,
                                color=ft.Colors.WHITE
                            )
                        ),
                    ], wrap=True),
                    ft.Container(
                        content=ft.Column([
                            self.tabla_ventas
                        ], scroll=ft.ScrollMode.AUTO),
                        height=300,
                        padding=10,
                    ),
                ]),
                padding=20,
            )
        )
        
        main_content = ft.Column([
            titulo,
            self.mensaje_container,
            form_cliente,
            form_productos,
            ft.Row([
                ft.Container(carrito_card, width=600),
                ft.Container(productos_ref_card, width=400),
            ], wrap=True, alignment=ft.MainAxisAlignment.CENTER),
            historial_card,
        ], spacing=20, scroll=ft.ScrollMode.AUTO)
        
        self.page.add(main_content)
        
        self.cargar_productos_disponibles()
        
        self.cargar_historial_ventas()
        
        self.actualizar_carrito()
        self.calcular_total()
        
        self.txt_producto_id.on_change = self.buscar_producto
    
    def limpiar_filtros(self):
        self.txt_filtro_cliente.value = ""
        self.txt_filtro_fecha.value = ""
        self.cargar_historial_ventas()
        self.page.update()