import flet as ft
from model.modelo import StockManager, Producto
from model.observers.observador import LogObservador, ConsolaObservador
from services.logger.integracion_logger import LogObservadorConServidor, ConsolaObservadorConServidor, log_venta_servidor, log_error_servidor

class VistaStock:
    def __init__(self, page: ft.Page):
        self.page = page
        self.stock_manager = StockManager()
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.auto_scroll = True
        
        self.log_observador = LogObservadorConServidor()
        self.consola_observador = ConsolaObservadorConServidor()
        
        # Controles del formulario
        self.txt_nombre = ft.TextField(label="Nombre del producto", width=250)
        self.txt_descripcion = ft.TextField(label="Descripción", width=250)
        self.txt_precio = ft.TextField(label="Precio", width=200)
        self.txt_stock = ft.TextField(label="Stock inicial", width=200)
        self.dropdown_categoria = ft.Dropdown(
            label="Categoría",
            width=200,
            options=[
                ft.dropdown.Option("Electrónica"),
                ft.dropdown.Option("Ropa"),
                ft.dropdown.Option("Hogar"),
                ft.dropdown.Option("Alimentos"),
                ft.dropdown.Option("Otros"),
            ]
        )

        # Controles para actualizar stock
        self.txt_producto_id = ft.TextField(label="ID del producto", width=150)
        self.txt_cantidad = ft.TextField(label="Cantidad", width=150)
        self.txt_usuario = ft.TextField(label="Usuario", width=150, value="admin")
        self.dropdown_tipo = ft.Dropdown(
            label="Tipo",
            width=150,
            options=[
                ft.dropdown.Option("entrada"),
                ft.dropdown.Option("salida"),
            ],
            value="entrada"
        )

        self.mensaje_container = ft.Container(
            content=ft.Text("", color=ft.Colors.GREEN),
            padding=10,
            margin=10,
            visible=False
        )

        self.productos_list = ft.ListView(expand=True, spacing=10, padding=20)
        
    def mostrar_mensaje(self, mensaje, es_error=False):
        color = ft.Colors.RED if es_error else ft.Colors.GREEN
        
        self.mensaje_container.content = ft.Text(mensaje, color=color, size=16)
        self.mensaje_container.visible = True
        self.page.update()
        
        def ocultar_mensaje():
            import time
            time.sleep(3)
            self.mensaje_container.visible = False
            self.page.update()
        
        import threading
        threading.Thread(target=ocultar_mensaje, daemon=True).start()
    
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

    def agregar_producto(self, e):
        try:
            if not self.txt_nombre.value:
                self.mostrar_snackbar("El nombre del producto es obligatorio", True)
                return
            
            if not self.txt_precio.value:
                self.mostrar_snackbar("El precio es obligatorio", True)
                return
            
            if not self.txt_stock.value:
                self.mostrar_snackbar("El stock inicial es obligatorio", True)
                return
                
            if not self.dropdown_categoria.value:
                self.mostrar_snackbar("Debe seleccionar una categoría", True)
                return
            
            try:
                precio = float(self.txt_precio.value)
                stock = int(self.txt_stock.value)
                
                if precio < 0:
                    self.mostrar_snackbar("El precio no puede ser negativo", True)
                    return
                
                if stock < 0:
                    self.mostrar_snackbar("El stock no puede ser negativo", True)
                    return
                    
            except ValueError:
                self.mostrar_snackbar("Precio y stock deben ser valores numéricos válidos", True)
                return
            
            # Crear el producto
            producto = self.stock_manager.agregar_producto(
                nombre=self.txt_nombre.value,
                descripcion=self.txt_descripcion.value or "",
                precio=precio,
                stock=stock,
                categoria=self.dropdown_categoria.value
            )
            
            try:
                from services.logger.cliente_log import LoggerCliente
                logger = LoggerCliente()
                logger.log_operacion_stock(
                    operacion="AGREGAR_PRODUCTO",
                    usuario="admin",
                    detalles={
                        "producto_id": producto.id,
                        "nombre": producto.nombre,
                        "precio": float(producto.precio),
                        "stock_inicial": producto.stock,
                        "categoria": producto.categoria,
                        "descripcion": producto.descripcion
                    },
                    nivel="INFO"
                )
            except Exception as log_error:
                print(f"⚠️ Error en logging remoto: {log_error}")
            
            producto.agregar_observador(self.log_observador)
            producto.agregar_observador(self.consola_observador)
            
            self.mostrar_snackbar(f"Producto '{self.txt_nombre.value}' agregado exitosamente")
            
            self.limpiar_formulario()
            
            self.cargar_productos()
            
        except Exception as ex:
            log_error_servidor(str(ex), "agregar_producto", "admin")
            self.mostrar_dialog("Error", f"Error al agregar producto: {str(ex)}", True)

    def actualizar_stock_producto(self, e):
        try:
            if not self.txt_producto_id.value:
                self.mostrar_snackbar("El ID del producto es obligatorio", True)
                return
            
            if not self.txt_cantidad.value:
                self.mostrar_snackbar("La cantidad es obligatoria", True)
                return
                
            if not self.txt_usuario.value:
                self.mostrar_snackbar("El usuario es obligatorio", True)
                return
            
            try:
                producto_id = int(self.txt_producto_id.value)
                cantidad = int(self.txt_cantidad.value)
                
                if cantidad < 0:
                    self.mostrar_snackbar("La cantidad no puede ser negativa", True)
                    return
                    
            except ValueError:
                self.mostrar_snackbar("ID del producto y cantidad deben ser números enteros", True)
                return
            
            try:
                producto = Producto.get_by_id(producto_id)
            except:
                self.mostrar_snackbar(f"No se encontró un producto con ID {producto_id}", True)
                return
            
            if not hasattr(producto, '_observadores'):
                producto._observadores = []
            if self.log_observador not in producto._observadores:
                producto.agregar_observador(self.log_observador)
            if self.consola_observador not in producto._observadores:
                producto.agregar_observador(self.consola_observador)
            
            self.stock_manager.actualizar_stock(
                producto_id=producto_id,
                cantidad=cantidad,
                usuario=self.txt_usuario.value,
                tipo=self.dropdown_tipo.value
            )
            
            try:
                from services.logger.cliente_log import LoggerCliente
                logger = LoggerCliente()
                logger.log_operacion_stock(
                    operacion="ACTUALIZAR_STOCK",
                    usuario=self.txt_usuario.value,
                    detalles={
                        "producto_id": producto_id,
                        "producto_nombre": producto.nombre,
                        "cantidad": cantidad,
                        "tipo_movimiento": self.dropdown_tipo.value,
                        "stock_anterior": producto.stock - (cantidad if self.dropdown_tipo.value == "entrada" else -cantidad),
                        "stock_nuevo": producto.stock
                    },
                    nivel="INFO"
                )
            except Exception as log_error:
                print(f"⚠️ Error en logging remoto: {log_error}")
            
            tipo_texto = "entrada" if self.dropdown_tipo.value == "entrada" else "salida"
            self.mostrar_snackbar(
                f"Stock actualizado: {tipo_texto} de {cantidad} unidades para '{producto.nombre}'"
            )
            
            self.txt_producto_id.value = ""
            self.txt_cantidad.value = ""
            
            self.cargar_productos()
            
        except ValueError as ve:
            if "Stock insuficiente" in str(ve):
                self.mostrar_dialog("Stock Insuficiente", 
                    f"No hay suficiente stock para realizar esta operación.\n"
                    f"Stock actual: {producto.stock} unidades", True)
            else:
                self.mostrar_dialog("Error de Validación", str(ve), True)
        except Exception as ex:
            log_error_servidor(str(ex), "actualizar_stock", self.txt_usuario.value)
            self.mostrar_dialog("Error", f"Error al actualizar stock: {str(ex)}", True)
    
    def eliminar_producto(self, producto_id):
        def confirmar_eliminacion(e):
            try:
                self.stock_manager.eliminar_producto(producto_id)
                self.mostrar_snackbar("Producto eliminado exitosamente")
                self.cargar_productos()
                dialog.open = False
                self.page.update()
            except Exception as ex:
                self.mostrar_dialog("Error", f"Error al eliminar producto: {str(ex)}", True)
                dialog.open = False
                self.page.update()
        
        def cancelar_eliminacion(e):
            dialog.open = False
            self.page.update()
        
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirmar Eliminación", color=ft.Colors.RED),
            content=ft.Text("¿Está seguro que desea eliminar este producto?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancelar_eliminacion),
                ft.TextButton("Eliminar", on_click=confirmar_eliminacion, 
                             style=ft.ButtonStyle(color=ft.Colors.RED)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        
        self.page.overlay.append(dialog)
        dialog.open = True
        self.page.update()

    def limpiar_formulario(self):
        self.txt_nombre.value = ""
        self.txt_descripcion.value = ""
        self.txt_precio.value = ""
        self.txt_stock.value = ""
        self.dropdown_categoria.value = None
        self.page.update()
    
    def cargar_productos(self):
        self.productos_list.controls.clear()
        
        try:
            productos = self.stock_manager.listar_productos()
            
            if not productos:
                self.productos_list.controls.append(
                    ft.Text("No hay productos registrados", 
                           style=ft.TextThemeStyle.BODY_LARGE,
                           color=ft.Colors.GREY)
                )
            else:
                for producto in productos:
                    stock_color = ft.Colors.RED if producto.stock < 5 else ft.Colors.GREEN
                    
                    card = ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.ListTile(
                                    leading=ft.Icon(ft.Icons.INVENTORY, color=ft.Colors.BLUE),
                                    title=ft.Text(f"ID: {producto.id} - {producto.nombre}", weight=ft.FontWeight.BOLD),
                                    subtitle=ft.Text(f"Categoría: {producto.categoria}\n"
                                                   f"Descripción: {producto.descripcion}"),
                                ),
                                ft.Row([
                                    ft.Text(f"Precio: ${producto.precio}", 
                                           style=ft.TextThemeStyle.BODY_MEDIUM),
                                    ft.Text(f"Stock: {producto.stock}", 
                                           color=stock_color,
                                           weight=ft.FontWeight.BOLD),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Eliminar producto",
                                        icon_color=ft.Colors.RED,
                                        on_click=lambda e, pid=producto.id: self.eliminar_producto(pid)
                                    ),
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ]),
                            padding=10,
                        )
                    )
                    self.productos_list.controls.append(card)
                    
        except Exception as ex:
            self.mostrar_dialog("Error", f"Error al cargar productos: {str(ex)}", True)
        
        self.page.update()
    
    def inicializar_formulario(self):
        titulo = ft.Text("Sistema de Gestión", 
                        style=ft.TextThemeStyle.HEADLINE_MEDIUM,
                        weight=ft.FontWeight.BOLD)
        
        # Formulario para agregar productos
        form_agregar = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Agregar Nuevo Producto", 
                           style=ft.TextThemeStyle.HEADLINE_SMALL,
                           weight=ft.FontWeight.BOLD),
                    ft.Row([
                        self.txt_nombre, 
                        self.txt_descripcion
                    ], wrap=True),
                    ft.Row([
                        self.txt_precio, 
                        self.txt_stock, 
                        self.dropdown_categoria
                    ], wrap=True),
                    ft.ElevatedButton(
                        "Agregar Producto",
                        icon=ft.Icons.ADD,
                        on_click=self.agregar_producto,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN,
                            color=ft.Colors.WHITE
                        )
                    ),
                ]),
                padding=20,
            )
        )
        
        # Formulario para actualizar stock
        form_stock = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Actualizar Stock", 
                           style=ft.TextThemeStyle.HEADLINE_SMALL,
                           weight=ft.FontWeight.BOLD),
                    ft.Row([
                        self.txt_producto_id, 
                        self.txt_cantidad, 
                        self.txt_usuario, 
                        self.dropdown_tipo
                    ], wrap=True),
                    ft.ElevatedButton(
                        "Actualizar Stock",
                        icon=ft.Icons.UPDATE,
                        on_click=self.actualizar_stock_producto,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE,
                            color=ft.Colors.WHITE
                        )
                    ),
                ]),
                padding=20,
            )
        )
        
        productos_card = ft.Card(
            content=ft.Container(
                content=ft.Column([
                    ft.Text("Lista de Productos", 
                           style=ft.TextThemeStyle.HEADLINE_SMALL,
                           weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=self.productos_list,
                        height=300,
                    )
                ]),
                padding=20,
            )
        )
        
        main_content = ft.Column([
            titulo,
            self.mensaje_container,  
            form_agregar,  
            form_stock,
            productos_card,
        ], spacing=20, scroll=ft.ScrollMode.AUTO)
        
        self.page.add(main_content)
        
        self.cargar_productos()