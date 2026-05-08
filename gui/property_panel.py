import os
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QGroupBox, QFormLayout, 
                             QComboBox, QDoubleSpinBox, QLineEdit, QLabel, 
                             QStackedWidget, QWidget, QHBoxLayout, QPushButton)
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt, Signal

class PropertyPanel(QFrame):
    # Señal para sincronizar con el Canvas
    data_changed_signal = Signal(dict)

    def __init__(self, database_manager):
        super().__init__()
        self.db_manager = database_manager
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setFixedWidth(320)
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(10, 10, 10, 10)
        self.main_layout.setSpacing(10)

        # 1. INFORMACIÓN COMÚN (ID, Etiqueta, Elevación)
        self.setup_fluid_section()
        self.setup_common_info()

        # 2. CONTENEDOR DINÁMICO DE NODOS (Stacked Widget)
        self.node_stack = QStackedWidget()
        
        # Módulos específicos
        self.tank_module = self.create_tank_module()
        self.junction_module = self.create_junction_module()
        self.end_press_module = self.create_end_press_module()
        self.empty_module = QWidget() # Para cuando no hay nada seleccionado

        self.node_stack.addWidget(self.tank_module)      # Index 0
        self.node_stack.addWidget(self.junction_module)  # Index 1
        self.node_stack.addWidget(self.end_press_module) # Index 2
        self.node_stack.addWidget(self.empty_module)     # Index 3
        
        self.main_layout.addWidget(self.node_stack)

        # 3. SECCIÓN DE TUBERÍA (Fija abajo)
        self.setup_pipe_properties()

        self.main_layout.addStretch()

    def setup_fluid_section(self):
        """Crea el combo global de fluidos"""
        group = QGroupBox("Configuración del Fluido")
        form = QFormLayout(group)
        self.fluid_combo = QComboBox() # <--- Aquí se define el atributo
        form.addRow("Fluido Global:", self.fluid_combo)
        self.main_layout.addWidget(group)
        
    # --- UI SETUP METHODS ---

    def setup_common_info(self):
        group = QGroupBox("Información General")
        form = QFormLayout(group)
        
        self.id_label = QLabel("-")
        self.tag_input = QLineEdit()
        self.elevation_spin = QDoubleSpinBox()
        self.elevation_spin.setSuffix(" m s.n.m.")
        self.elevation_spin.setRange(-1000, 9000)
        
        form.addRow("ID Interno:", self.id_label)
        form.addRow("Etiqueta:", self.tag_input)
        form.addRow("Elevación:", self.elevation_spin)
        
        self.tag_input.textChanged.connect(self.sync_data)
        self.elevation_spin.valueChanged.connect(self.sync_data)
        self.main_layout.addWidget(group)

    def create_tank_module(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Propiedades del Tanque")
        form = QFormLayout(group)
        
        # Imagen del diagrama (Tu referencia)
        img_label = QLabel()
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        pix = QPixmap(os.path.join(base_path, "resources", "images", "tank_diagram.png"))
        img_label.setPixmap(pix.scaledToWidth(200, Qt.SmoothTransformation))
        img_label.setAlignment(Qt.AlignCenter)
        
        self.liquid_level = QDoubleSpinBox()
        self.liquid_level.setSuffix(" m")
        self.surf_press = QDoubleSpinBox()
        self.surf_press.setSuffix(" bar")
        
        layout.addWidget(img_label)
        form.addRow("Nivel Líquido:", self.liquid_level)
        form.addRow("Presión Superficie:", self.surf_press)
        layout.addWidget(group)
        
        self.liquid_level.valueChanged.connect(self.sync_data)
        self.surf_press.valueChanged.connect(self.sync_data)
        return widget

    def create_junction_module(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Demandas del Nodo")
        form = QFormLayout(group)
        
        self.demand_in = QDoubleSpinBox()
        self.demand_in.setSuffix(" m³/h")
        self.demand_out = QDoubleSpinBox()
        self.demand_out.setSuffix(" m³/h")
        
        # Flechas de flujo (Estética PipeFlow)
        form.addRow("📥 Demand In:", self.demand_in)
        form.addRow("📤 Demand Out:", self.demand_out)
        
        layout.addWidget(group)
        self.demand_in.valueChanged.connect(self.sync_data)
        self.demand_out.valueChanged.connect(self.sync_data)
        return widget

    def create_end_press_module(self):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Presión de Salida")
        form = QFormLayout(group)
        
        self.end_pressure = QDoubleSpinBox()
        self.end_pressure.setSuffix(" bar")
        form.addRow("Presión Final:", self.end_pressure)
        
        layout.addWidget(group)
        self.end_pressure.valueChanged.connect(self.sync_data)
        return widget

    def setup_pipe_properties(self):
        self.pipe_group = QGroupBox("Propiedades de Tubería")
        form = QFormLayout(self.pipe_group)
        
        self.material_combo = QComboBox()
        self.schedule_combo = QComboBox()
        self.size_combo = QComboBox()
        self.length_spin = QDoubleSpinBox()
        self.length_spin.setSuffix(" m")
        
        form.addRow("Material:", self.material_combo)
        form.addRow("Schedule:", self.schedule_combo)
        form.addRow("Tamaño Nom:", self.size_combo)
        form.addRow("Longitud:", self.length_spin)
        
        # Botones de Accesorios (Fase 3 del plan)
        btn_layout = QHBoxLayout()
        self.btn_fittings = QPushButton("Accesorios")
        self.btn_pump = QPushButton("Bomba")
        btn_layout.addWidget(self.btn_fittings)
        btn_layout.addWidget(self.btn_pump)
        form.addRow(btn_layout)

        self.main_layout.addWidget(self.pipe_group)
        self.pipe_group.hide()
        
    def create_end_press_module(self):
        """Módulo para nodos de descarga con presión fija"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        group = QGroupBox("Propiedades del Punto de Presión")
        form = QFormLayout(group)

        # Imagen opcional o icono de presión
        self.end_pressure_input = QDoubleSpinBox()
        self.end_pressure_input.setSuffix(" bar")
        self.end_pressure_input.setRange(0, 500)
        self.end_pressure_input.setDecimals(3)
        
        form.addRow("Presión de Salida:", self.end_pressure_input)
        layout.addWidget(group)
        
        # Conectar a la sincronización
        self.end_pressure_input.valueChanged.connect(self.sync_data)
        return widget
    # --- LOGIC & SYNC ---

    def sync_data(self):
        if self.signalsBlocked() or self.id_label.text() == "-": return
        
        data = {
            "notes": self.tag_input.text(),
            "elevation": self.elevation_spin.value(),
            "demand_in": self.demand_in.value(),
            "demand_out": self.demand_out.value(),
            "liquid_level": self.liquid_level.value(),
            "surface_pressure": self.surf_press.value(),
            "end_pressure": self.end_pressure.value()
        }
        self.data_changed_signal.emit(data)

    def update_node_data(self, node_dict):
        self.blockSignals(True)
        
        node_type = node_dict.get("type", "Junction")
        data = node_dict["data"]
        
        self.id_label.setText(str(data.id))
        self.tag_input.setText(data.notes)
        self.elevation_spin.setValue(data.elevation)
        
        # Cambio dinámico de StackedWidget
        if node_type == "Tank":
            self.node_stack.setCurrentIndex(0)
            self.liquid_level.setValue(node_dict.get("liquid_level", 0.0))
            self.surf_press.setValue(node_dict.get("surface_pressure", 0.0))
            self.pipe_group.hide()
        elif node_type in ["Junction", "Valve"]:
            self.node_stack.setCurrentIndex(1)
            self.demand_in.setValue(node_dict.get("demand_in", 0.0))
            self.demand_out.setValue(node_dict.get("demand_out", 0.0))
            self.pipe_group.hide()
        elif node_type == "EndPressure":
            self.node_stack.setCurrentIndex(2)
            self.end_pressure.setValue(node_dict.get("end_pressure", 0.0))
            self.pipe_group.hide()
        else:
            self.node_stack.setCurrentIndex(3)
            
        self.blockSignals(False)

    def populate_initial_data(self):
        self.blockSignals(True)
        for f_id, name, temp in self.db_manager.get_fluids():
            self.fluid_combo.addItem(f"{name} ({temp}°C)", f_id)
        for mat in self.db_manager.get_distinct_materials():
            self.material_combo.addItem(mat)
        self.material_combo.currentIndexChanged.connect(self.update_schedules)
        self.schedule_combo.currentIndexChanged.connect(self.update_sizes)
        self.blockSignals(False)
        self.update_schedules()

    def update_schedules(self):
        self.schedule_combo.blockSignals(True)
        self.schedule_combo.clear()
        material = self.material_combo.currentText()
        schedules = self.db_manager.get_schedules_by_material(material)
        self.schedule_combo.addItems(schedules)
        self.schedule_combo.blockSignals(False)
        self.update_sizes()

    def update_sizes(self):
        self.size_combo.clear()
        material = self.material_combo.currentText()
        schedule = self.schedule_combo.currentText()
        sizes = self.db_manager.get_sizes(material, schedule)
        for rowid, nominal in sizes:
            self.size_combo.addItem(str(nominal), rowid)
