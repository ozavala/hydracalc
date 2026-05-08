import os
import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QColor, QPen, QTransform, QBrush, QPixmap
from PySide6.QtCore import Qt, QPointF, Signal
from dataclasses import dataclass

@dataclass
class NodeData:
    id: int
    pressure: float
    elevation: float
    notes: str

class NetworkCanvas(QWidget):
    nodeSelected = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        
        # --- VIEW STATE ---
        self.zoom_factor = 1.0
        self.pan_offset = QPointF(0, 0)
        self.last_mouse_pos = QPointF()
        self.grid_size = 30
        
        # --- INTERACTION STATE ---
        self.interact_mode = "SELECT"
        self.selected_node_idx = None
        self.start_node_idx = None
        self.temp_line = None
        
        # --- DATA STRUCTURE ---
        self.nodes = [] # List of dicts: {"pos", "type", "data", "demand_in", etc}
        self.pipes = [] # List of tuples: (start_idx, end_idx)
        
        # --- RESOURCES ---
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.icons = {
            "Valve": QPixmap(os.path.join(base_path, "resources", "icons", "valve.png")),
            "Tank": QPixmap(os.path.join(base_path, "resources", "icons", "tank.png"))
        }

    def get_current_transform(self):
        """Calculates the transformation matrix for zoom and pan"""
        transform = QTransform()
        transform.translate(self.pan_offset.x(), self.pan_offset.y())
        transform.scale(self.zoom_factor, self.zoom_factor)
        return transform

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            painter.fillRect(self.rect(), QColor("white"))
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
        # 1. Pipes
        pen_pipe = QPen(QColor("#2c3e50"), 3)
        painter.setPen(pen_pipe)
        for start_idx, end_idx in self.pipes:
            painter.drawLine(self.nodes[start_idx]["pos"], self.nodes[end_idx]["pos"])

        # 2. Rubber Band for Pipe creation
        if self.interact_mode == "ADD_PIPE" and self.start_node_idx is not None and self.temp_line:
            painter.setPen(QPen(QColor("gray"), 2, Qt.DashLine))
            painter.drawLine(self.nodes[self.start_node_idx]["pos"], self.temp_line)

        # 3. Demand Arrows (Drawn below nodes)
        for node in self.nodes:
            self.draw_demand_arrows(painter, node["pos"], node)

        # 4. Nodes and Icons
        for i, node in enumerate(self.nodes):
            pos = node["pos"]
            node_type = node.get("type", "Junction")
            
            if node_type in self.icons and not self.icons[node_type].isNull():
                pixmap = self.icons[node_type]
                painter.drawPixmap(int(pos.x() - 16), int(pos.y() - 16), 32, 32, pixmap)
                if i == self.selected_node_idx:
                    painter.setPen(QPen(QColor("#e74c3c"), 2))
                    painter.setBrush(Qt.NoBrush)
                    painter.drawRect(int(pos.x() - 18), int(pos.y() - 18), 36, 36)
            else:
                color = "#e74c3c" if i == self.selected_node_idx else "#3498db"
                painter.setBrush(QBrush(QColor(color)))
                painter.setPen(QPen(Qt.black, 1))
                painter.drawEllipse(pos, 8, 8)
                
            if node_type == "EndPressure":
                painter.setBrush(QBrush(QColor("#f1c40f"))) # Amarillo
                painter.drawRect(int(pos.x() - 10), int(pos.y() - 10), 20, 20)

    def draw_demand_arrows(self, painter, pos, node):
        """Draws flow arrows for Demand In (Green) and Demand Out (Red)"""
        d_in = float(node.get("demand_in", 0.0))
        d_out = float(node.get("demand_out", 0.0))
        
        offset = 35 
        size = 12

        if d_in > 0:
            painter.setPen(QPen(QColor("#27ae60"), 3))
            painter.setBrush(QColor("#27ae60"))
            start_p = QPointF(pos.x() - offset, pos.y() - offset)
            self.paint_arrow_head(painter, start_p, pos, size)

        if d_out > 0:
            painter.setPen(QPen(QColor("#e74c3c"), 3))
            painter.setBrush(QColor("#e74c3c"))
            end_p = QPointF(pos.x() + offset, pos.y() + offset)
            self.paint_arrow_head(painter, pos, end_p, size)

    def paint_arrow_head(self, painter, start, end, size):
        painter.drawLine(start, end)
        angle = math.atan2(end.y() - start.y(), end.x() - start.x())
        p1 = QPointF(end.x() - size * math.cos(angle - math.pi/6),
                     end.y() - size * math.sin(angle - math.pi/6))
        p2 = QPointF(end.x() - size * math.cos(angle + math.pi/6),
                     end.y() - size * math.sin(angle + math.pi/6))
        painter.drawPolygon([end, p1, p2])

    # --- MOUSE EVENTS ---

    def mousePressEvent(self, event):
        inv_transform = self.get_current_transform().inverted()[0]
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
            elif self.interact_mode == "ADD_PRESSURE":
                self.add_node(world_pos, "EndPressure")
        
        elif event.button() == Qt.MiddleButton:
            self.last_mouse_pos = event.position()
        self.update()

    def mouseMoveEvent(self, event):
        inv_transform = self.get_current_transform().inverted()[0]
        world_pos = inv_transform.map(event.position())

        if self.interact_mode == "ADD_PIPE" and self.start_node_idx is not None:
            self.temp_line = world_pos
            self.update()

        if event.buttons() & Qt.MiddleButton:
            delta = event.position() - self.last_mouse_pos
            self.pan_offset += delta
            self.last_mouse_pos = event.position()
            self.update()

    def wheelEvent(self, event):
        adj = 1.1 if event.angleDelta().y() > 0 else 0.9
        self.zoom_factor *= adj
        self.update()

    # --- LOGIC METHODS ---

    def add_node(self, world_pos, node_type):
        new_id = len(self.nodes) + 1
        new_node = {
            "pos": world_pos,
            "type": node_type,
            "demand_in": 0.0,
            "demand_out": 0.0,
            "liquid_level": 0.0,
            "surface_pressure": 0.0,
            "data": NodeData(new_id, 0.0, 0.0, f"{node_type} {new_id}")
        }
        self.nodes.append(new_node)

    def handle_selection(self, world_pos):
        self.selected_node_idx = None
        for i, node in enumerate(self.nodes):
            if (node["pos"] - world_pos).manhattanLength() < 20:
                self.selected_node_idx = i
                self.nodeSelected.emit(node)
                break

    def handle_pipe_creation(self, world_pos):
        hit_idx = None
        for i, node in enumerate(self.nodes):
            if (node["pos"] - world_pos).manhattanLength() < 20:
                hit_idx = i
                break
        
        if self.start_node_idx is None:
            if hit_idx is not None: self.start_node_idx = hit_idx
        else:
            if hit_idx is not None and hit_idx != self.start_node_idx:
                self.pipes.append((self.start_node_idx, hit_idx))
                self.start_node_idx = None
                self.temp_line = None
            else:
                self.start_node_idx = None
                self.temp_line = None

    def update_selected_node_data(self, new_values):
        """Saves values from PropertyPanel into the selected node"""
        if self.selected_node_idx is not None:
            node = self.nodes[self.selected_node_idx]
            node["data"].notes = new_values["notes"]
            node["data"].elevation = new_values["elevation"]
            node["demand_in"] = new_values.get("demand_in", 0.0)
            node["demand_out"] = new_values.get("demand_out", 0.0)
            node["liquid_level"] = new_values.get("liquid_level", 0.0)
            node["surface_pressure"] = new_values.get("surface_pressure", 0.0)
            self.update()
