import flet as ft
from controller.controlador import ControladorStock

def main(page: ft.Page):
    page.title = "Sistema de Gestión"
    page.window_width = 1000
    page.window_height = 700
    page.window_resizable = True

    controlador = ControladorStock(page)
    controlador.iniciar()

ft.app(target=main)