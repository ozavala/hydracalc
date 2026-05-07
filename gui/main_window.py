import sys
from PySide6.QtWidgets import (QMainWindow, QApplication, QWidget, QVBoxLayout, 
                             QHBoxLayout, QToolBar, QStatusBar, QSplitter, 
                             QGroupBox, QFormLayout, QDoubleSpinBox, QLineEdit,
                             QLabel, QFrame)
from PySide6.QtGui import QAction, QIcon, QKeySequence
from PySide6.QtCore import Qt
from gui.canvas import NetworkCanvas # Asumiendo que tu archivo se llama canvas.py

class PropertyPanel(QFrame):
    """Panel lateral para edición de atributos"""
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setFixedWidth(280)
        
        layout = QVBoxLayout(self)
        
        # Grupo de Información del Nodo
        group_node = QGroupBox("Propiedades del Elemento")
        form = QFormLayout(group_node)
        
        self.lbl_id = QLabel("-")
        self.spin_press = QDoubleSpinBox()
        self.spin_press.setSuffix(" bar")
        self.spin_elev = QDoubleSpinBox()
        self.spin_elev.setSuffix(" m")
        self.txt_tag = QLineEdit()
        
        form.addRow("ID Interno:", self.lbl_id)
        form.addRow("Presión:", self.spin_press)
        form.addRow("Elevación:", self.spin_elev)
        form.addRow("Etiqueta:", self.txt_tag)
        
        layout.addWidget(group_node)
        layout.addStretch() # Empuja todo hacia arriba

    def update_node_data(self, data):
        self.lbl_id.setText(str(data.id))
        self.spin_press.setValue(data.pressure)
        self.spin_elev.setValue(data.elevation)
        self.txt_tag.setText(data.notes)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("HydraCalc - Simulador de Redes Hidráulicas")
        self.resize(1200, 800)

        # 1. Componentes Centrales
        self.canvas = NetworkCanvas()
        self.sidebar = PropertyPanel()
        
        # 2. Organización con Splitter (permite ajustar el ancho del panel)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.canvas)
        self.splitter.setStretchFactor(1, 1) # El canvas crece más
        
        self.setCentralWidget(self.splitter)

        # 3. Llamada a configuraciones
        self.create_menus()
        self.create_toolbars()
        self.create_statusbar()
        
        # 4. Conexión de Señales
        self.canvas.nodeSelected.connect(self.sidebar.update_node_data)

    def create_menus(self):
        menu_bar = self.menuBar()
        
        # Menú Archivo
        file_menu = menu_bar.addMenu("&Archivo")
        exit_action = QAction("Salir", self)
        exit_action.setShortcut(QKeySequence.Quit)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Menú Herramientas
        tool_menu = menu_bar.addMenu("&Herramientas")
        calc_action = QAction("Calcular Red", self)
        tool_menu.addAction(calc_action)

    def create_toolbars(self):
        # Toolbar Principal
        main_toolbar = QToolBar("Barra Principal")
        self.addToolBar(main_toolbar)
        
        # Acciones de ejemplo (puedes usar iconos con QIcon)
        main_toolbar.addAction("Nuevo")
        main_toolbar.addAction("Abrir")
        main_toolbar.addAction("Guardar")
        main_toolbar.addSeparator()
        
        # Toolbar de Dibujo
        draw_toolbar = QToolBar("Dibujo")
        self.addToolBar(Qt.LeftToolBarArea, draw_toolbar) # A la izquierda
        draw_toolbar.addAction("Node")
        draw_toolbar.addAction("Pipe")
        draw_toolbar.addAction("Pump")
        draw_toolbar.addAction("Valve")

    def create_statusbar(self):
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Listo")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # Aplicar un estilo oscuro básico (opcional)
    app.setStyle("Fusion")
    
    win = MainWindow()
    win.show()
    sys.exit(app.exec())
