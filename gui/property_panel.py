import os
from PySide6.QtWidgets import (QFrame, QVBoxLayout, QGroupBox, QFormLayout, 
                             QComboBox, QDoubleSpinBox, QLineEdit, QLabel)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, Signal

class PropertyPanel(QFrame):
    # Señal de clase para enviar cambios al Canvas
    data_changed_signal = Signal(dict)

    def __init__(self, database_manager):
        super().__init__()
        self.db_manager = database_manager
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setFixedWidth(300)
        self.main_layout = QVBoxLayout(self)
        
        # --- 1. CREACIÓN DE SECCIONES ---
        self.setup_fluid_section()
        self.setup_common_info()
        self.setup_tank_properties()
        self.setup_pipe_properties()
        
        self.main_layout.addStretch()

    def setup_fluid_section(self):
        group = QGroupBox("Configuración del Fluido")
        form = QFormLayout(group)
        self.fluid_combo = QComboBox()
        form.addRow("Fluido Global:", self.fluid_combo)
        self.main_layout.addWidget(group)

    def setup_common_info(self):
        group = QGroupBox("Información General")
        form = QFormLayout(group)
        self.id_label = QLabel("-")
        self.tag_input = QLineEdit()
        self.elevation_spin = QDoubleSpinBox()
        self.elevation_spin.setSuffix(" m")
        self.elevation_spin.setRange(-1000, 9000)
        self.elevation_spin.setDecimals(2)
        
        form.addRow("ID Interno:", self.id_label)
        form.addRow("Etiqueta:", self.tag_input)
        form.addRow("Elevación:", self.elevation_spin)
        
        # Conexiones de sincronización
        self.tag_input.textChanged.connect(self.sync_data)
        self.elevation_spin.valueChanged.connect(self.sync_data)
        self.main_layout.addWidget(group)

    def setup_tank_properties(self):
        self.tank_group = QGroupBox("Propiedades del Tanque")
        layout = QVBoxLayout(self.tank_group)
        
        # --- RECUPERACIÓN DE IMAGEN ---
        self.tank_img_label = QLabel()
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        img_path = os.path.join(base_path, "resources", "images", "tank_diagram.png")
        
        pix = QPixmap(img_path)
        if not pix.isNull():
            self.tank_img_label.setPixmap(pix.scaledToWidth(250, Qt.SmoothTransformation))
        else:
            self.tank_img_label.setText("[Diagrama no encontrado]")
        
        self.tank_img_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.tank_img_label)

        form = QFormLayout()
        self.liquid_level = QDoubleSpinBox()
        self.liquid_level.setSuffix(" m")
        self.liquid_level.setRange(0, 1000)
        
        self.surf_press = QDoubleSpinBox()
        self.surf_press.setSuffix(" bar")
        self.surf_press.setRange(0, 1000)
        
        form.addRow("Nivel Líquido:", self.liquid_level)
        form.addRow("Presión Superficie:", self.surf_press)
        layout.addLayout(form)
        
        # Conexiones
        self.liquid_level.valueChanged.connect(self.sync_data)
        self.surf_press.valueChanged.connect(self.sync_data)
        
        self.main_layout.addWidget(self.tank_group)
        self.tank_group.hide()

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
        form.addRow("Tamaño:", self.size_combo)
        form.addRow("Longitud:", self.length_spin)
        
        self.main_layout.addWidget(self.pipe_group)
        self.pipe_group.hide()

    # --- LÓGICA DE DATOS (ENGLISH) ---

    def populate_initial_data(self):
        self.blockSignals(True)
        try:
            # Fluidos
            for f_id, name, temp in self.db_manager.get_fluids():
                self.fluid_combo.addItem(f"{name} ({temp}°C)", f_id)
            # Materiales
            for mat in self.db_manager.get_distinct_materials():
                self.material_combo.addItem(mat)
        except Exception as e:
            print(f"Error DB: {e}")
            
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

    def sync_data(self):
        """Envía datos al Canvas solo si no estamos en proceso de carga"""
        if self.signalsBlocked() or self.id_label.text() == "-":
            return
            
        data_to_send = {
            "notes": self.tag_input.text(),
            "elevation": self.elevation_spin.value(),
            "liquid_level": self.liquid_level.value(),
            "surface_pressure": self.surf_press.value()
        }
        self.data_changed_signal.emit(data_to_send)

    def update_node_data(self, node_dict):
        """Carga los datos del Canvas a la UI bloqueando señales de 'vuelta'"""
        self.blockSignals(True)
        
        node_type = node_dict.get("type", "Junction")
        data = node_dict["data"]
        
        self.id_label.setText(str(data.id))
        self.tag_input.setText(data.notes)
        self.elevation_spin.setValue(data.elevation)
        
        if node_type == "Tank":
            self.liquid_level.setValue(node_dict.get("liquid_level", 0.0))
            self.surf_press.setValue(node_dict.get("surface_pressure", 0.0))
            self.tank_group.show()
            self.pipe_group.hide()
        elif node_type == "Pipe":
            self.tank_group.hide()
            self.pipe_group.show()
        else:
            self.tank_group.hide()
            self.pipe_group.hide()
            
        self.blockSignals(False)
