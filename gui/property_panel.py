from PySide6.QtWidgets import (QFrame, QVBoxLayout, QGroupBox, QFormLayout, 
                             QComboBox, QDoubleSpinBox, QLineEdit, QLabel)
from PySide6.QtCore import Qt

class PropertyPanel(QFrame):
    """Panel lateral unificado para la edición de atributos de la red"""
    def __init__(self, db_manager):
        super().__init__()
        self.db_manager = db_manager
        
        # UI Styling (Herencia de QFrame)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setFixedWidth(300)
        
        # Main Layout
        self.main_layout = QVBoxLayout(self)
        
        # --- SECCIÓN 1: CONFIGURACIÓN GLOBAL (FLUIDO) ---
        self.setup_fluid_section()
        
        # --- SECCIÓN 2: DETALLES DEL ELEMENTO SELECCIONADO ---
        self.setup_element_section()
        
        self.main_layout.addStretch() # Empujar contenido hacia arriba

    def setup_fluid_section(self):
        group = QGroupBox("Configuración del Fluido")
        form = QFormLayout(group)
        
        self.fluid_combo = QComboBox()
        form.addRow("Fluido Global:", self.fluid_combo)
        
        self.main_layout.addWidget(group)

    def setup_element_section(self):
        self.element_group = QGroupBox("Propiedades del Elemento")
        form = QFormLayout(self.element_group)
        
        # Campos de identificación
        self.id_label = QLabel("-")
        self.tag_input = QLineEdit()
        
        # Campos de tubería (especificado en tu documento)
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
        """Puebla los combos iniciales desde SQLite"""
        # Liquids
        for f_id, name, temp in self.db_manager.get_liquids():
            self.fluid_combo.addItem(f"{name} ({temp}°C)", f_id)
            
        # Materials
        for mat in self.db_manager.get_distinct_materials():
            self.material_combo.addItem(mat)
            
        # Conectar eventos para cascada (Material -> Schedule -> Size)
        self.material_combo.currentIndexChanged.connect(self.update_schedules)
        self.schedule_combo.currentIndexChanged.connect(self.update_sizes)
        
        self.update_schedules()

    def update_schedules(self):
        self.schedule_combo.clear()
        material = self.material_combo.currentText()
        schedules = self.db_manager.get_schedules_by_material(material)
        for sch in schedules:
            self.schedule_combo.addItem(sch)

    def update_sizes(self):
        self.size_combo.clear()
        material = self.material_combo.currentText()
        schedule = self.schedule_combo.currentText()
        sizes = self.db_manager.get_sizes(material, schedule)
        for t_id, size in sizes:
            self.size_combo.addItem(size, t_id)
