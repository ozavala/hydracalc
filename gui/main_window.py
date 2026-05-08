import sys
from PySide6.QtWidgets import (QMainWindow, QSplitter, QToolBar, QStatusBar, 
                             QApplication, QHBoxLayout, QWidget)
from PySide6.QtGui import QAction, QIcon, QActionGroup
from PySide6.QtCore import Qt, QSize

from gui.canvas import NetworkCanvas
from gui.property_panel import PropertyPanel
from database.database_manager import DatabaseManager
from PySide6.QtCore import Signal


class MainWindow(QMainWindow):
    data_changed_signal = Signal(dict)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HydraCalc")
        self.resize(1200, 800)

        # 1. Primero los motores de datos
        self.db_manager = DatabaseManager()
        self.canvas = NetworkCanvas()
        self.sidebar = PropertyPanel(self.db_manager)

        # 2. LUEGO creas los widgets (El orden importa)
        self.canvas = NetworkCanvas()
        self.sidebar = PropertyPanel(self.db_manager) # <--- Se crea AQUÍ

        # 3. LUEGO los organizas en el layout/splitter
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.canvas)
        self.setCentralWidget(self.splitter)

        # 4. FINALMENTE haces las conexiones de señales
        # Ahora self.sidebar y self.canvas ya existen y no darán AttributeError
        self.canvas.nodeSelected.connect(self.sidebar.update_node_data)
        #self.sidebar.data_changed_signal.connect(self.canvas.update_selected_node_data)

        # 5. Inicializar datos de la interfaz
        self.sidebar.populate_initial_data()
        self.create_toolbars()
        
        self.sidebar.data_changed_signal.connect(self.canvas.update_selected_node_data)
        self.setup_ui()
        
    def setup_ui(self):
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.canvas)
        self.setCentralWidget(self.splitter)
    
    def create_menus(self):
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&Archivo")
        file_menu.addAction("Nuevo Proyecto")
        file_menu.addAction("Guardar")
        file_menu.addSeparator()
        file_menu.addAction("Salir", self.close)

    def create_toolbars(self):
        # --- Toolbar Superior (General) ---
        main_toolbar = self.addToolBar("General")
        main_toolbar.setIconSize(QSize(24, 24))
        
        # Acciones de Unidades
        self.unit_mm_action = QAction("Métrico (mm)", self)
        self.unit_in_action = QAction("Imperial (in)", self)
        self.unit_mm_action.setCheckable(True)
        self.unit_in_action.setCheckable(True)
        self.unit_mm_action.setChecked(True)
        
        unit_group = QActionGroup(self)
        unit_group.addAction(self.unit_mm_action)
        unit_group.addAction(self.unit_in_action)
        
        main_toolbar.addActions([self.unit_mm_action, self.unit_in_action])
        main_toolbar.addSeparator()
        
        # Conectar cambio de unidades
        self.unit_mm_action.triggered.connect(lambda: self.change_units("mm"))
        self.unit_in_action.triggered.connect(lambda: self.change_units("in"))

        # --- Toolbar Lateral (Herramientas de Ingeniería) ---
        draw_toolbar = QToolBar("Dibujo")
        draw_toolbar.setIconSize(QSize(32, 32))
        self.addToolBar(Qt.LeftToolBarArea, draw_toolbar)

        # Definición de Acciones con Iconos (Asegúrate que existan en la carpeta)
        self.select_action = QAction(QIcon("resources/icons/select.png"), "Seleccionar", self)
        self.node_action = QAction(QIcon("resources/icons/node.png"), "Añadir Nodo", self)
        self.pipe_action = QAction(QIcon("resources/icons/pipe.png"), "Añadir Tubería", self)
        self.valve_action = QAction(QIcon("resources/icons/valve.png"), "Añadir Válvula", self)
        self.tank_action = QAction(QIcon("resources/icons/tank.png"), "Añadir Tanque", self)

        # Hacerlas accionables
        self.tools_group = QActionGroup(self)
        for action in [self.select_action, self.node_action, self.pipe_action, self.valve_action, self.tank_action]:
            action.setCheckable(True)
            draw_toolbar.addAction(action)
            self.tools_group.addAction(action)

        self.select_action.setChecked(True)

        # Conexiones de modo
        self.select_action.triggered.connect(lambda: self.change_interact_mode("SELECT"))
        self.node_action.triggered.connect(lambda: self.change_interact_mode("ADD_NODE"))
        self.pipe_action.triggered.connect(lambda: self.change_interact_mode("ADD_PIPE"))
        self.valve_action.triggered.connect(lambda: self.change_interact_mode("ADD_VALVE"))
        self.tank_action.triggered.connect(lambda: self.change_interact_mode("ADD_TANK"))
    
    def change_interact_mode(self, mode):
        self.canvas.interact_mode = mode
        messages = {
            "SELECT": "Modo: Selección de elementos",
            "ADD_NODE": "Modo: Añadir Nodo (Clic en el lienzo)",
            "ADD_PIPE": "Modo: Añadir Tubería (Selecciona nodo origen)",
            "ADD_VALVE": "Modo: Añadir Válvula", 
            "ADD_TANK": "Modo: Añadir Tanque",     
        }
        self.statusBar().showMessage(messages.get(mode, "Listo"))

    def change_units(self, unit_type):
        """Cambia el sistema de tablas entre mm e in"""
        self.current_units = unit_type
        # Aquí notificaremos al DatabaseManager en el futuro para cambiar de tabla
        self.statusBar().showMessage(f"Sistema cambiado a: {unit_type}")
        self.sidebar.update_sizes() # Refrescar lista de diámetros

    def create_statusbar(self):
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Listo")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion") # Estilo limpio y profesional
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
