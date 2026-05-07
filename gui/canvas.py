from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QTransform, QBrush, QPixmap
from PySide6.QtCore import Qt, QPointF, Signal
from dataclasses import dataclass
import os

@dataclass
class NodeData:
    id: int
    pressure: float
    elevation: float
    notes: str

class NetworkCanvas(QWidget):
    nodeSelected = Signal(NodeData)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        
        # --- ESTADO DE LA VISTA ---
        self.zoom_factor = 1.0
        self.pan_offset = QPointF(0, 0)
        self.last_mouse_pos = QPointF()
        self.grid_size = 30
        
        # --- ESTADO DE INTERACCIÓN ---
        self.interact_mode = "SELECT"
        self.selected_node_idx = None
        self.start_node_idx = None
        self.temp_line = None
        
        # --- DATOS Y RECURSOS ---
        self.nodes = [] # Lista de dicts: {"pos": QPointF, "type": str, "data": NodeData}
        self.pipes = []
        
        '''# Carga de iconos (Asegúrate de que la ruta sea correcta)
        self.icons = {
            "Valve": QPixmap("resources/icons/valve.png"),
            "Tank": QPixmap("resources/icons/tank.png")
        }'''
        
        base_path = os.path.dirname(os.path.abspath(__file__))
        self.icons= {
            "Valve": QPixmap(os.path.join(base_path, "..","resources", "icons","valve.png")),
            "Tank": QPixmap(os.path.join(base_path, "..", "resources", "icons","tank.png"))
        }

        for name,pm in self.icons.items():
            if pm.isNull():
                print(f"Error; No se pudo cargar el icono {name} en la ruta especificada.")
    
    def get_current_transform(self):
        """Calcula la matriz de transformación para zoom y pan"""
        transform = QTransform()
        transform.translate(self.pan_offset.x(), self.pan_offset.y())
        transform.scale(self.zoom_factor, self.zoom_factor)
        return transform

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            painter.fillRect(self.rect(), QColor("white"))
            # Aplicar transformación de vista
            painter.setTransform(self.get_current_transform())
            self.draw_grid(painter)
            self.draw_network(painter)
        finally:
            painter.end()

    def draw_grid(self, painter):
        pen = QPen(QColor(240, 240, 240), 1)
        painter.setPen(pen)
        r = 5000 
        for x in range(-r, r, self.grid_size):
            painter.drawLine(x, -r, x, r)
        for y in range(-r, r, self.grid_size):
            painter.drawLine(-r, y, r, y)

    def draw_network(self, painter):
        # 1. Tuberías
        pen_pipe = QPen(QColor("#2c3e50"), 3)
        painter.setPen(pen_pipe)
        for start_idx, end_idx in self.pipes:
            painter.drawLine(self.nodes[start_idx]["pos"], self.nodes[end_idx]["pos"])

        # 2. Línea elástica (Rubber Band)
        if self.interact_mode == "ADD_PIPE" and self.start_node_idx is not None and self.temp_line:
            painter.setPen(QPen(QColor("gray"), 2, Qt.DashLine))
            painter.drawLine(self.nodes[self.start_node_idx]["pos"], self.temp_line)

        # 3. Nodos e Iconos
        for i, node in enumerate(self.nodes):
            pos = node["pos"]
            node_type = node.get("type", "Junction")
            
            if node_type in self.icons and not self.icons[node_type].isNull():
                pixmap = self.icons[node_type]
                painter.drawPixmap(int(pos.x() - 16), int(pos.y() - 16), 32, 32, pixmap)
                
            # Opcional: Dibujar un pequeño círculo si está seleccionado
            if i == self.selected_node_idx:
                painter.setPen(QPen(QColor("#e74c3c"), 2))
                painter.setBrush(Qt.NoBrush)
                painter.drawRect(int(pos.x() - 18), int(pos.y() - 18), 36, 36)
            else:
                color = "#e74c3c" if i == self.selected_node_idx else "#3498db"
                painter.setBrush(QBrush(QColor(color)))
                painter.setPen(QPen(Qt.black, 1))
                painter.drawEllipse(pos, 8, 8)

    def mousePressEvent(self, event):
        # Obtener coordenadas del mundo real
        transform = self.get_current_transform()
        inv_transform, success = transform.inverted()
        if not success: return
        
        world_pos = inv_transform.map(event.position())

        if event.button() == Qt.LeftButton:
            if self.interact_mode == "SELECT":
                self.handle_selection(world_pos)
            elif self.interact_mode == "ADD_NODE":
                self.add_node(world_pos, "Junction")
            elif self.interact_mode == "ADD_VALVE":
                self.add_node(world_pos, "Valve")
            elif self.interact_mode == "ADD_TANK":
                self.add_node(world_pos, "Tank")
            elif self.interact_mode == "ADD_PIPE":
                self.handle_pipe_creation(world_pos)
        
        elif event.button() == Qt.MiddleButton:
            self.last_mouse_pos = event.position()
        self.update()

    def add_node(self, world_pos, node_type):
        new_id = len(self.nodes) + 1
        print(f"Creando elemento: {node_type} en posición {world_pos}") # <-- DEBUG
        self.nodes.append({
            "pos": world_pos,
            "type": node_type,
            "data": NodeData(new_id, 0.0, 0.0, f"{node_type} {new_id}")
        })
        self.update()
        
    def handle_selection(self, world_pos):
        """Busca y selecciona un nodo bajo el cursor"""
        self.selected_node_idx = None
        for i, node in enumerate(self.nodes):
            # Hit testing de 15 píxeles de radio
            if (node["pos"] - world_pos).manhattanLength() < 20:
                self.selected_node_idx = i
                self.nodeSelected.emit(node["data"])
                break

    def handle_pipe_creation(self, world_pos):
        """Lógica de dos clics para crear una tubería entre nodos"""
        # 1. Buscar si el clic fue sobre un nodo existente
        hit_idx = None
        for i, node in enumerate(self.nodes):
            if (node["pos"] - world_pos).manhattanLength() < 15:
                hit_idx = i
                break
        
        # 2. Gestionar los estados de creación
        if self.start_node_idx is None:
            # PRIMER CLIC: Seleccionar nodo de origen
            if hit_idx is not None:
                self.start_node_idx = hit_idx
        else:
            # SEGUNDO CLIC: Seleccionar nodo de destino
            if hit_idx is not None and hit_idx != self.start_node_idx:
                # Evitar duplicados si lo deseas, o simplemente añadir
                self.pipes.append((self.start_node_idx, hit_idx))
                self.start_node_idx = None # Reset
                self.temp_line = None
            else:
                # Clic al aire o al mismo nodo: Cancelar
                self.start_node_idx = None
                self.temp_line = None

    def mouseMoveEvent(self, event):
        """Maneja el movimiento del mouse para la línea elástica y el desplazamiento"""
        transform = self.get_current_transform()
        inv_transform, success = transform.inverted()
        if not success: return
        
        world_pos = inv_transform.map(event.position())

        # Actualizar punto final de la línea elástica (Rubber Band)
        if self.interact_mode == "ADD_PIPE" and self.start_node_idx is not None:
            self.temp_line = world_pos
            self.update()

        # Lógica de Pan (Desplazamiento con botón central)
        if event.buttons() & Qt.MiddleButton:
            delta = event.position() - self.last_mouse_pos
            self.pan_offset += delta
            self.last_mouse_pos = event.position()
            self.update()
            
        super().mouseMoveEvent(event)


    
