from view.vista import VistaStock
from view.ventas import VistaVentas
import flet as ft

class ControladorStock:
    def __init__(self, page: ft.Page):
        self.page = page
        self.vista_stock = None
        self.vista_ventas = None
        self.pantalla_actual = "stock"
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.auto_scroll = True

    def cambiar_a_stock(self, e):
        if self.pantalla_actual != "stock":
            self.page.clean()
            self.vista_stock = VistaStock(self.page)
            self.agregar_navegacion()
            self.vista_stock.inicializar_formulario()
            self.pantalla_actual = "stock"

    def cambiar_a_ventas(self, e):
        if self.pantalla_actual != "ventas":
            self.page.clean()
            self.vista_ventas = VistaVentas(self.page)
            self.agregar_navegacion()
            self.vista_ventas.inicializar_ventas()
            self.pantalla_actual = "ventas"

    def agregar_navegacion(self):
        nav_bar = ft.Container(
            content=ft.Row([
                ft.Text("Sistema de Gestión", 
                       style=ft.TextThemeStyle.HEADLINE_SMALL,
                       weight=ft.FontWeight.BOLD,
                       color=ft.Colors.WHITE),
                ft.Row([
                    ft.ElevatedButton(
                        "Gestión de Stock",
                        icon=ft.Icons.INVENTORY,
                        on_click=self.cambiar_a_stock,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.BLUE if self.pantalla_actual == "stock" else ft.Colors.BLUE_GREY,
                            color=ft.Colors.WHITE
                        )
                    ),
                    ft.ElevatedButton(
                        "Ventas",
                        icon=ft.Icons.POINT_OF_SALE,
                        on_click=self.cambiar_a_ventas,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.PURPLE if self.pantalla_actual == "ventas" else ft.Colors.BLUE_GREY,
                            color=ft.Colors.WHITE
                        )
                    ),
                ], spacing=10),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            padding=ft.padding.all(15),
            bgcolor=ft.Colors.BLUE_GREY_800,
            margin=ft.margin.only(bottom=20),
        )
        
        self.page.controls.insert(0, nav_bar)
        self.page.update()

    def iniciar(self):
        self.vista_stock = VistaStock(self.page)
        self.agregar_navegacion()
        self.vista_stock.inicializar_formulario()