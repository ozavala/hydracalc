from PySide6.QtWidgets import QFrame, QVBoxLayout, QGroupBox, QFormLayout, QComboBox, QDoubleSpinBox, QLineEdit, QLabel
from PySide6.QtCore import Qt

class PropertyPanel(QFrame):
    def __init__(self, database_manager):
        super().__init__()
        self.database_manager = database_manager
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setFixedWidth(300)
        self.main_layout = QVBoxLayout(self)
        
        self.setup_fluid_section()
        self.setup_element_section()
        self.main_layout.addStretch()

    def setup_fluid_section(self):
        group = QGroupBox("Configuración del Fluido")
        form = QFormLayout(group)
        self.fluid_combo = QComboBox()
        form.addRow("Fluido Global:", self.fluid_combo)
        self.main_layout.addWidget(group)

    def setup_element_section(self):
        self.element_group = QGroupBox("Propiedades del Elemento")
        form = QFormLayout(self.element_group)
        
        self.id_label = QLabel("-")
        self.tag_input = QLineEdit()
        self.material_combo = QComboBox()
        self.schedule_combo = QComboBox()
        self.size_combo = QComboBox()
        self.length_spin = QDoubleSpinBox()
        self.length_spin.setSuffix(" m")
        
        form.addRow("ID Interno:", self.id_label)
        form.addRow("Etiqueta:", self.tag_input)
        form.addRow("Material:", self.material_combo)
        form.addRow("Cédula (Schedule):", self.schedule_combo)
        form.addRow("Diámetro Nom:", self.size_combo)
        form.addRow("Longitud:", self.length_spin)
        
        self.main_layout.addWidget(self.element_group)

    # --- LOGIC METHODS (ENGLISH) ---
    def populate_initial_data(self):
        # Fluids from 'liquids' table
        for f_id, name, temp in self.database_manager.get_fluids():
            self.fluid_combo.addItem(f"{name} ({temp}°C)", f_id)
            
        # Materials from 'pipes_mm'
        for mat in self.database_manager.get_distinct_materials():
            self.material_combo.addItem(mat)
            
        self.material_combo.currentIndexChanged.connect(self.update_schedules)
        self.schedule_combo.currentIndexChanged.connect(self.update_sizes)
        self.update_schedules()

    def update_schedules(self):
        self.schedule_combo.blockSignals(True)
        self.schedule_combo.clear()
        material = self.material_combo.currentText()
        schedules = self.database_manager.get_schedules_by_material(material)
        self.schedule_combo.addItems(schedules)
        self.schedule_combo.blockSignals(False)
        self.update_sizes()

    def update_sizes(self):
        self.size_combo.clear()
        material = self.material_combo.currentText()
        schedule = self.schedule_combo.currentText()
        sizes = self.database_manager.get_sizes(material, schedule)
        for rowid, nominal in sizes:
            self.size_combo.addItem(str(nominal), rowid)

    def update_node_data(self, node_data):
        self.id_label.setText(str(node_data.id))
        self.tag_input.setText(node_data.notes)
